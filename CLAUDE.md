# CLAUDE.md — Developer Guide for AI Assistants

This file documents the project structure, conventions, and critical context for anyone (human or AI) working on this codebase.

---

## Project Summary

**Multiagent TV Scheduler** — A FastAPI + Streamlit application that uses a pipeline of 4 LangChain agents backed by Claude claude-sonnet-4-6 to generate optimized 24-hour TV broadcast schedules. ContentAgent fetches live sports events from free APIs (TheSportsDB, TVMaze) and falls back to a local CSV. Schedules are saved to PostgreSQL. The RAG knowledge base uses FAISS + HuggingFace sentence-transformers.

---

## How to Run

### Prerequisites (must be done once)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create PostgreSQL database
psql -U postgres -c "CREATE DATABASE tv_scheduler;"

# 3. Build the FAISS vectorstore from data/ files
python -m backend.rag.ingest
# OR use the "Rebuild Knowledge Base" button in the Streamlit sidebar
```

### Start the app

```bash
# Terminal 1: API server (auto-reloads on file changes)
uvicorn backend.main:app --reload --port 8000

# Terminal 2: Frontend
streamlit run Frontend/streamlit_app.py
```

- API: http://localhost:8000 (interactive docs at /docs)
- Frontend: http://localhost:8501

---

## Architecture

### Request Flow

```
POST /generate-schedule {"day": "Friday"}
  → creates job_id, starts background thread
  → returns {"job_id": "..."}

Background thread: SchedulerWorkflow.run(day, callback)
  → AudienceAgent.run(day)    ─┐ ThreadPoolExecutor (parallel)
  → ContentAgent.run(day)      ─┘
  → SchedulingAgent.run(audience, content)
  → OptimizationAgent.run(schedule)
  → save to PostgreSQL
  → job["status"] = "done"

Frontend polls GET /job/{job_id} every 1s
  → shows callback messages as checkmarks
  → renders schedule table on completion
```

### Agent Pipeline

All agents follow the same pattern:
1. Call `KnowledgeRetriever().retrieve(query)` to get relevant context from FAISS
2. Build a prompt string with that context + their specific inputs
3. Call `llm.invoke(prompt)` (shared `ChatAnthropic` instance)
4. Return the result (string for `AudienceAgent`, parsed JSON dict for `Scheduling` and `Optimization`)

### ContentAgent Data Flow

```
ContentAgent.run(day)
  → day_name_to_date("Friday") → "2026-06-27"
  → fetch_sports_events("2026-06-27")  [TheSportsDB]
      if empty →
  → fetch_tv_sports("2026-06-27")      [TVMaze, country from TV_COUNTRY env]
      if empty →
  → _load_csv()                        [data/programs.csv]
```

### 24-Hour Schedule Structure

`SchedulingAgent` divides the day into 7 blocks via its prompt:
- 00:00–06:00 Overnight, 06:00–09:00 Breakfast, 09:00–12:00 Mid-Morning,
  12:00–15:00 Afternoon, 15:00–18:00 Late Afternoon, 18:00–23:00 Prime Time, 23:00–00:00 Late Evening

### Job System

`backend/main.py` maintains an in-memory `jobs: dict` keyed by UUID. The background thread writes to it; the polling endpoint reads from it. This handles both schedule generation jobs and ingest jobs. On server restart, in-flight jobs are lost (completed schedules are in PostgreSQL).

### RAG System

- **Ingest** (`backend/rag/ingest.py`): reads `*.txt` files from `data/`, splits into 500-char chunks with 50-char overlap, embeds with `all-MiniLM-L6-v2`, saves to `vectorstore/`
- **Retriever** (`backend/rag/retriever.py`): loads the FAISS index on init, `retrieve(query, k=3)` returns the top-3 chunks concatenated as a string
- **Re-ingest needed when**: any file in `data/` is added or changed — use `POST /ingest` or `python -m backend.rag.ingest`

---

## Key Files

| File | Purpose |
|------|---------|
| `backend/main.py` | FastAPI app. All endpoints: `/generate-schedule`, `/job/{id}`, `/ingest`, `/schedules`, `/schedules/{id}`. `Base.metadata.create_all()` on startup. Background threads for both schedule generation and ingest. |
| `backend/workflow.py` | `SchedulerWorkflow` — runs AudienceAgent + ContentAgent in parallel via `ThreadPoolExecutor`, then SchedulingAgent, then OptimizationAgent sequentially. Accepts optional `callback` for progress reporting. |
| `backend/agents/audience_agent.py` | RAG query + LLM call → returns plain text audience analysis |
| `backend/agents/content_agent.py` | Tries TheSportsDB → TVMaze → CSV (in that order). Returns list of program dicts. |
| `backend/agents/scheduling_agent.py` | RAG + LLM → returns parsed JSON dict `{"schedule": [...]}` for a full 24-hour day |
| `backend/agents/optimization_agent.py` | RAG + LLM → returns parsed JSON dict `{"schedule": [...]}` (includes `SCHEDULE_FORMAT` for structure enforcement) |
| `backend/services/llm_service.py` | Singleton `llm` = `ChatAnthropic(model="claude-sonnet-4-6", temperature=0.3)`. All agents import from here. |
| `backend/services/json_parser.py` | `parse_llm_json(text)` — strips markdown fences (` ```json ``` `) before `json.loads`. Use this for all LLM JSON output. |
| `backend/services/sports_api.py` | `day_name_to_date(day)` maps weekday name → YYYY-MM-DD. `fetch_sports_events(date)` queries TheSportsDB. `fetch_tv_sports(date)` queries TVMaze and filters by Sports genre. Both return `[]` on any error. |
| `backend/prompts/schedule_prompt.py` | `SCHEDULE_FORMAT` constant — the exact JSON structure the LLM must return. Keep in sync with `ScheduleSlot` in `schemas.py`. |
| `backend/database.py` | SQLAlchemy engine + `SessionLocal` factory. DATABASE_URL built from `.env` vars. |
| `backend/models.py` | `Schedule` ORM model — columns: `id`, `day`, `created_at`, `schedule_data` (JSON). |
| `backend/schemas.py` | Pydantic models: `ScheduleRequest`, `ScheduleSlot`, `ScheduleResponse`, `Program`. |
| `backend/rag/ingest.py` | `ingest()` function — reads `data/*.txt`, chunks, embeds, saves FAISS. Called by `POST /ingest` and directly via `python -m backend.rag.ingest`. |
| `backend/rag/vectorstore.py` | `get_embeddings()` returns HuggingFace embeddings. `create_vectorstore(docs)` saves to `vectorstore/`. |
| `backend/rag/retriever.py` | `KnowledgeRetriever` — loads FAISS on init, `retrieve(query)` returns string. Crashes if `vectorstore/` doesn't exist (run ingest first). |
| `Frontend/streamlit_app.py` | Streamlit UI. Sidebar: "Rebuild Knowledge Base" button (polls `/ingest` job) + schedule history. Main: day selector, generate button, agent progress polling, schedule table. |

---

## Database

**PostgreSQL** via SQLAlchemy. Connection configured in `.env`.

The `schedules` table is created automatically on startup via `Base.metadata.create_all(bind=engine)`.

Schema:
```sql
CREATE TABLE schedules (
    id         SERIAL PRIMARY KEY,
    day        VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT now(),
    schedule_data JSON NOT NULL
);
```

`schedule_data` stores the full `{"schedule": [...]}` dict returned by the workflow.

---

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | Required. Claude API key. |
| `DB_HOST` | PostgreSQL host (default: `localhost`) |
| `DB_PORT` | PostgreSQL port (default: `5432`) |
| `DB_NAME` | Database name (default: `tv_scheduler`) |
| `DB_USER` | PostgreSQL user (default: `postgres`) |
| `DB_PASSWORD` | PostgreSQL password |
| `FAISS_INDEX_PATH` | Path hint for FAISS (actual path hardcoded as `"vectorstore"`) |
| `TV_COUNTRY` | ISO country code for TVMaze sports fallback (default: `GB`) |

---

## Dependencies

| Package | Why |
|---------|-----|
| `langchain-anthropic` | `ChatAnthropic` wrapper for Claude |
| `langchain-community` | `FAISS` vectorstore integration |
| `langchain-huggingface` | `HuggingFaceEmbeddings` |
| `langchain-text-splitters` | `RecursiveCharacterTextSplitter` for RAG ingest |
| `langchain_core` | `Document` class for RAG documents |
| `faiss-cpu` | Local vector similarity search |
| `sentence-transformers` | Embedding model weights |
| `fastapi` + `uvicorn` | REST API server |
| `sqlalchemy` | ORM for PostgreSQL |
| `psycopg2-binary` | PostgreSQL driver |
| `streamlit` | Frontend UI |
| `httpx` | HTTP client for live sports API calls |
| `python-dotenv` | Load `.env` into `os.getenv()` |
| `pydantic` | Request/response validation |

---

## Common Tasks

### Add a new agent
1. Create `backend/agents/my_agent.py` with a class that has a `run(self, ...)` method
2. Export it from `backend/agents/__init__.py`
3. Call it in `backend/workflow.py` at the right point in the pipeline

### Add knowledge to the RAG
1. Add a `.txt` file to `data/`
2. Click **Rebuild Knowledge Base** in the Streamlit sidebar, or run `python -m backend.rag.ingest`
3. Restart uvicorn (so `KnowledgeRetriever` reloads the index on next request)

### Change the LLM model
Edit `backend/services/llm_service.py` — all agents share this instance.

### Add a new API endpoint
Add to `backend/main.py`. If it needs DB access, use the `SessionLocal` pattern already used in `list_schedules()` and `get_schedule()`. If it needs background execution, use the `jobs` dict + `threading.Thread` pattern used by `run_ingest()` and `run_workflow()`.

### Add a new Pydantic schema
Add to `backend/schemas.py`. Import in `backend/main.py` as needed.

---

## Known Limitations / Watch Out For

- **`KnowledgeRetriever` crashes if vectorstore doesn't exist.** Always run ingest before starting the server on a fresh clone.
- **Jobs are in-memory only.** Restarting uvicorn loses all in-flight job state. Completed schedules are safe in PostgreSQL.
- **LLM JSON output.** Always use `parse_llm_json()` from `backend/services/json_parser.py` — Claude often wraps JSON in markdown fences.
- **24-hour schedule coverage.** The SchedulingAgent prompt instructs the model to cover all 24 hours, but it may occasionally produce gaps. The OptimizationAgent has a second instruction to enforce full coverage.
- **Live API latency.** TheSportsDB and TVMaze calls add ~2–5s to ContentAgent. TheSportsDB free key is rate-limited to 3 req/min on the `eventsday` endpoint — not a problem for normal use.
- **ContentAgent CSV fallback.** If both live APIs return no results (no events that day, or network issues), the system falls back silently to `data/programs.csv`. The schedule will still generate but with static placeholder content.
- **No auth.** The API has no authentication — any request to `localhost:8000` is accepted.

---

## Gitignored Paths

```
.env
__pycache__/
*.pyc / *.pyo
vectorstore/
.DS_Store
```
