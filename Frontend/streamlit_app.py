import time
import pandas as pd
import streamlit as st
import requests

API_URL = "http://localhost:8000"

st.set_page_config(page_title="TV Scheduler AI", layout="wide")

# --- Sidebar ---
with st.sidebar:

    # Knowledge Base / Ingest
    st.header("Knowledge Base")
    if st.button("Rebuild Knowledge Base"):
        resp = requests.post(f"{API_URL}/ingest")
        st.session_state["ingest_job_id"] = resp.json()["job_id"]
        st.rerun()

    if "ingest_job_id" in st.session_state:
        ingest_resp = requests.get(f"{API_URL}/job/{st.session_state['ingest_job_id']}")
        ingest_job = ingest_resp.json()
        if ingest_job["status"] == "running":
            st.info("Rebuilding vectorstore...")
        elif ingest_job["status"] == "done":
            st.success("Knowledge base rebuilt.")
            del st.session_state["ingest_job_id"]
        elif ingest_job["status"] == "error":
            st.error(f"Ingest failed: {ingest_job.get('error', '')}")
            del st.session_state["ingest_job_id"]

    st.divider()

    # Schedule History
    st.header("Schedule History")
    if st.button("Refresh"):
        st.session_state.pop("history", None)

    if "history" not in st.session_state:
        try:
            resp = requests.get(f"{API_URL}/schedules", timeout=3)
            st.session_state["history"] = resp.json() if resp.status_code == 200 else []
        except Exception:
            st.session_state["history"] = []

    for item in st.session_state.get("history", []):
        label = f"{item['day']}  •  {item['created_at'][:16]}"
        if st.button(label, key=f"hist_{item['id']}"):
            st.session_state["load_id"] = item["id"]

# --- Load historical schedule if selected ---
if "load_id" in st.session_state:
    resp = requests.get(f"{API_URL}/schedules/{st.session_state.pop('load_id')}")
    if resp.status_code == 200:
        data = resp.json()
        st.subheader(f"Loaded: {data['day']} — {data['created_at'][:16]}")
        st.dataframe(pd.DataFrame(data["schedule"]), use_container_width=True)
        st.stop()

# --- Main UI ---
st.title("📺 TV Scheduler AI")
st.write("Generate optimized 24-hour TV schedules using AI agents.")

day = st.selectbox(
    "Select Day",
    ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
)

if st.button("Generate Schedule"):
    resp = requests.post(f"{API_URL}/generate-schedule", json={"day": day})
    st.session_state["job_id"] = resp.json()["job_id"]
    st.session_state["job_messages"] = []
    st.rerun()

# --- Polling loop ---
if "job_id" in st.session_state:
    job_id = st.session_state["job_id"]

    resp = requests.get(f"{API_URL}/job/{job_id}")
    job = resp.json()

    st.session_state["job_messages"] = job.get("messages", [])

    st.subheader("Agent Progress")
    for msg in st.session_state["job_messages"]:
        st.write(f"✅ {msg}")

    if job["status"] == "running":
        with st.spinner("Agents working..."):
            time.sleep(1)
        st.rerun()

    elif job["status"] == "done":
        result = job["result"]
        st.success("Schedule generated successfully!")
        st.dataframe(pd.DataFrame(result["schedule"]), use_container_width=True)
        del st.session_state["job_id"]
        del st.session_state["job_messages"]
        st.session_state.pop("history", None)

    elif job["status"] == "error":
        st.error(f"Error: {job.get('error', 'Unknown error')}")
        del st.session_state["job_id"]
