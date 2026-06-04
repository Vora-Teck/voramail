from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity
)
import uuid
from root.models import *
from root.extensions import db
from root.security.utils import *
from root.security.mail import send_api_mail
from root.schemas import *
from root.token_limits import token_limited
from root.config import INTERNAL_API_KEY
from root.security.auth_utils import require_secret_key, require_public_key, require_active_user
from decimal import Decimal
import time


api_bp = Blueprint("api", __name__, url_prefix="/api")

def register_api(app):
    app.register_blueprint(api_bp)

# ----------- HTTP endpoints -------------------------------
@api_bp.route("/send-mail", methods=["POST"])
@require_secret_key
@token_limited(request)
def send_email():
    user = request.current_user
    body = request.get_json() or {}
    account_id = body.get("account_id", "")
    subject = body.get("subject", "")
    recipients = body.get("recipients", [])
    message = body.get("content", "")
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)

    job_id = str(uuid.uuid4())
    try:
        account = Account.query.filter_by(user=user, account_id=account_id).first()
        if not account:
            return jsonify(error="Email account ID not found"), 404
        if account.ip_whitelist and ip not in account.ip_whitelist:
            return jsonify(error="Unauthorized IP origin"), 401
        job = EmailMessage(
            message_id=job_id, user_id=user.id, user=user,
            mode="api", account_id=account_id, account=account,
            subject=subject, recipients=recipients,
            message=message, status=JobStatus.queued,
            callback_url=account.callback_url, ip_address=ip
        )
        db.session.add(job)
        db.session.commit()
        resp = send_api_mail(account, job)
        user.consume_api()
        db.session.commit()
        if "error" in resp:
            job.status = JobStatus("failed")
            db.session.commit()
            return jsonify({
                "success": False, "message_id": job.message_id, "status": job.status.value, "message": resp["error"]
            }), 200
        job.status = JobStatus("completed")
        db.session.commit()
        return jsonify({
            "success": True, "message_id": job.message_id, "status": job.status.value, "message": "message sent successfully"
        }), 200
    except Exception as e:
        return jsonify(error=f"Server error: {str(e)}"), 500

@api_bp.route("/accounts", methods=["GET"])
@require_secret_key
def email_accounts():
    user = request.current_user
    try:
        accounts = Account.query.filter_by(user_id=user.id)
        return jsonify(accounts_schema.dump(accounts)), 200
    except Exception as e:
        #raise e
        return jsonify(error=f"Error occurred: {e}"), 500

@api_bp.route("/<account_id>/mails", methods=["GET"])
@require_secret_key
def email_messages(account_id):
    user = request.current_user
    try:
        page = request.args.get("page", 1, int)
        per_page = request.args.get("per_page", 20, int)
        job_stat = request.args.get("status", "")

        account = Account.query.filter_by(user_id=user.id, account_id=account_id).first()
        if not account:
            return jsonify(error="Invalid account ID"), 404

        if per_page > 30: per_page = 30
        if per_page < 1: per_page = 20
        if page < 1: page = 1

        items = EmailMessage.query.filter_by(account_id=account.id)
        if job_stat and job_stat in ['queued', 'running', 'completed', 'failed']:
            items = items.filter_by(status=JobStatus(job_stat), mode="api")
        pagination = (
            items.order_by(EmailMessage.created_at.desc())
            .paginate(
                page=page, per_page=per_page, error_out=False
            )
        )
        messages = pagination.items

        return jsonify({
            "pages": pagination.pages,
            "page": page,
            "total_items": pagination.total,
            "has_prev": pagination.has_prev,
            "has_next": pagination.has_next,
            "data": [{
                "message_id": m.message_id,
                "status": m.status.value,
                "subject": m.subject,
                "created_at": m.created_at.isoformat(),
                "updated_at": m.updated_at.isoformat()
            } for m in messages]
        }), 200
    except Exception as e:
        return jsonify(error=f"Error occurred: {e}"), 500

@api_bp.route("/mails/<mail_id>", methods=["GET"])
@require_secret_key
def email_message(mail_id):
    user = request.current_user
    try:
        message = EmailMessage.query.filter_by(user_id=user.id, message_id=mail_id).first()
        if not message:
            return jsonify(error="Invalid mail ID"), 404
        return jsonify({
            "message_id": message.message_id,
            "mode": message.mode,
            "subject": message.subject,
            "sender_email": message.account.smtp_username,
            "recipients": message.recipients,
            "message": message.message,
            "status": message.status.value,
            "callback_url": message.callback_url,
            "sender": message.account.smtp_username,
            "ip_address": message.ip_address,
            "created_at": message.created_at.isoformat()
        }), 200
    except Exception as e:
        return jsonify(error=f"Error occurred: {e}"), 500

