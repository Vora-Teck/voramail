# orchestrator.py
import os
from root.models import *
from root.extensions import db
from typing import Any, Dict, Optional, List
import time
from threading import Thread
import httpx
from flask_jwt_extended import jwt_required

from root.config import INTERNAL_API_KEY
from root.security.encryption import encrypt_payload

from root.main import app, start_job_runner_thread


# Map tasks to in-process handlers (functions) when running single-process
# We'll import handlers lazily to avoid circular imports

# --- Job runner thread -----------------------------------------------------
def requeue_stale_jobs():
    """
    On startup, convert any jobs marked as 'running' back to 'queued' so they can be retried.
    This avoids leaving jobs in limbo when the process is interrupted.
    """
    with app.app_context():
        result = Job.query.filter(Job.status == JobStatus.running)
        if not result:
            return

        for j in result:
            j.status = JobStatus.queued
            db.session.commit()
        print(f"Requeued {result.count()} stale 'running' jobs to 'queued'.")


def fetch_and_lock_next_job():
    # simple: order by created_at asc, select first queued job and mark running
    job = Job.query.filter(Job.status == JobStatus.queued).order_by(Job.created_at.asc()).with_for_update().first()
    if not job:
        return None
    job.status = JobStatus.running
    db.session.commit()
    return job


def process_job(job):
    AGENT_MAP = {
        "ai_assistant": run_assistant_agent_sync,
        "generate_lesson": run_content_agent_sync,
        "generate_timetable": "http://localhost:8000/timetable/run",
        "generate_assessment": "http://localhost:8000/assessment/run",
    }

    agent_func = AGENT_MAP.get(job.task, AGENT_MAP["ai_assistant"])

    payload = {
        "job_id": job.job_id,
        "tenant_id": job.tenant_id,
        "user_id": job.user_id,
        "task": job.task,
        "payload": job.payload,
    }
    # prefer to call in-process handler if available
    try:
        resp = agent_func(payload)
        job.result = resp
        if resp['status'] == "invalid":
            job.status = JobStatus.invalid
        elif resp['status'] == "error":
            job.status = JobStatus.failed
        else:
            job.status = JobStatus.completed
        db.session.commit()

        # callback if present (encrypt payload)
        callback_url = job.payload.get("callback_url") if isinstance(job.payload, dict) else None
        # Try to use dedicated callback_url field first
        if getattr(job, "callback_url", None):
            callback_url = job.callback_url
        if callback_url:
            # encrypt using INTERNAL_API_KEY as shared secret
            try:
                encrypted = encrypt_payload(
                        {"job_id": job.job_id, "status": job.status.value, "result": resp['response']},
                        api_key=INTERNAL_API_KEY,  # encryption based on your X-API-Key
                    )
                with httpx.Client(timeout=10.0) as client:
                    callback = client.post(
                        callback_url,
                        json={"data": encrypted},
                        headers={"X-API-Key": INTERNAL_API_KEY}
                    )
                    if callback.status_code == 200:
                        job.callback_sent = True
                        db.session.commit()
            except Exception as e:
                # log but continue
                print("Callback POST failed:", e)
    except Exception as e:
        job.result = {"error": str(e)}
        job.status = JobStatus.failed
        db.session.commit()
        print(f"Job {job.job_id} failed during processing: {e}")


def job_runner_loop(stop_flag, poll_interval=2.0):

    print("Job runner thread started.")
    while not stop_flag.get("stop"):
        try:
            job = fetch_and_lock_next_job()
            if not job:
                time.sleep(poll_interval)
            else:
                process_job(job)
        except Exception as e:
            db.session.rollback()
            print("Job runner exception:", e)
            time.sleep(1.0)
    print("Job runner thread stopped.")


start_job_runner_thread(requeue_stale_jobs, job_runner_loop)


# ----------- HTTP endpoints -------------------------------



