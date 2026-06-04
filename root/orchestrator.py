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
from root.security.mail import send_api_mail


# Map tasks to in-process handlers (functions) when running single-process
# We'll import handlers lazily to avoid circular imports

# --- Job runner thread -----------------------------------------------------
def requeue_stale_jobs():
    result = EmailMessage.query.filter(EmailMessage.status == JobStatus.running)
    if not result:
        return
    for j in result:
        j.status = JobStatus.queued
        db.session.commit()
    print(f"Requeued {result.count()} stale 'running' jobs to 'queued'.")


def fetch_and_lock_next_job(app):
    # simple: order by created_at asc, select first queued job and mark running
    with app.app_context():
        job = EmailMessage.query.filter(EmailMessage.status == JobStatus.queued).order_by(EmailMessage.created_at.asc()).with_for_update().first()
        if not job:
            return None
        job.status = JobStatus.running
        db.session.commit()
        return job


def process_job(app, job):
    print(f"Processing {job.message_id}")
    # prefer to call in-process handler if available
    with app.app_context():
        try:
            resp = send_api_mail(job.account, job)
            callback_payload = {}
            if "error" in resp:
                job.status = JobStatus("failed")
                callback_payload["success"] = False
                callback_payload["message"] = resp["error"]
            else:
                job.status = JobStatus("completed")
                callback_payload["success"] = True
                callback_payload["message"] = "message sent successfully"
            job.result = callback_payload
            db.session.commit()
            callback_payload["message_id"] = job.message_id
            callback_payload['status'] = job.status
            # callback if present (encrypt payload)
            callback_url = job.callback_url
            if callback_url:
                # encrypt using INTERNAL_API_KEY as shared secret
                try:
                    signature = encrypt_payload(callback_payload, job.user.public_key)
                    with httpx.Client(timeout=10.0) as client:
                        print(f"Sending webhook to {callback_url}")
                        callback = client.post(
                            callback_url,
                            json=callback_payload,
                            headers={"X-Signature": signature}
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
            print(f"Job {job.message_id} failed during processing: {e}")


stop_flag = {"stop": False}
_runner_thread = None

def job_runner_loop(app, poll_interval=2.0):
    print("Job runner thread started.")
    while not stop_flag.get("stop"):
        try:
            job = fetch_and_lock_next_job(app)
            print(f"Locked mail: {job.message_id}")
            if not job:
                time.sleep(poll_interval)
            else:
                process_job(app, job)
        except Exception as e:
            db.session.rollback()
            print("Job runner exception:", e)
            time.sleep(poll_interval)
    print("Job runner thread stopped.")


def start_job_runner_thread(app):
    print("Requeuing Stale Mails...")
    with app.app_context():
        requeue_stale_jobs()
    global _runner_thread
    if _runner_thread and _runner_thread.is_alive():
        return
    _runner_thread = Thread(target=job_runner_loop, args=(app,), daemon=True)
    _runner_thread.start()





# ----------- HTTP endpoints -------------------------------



