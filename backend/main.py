import uuid
import threading
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.schemas import ScheduleRequest
from backend.workflow import SchedulerWorkflow
from backend.database import engine, SessionLocal
from backend.models import Schedule, Base
from backend.rag.ingest import ingest

Base.metadata.create_all(bind=engine)

app = FastAPI(title="TV Scheduler API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

jobs: dict = {}


def run_workflow(job_id: str, day: str):
    def callback(msg: str):
        jobs[job_id]["messages"].append(msg)

    try:
        result = SchedulerWorkflow(callback=callback).run(day)

        db = SessionLocal()
        record = Schedule(day=day, schedule_data=result)
        db.add(record)
        db.commit()
        db.refresh(record)
        db.close()

        jobs[job_id].update({"status": "done", "result": result, "schedule_id": record.id})
    except Exception as e:
        jobs[job_id].update({"status": "error", "error": str(e)})


@app.post("/generate-schedule")
def generate_schedule(request: ScheduleRequest):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "running", "messages": [], "result": None}
    threading.Thread(target=run_workflow, args=(job_id, request.day), daemon=True).start()
    return {"job_id": job_id}


@app.get("/job/{job_id}")
def get_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]


@app.post("/ingest")
def run_ingest():
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "running", "messages": ["Rebuilding knowledge base..."], "result": None}

    def _ingest():
        try:
            ingest()
            jobs[job_id].update({"status": "done", "messages": ["Knowledge base rebuilt successfully."]})
        except Exception as e:
            jobs[job_id].update({"status": "error", "error": str(e)})

    threading.Thread(target=_ingest, daemon=True).start()
    return {"job_id": job_id}


@app.get("/schedules")
def list_schedules():
    db = SessionLocal()
    rows = db.query(Schedule).order_by(Schedule.created_at.desc()).limit(20).all()
    db.close()
    return [{"id": r.id, "day": r.day, "created_at": str(r.created_at)} for r in rows]


@app.get("/schedules/{schedule_id}")
def get_schedule(schedule_id: int):
    db = SessionLocal()
    row = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    db.close()
    if not row:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {"id": row.id, "day": row.day, "created_at": str(row.created_at), "schedule": row.schedule_data}
