from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity
)
import uuid
from root.extensions import db
from root.models import (
    User, EmailMessage, JobStatus, UserRole, Account, Upload
)
from root.security.utils import *
from root.schemas import *
from root.token_limits import token_limited
from root.config import INTERNAL_API_KEY
from root.security.auth_utils import require_secret_key, require_public_key, require_active_user
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from root.smtp_host import smtp_hosts

account_bp = Blueprint("account", __name__, url_prefix="/accounts")

def register_account(app):
    app.register_blueprint(account_bp)

# ----------- HTTP endpoints -------------------------------
@account_bp.route("/", methods=["GET", "POST"])
@jwt_required()
@require_active_user
def email_accounts():
    user = request.current_user
    user_id = get_jwt_identity()
    try:
        if request.method == "GET":
            accounts = Account.query.filter_by(user_id=user_id)
            return jsonify(accounts_schema.dump(accounts)), 200
        elif request.method == "POST":
            if len(user.email_accounts) >= user.plan.max_accounts:
                return jsonify(error=f"You have reached your limit of {user.plan.max_accounts} email accounts.")
            data = clean_form(request.json)
            acc_name = data["name"]
            acc_username = data["username"]
            smtp_host = data["host"]

            if not acc_name or acc_name.strip() == "":
                return jsonify(error=f"Account name not provided"), 400
            if not acc_username or not is_valid_email(acc_username):
                return jsonify(error=f"Invalid email provided"), 400
            if not smtp_host or smtp_host.strip() == "":
                return jsonify(error=f"Host not provided"), 400

            existing = Account.query.filter_by(smtp_username=acc_username).first()
            if existing:
                return jsonify(error=f"Email account already exists. kindly use another."), 409
            account_id = f"{slugify(acc_name.split()[0])}_{generate_lower(10)}"
            email_host = {}
            encryption = {}
            for s in smtp_hosts:
                if s["smtp_host"] == smtp_host:
                    email_host = s
                    break
            if not email_host:
                return jsonify(error=f"Invalid email host"), 400
            for p in email_host["ports"]:
                if p["port"] == 587:
                    encryption = p
                    break
            account = Account(
                account_id=account_id, user_id=user.id, user=user,
                name=acc_name, smtp_username=acc_username, smtp_host=smtp_host,
                encryption=encryption, smtp_data=email_host
            )
            db.session.add(account)
            db.session.commit()
            return jsonify(message="Email account created successfully!"), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify(error=f"Email account already exists. kindly use another."), 409
    except Exception as e:
        #raise e
        return jsonify(error=f"Error occurred: {e}"), 500

@account_bp.route("/<account_id>", methods=["GET", "POST", "DELETE"])
@jwt_required()
@require_active_user
def email_account(account_id):
    user = request.current_user
    user_id = get_jwt_identity()
    try:
        account = Account.query.filter_by(user_id=user_id, account_id=account_id).first()
        if not account:
            return jsonify(error="Email account Not Found"), 404
        if request.method == "GET":
            return jsonify(account_detail_schema.dump(account)), 200
        elif request.method == "POST":
            data = clean_form(request.json)
            acc_name = data["name"]
            smtp_pass = data.get("password", "")
            callback = data.get("callback", "")
            ips = data.get("ips", [])

            ips = list(set([i.strip() for i in ips if i.strip() != ""]))

            if not acc_name:
                return jsonify(error=f"Account name not provided"), 400
            if callback and not is_valid_url(callback):
                return jsonify(error=f"Invalid URL pattern for callback"), 400
            if len(ips) > 0 and any([not is_valid_ip(i) for i in ips]):
                return jsonify(error=f"Invalid IP address provided in IP whitelist"), 400

            account.name = acc_name
            account.callback_url = callback
            account.ip_whitelist = ips
            if smtp_pass:
                account.encrypt_password(smtp_pass)
            db.session.commit()
            return jsonify(message="Email account updated successfully!"), 201
        elif request.method == "DELETE":
            db.session.delete(account)
            db.session.commit()
            return jsonify(message="Email account deleted successfully!"), 200
    except Exception as e:
        return jsonify(error=f"Error occurred: {e}"), 500

@account_bp.route("/<account_id>/mails", methods=["GET"])
@jwt_required()
@require_active_user
def email_messages(account_id):
    user = request.current_user
    user_id = get_jwt_identity()
    try:
        page = request.args.get("page", 1, int)
        per_page = request.args.get("per_page", 20, int)
        job_stat = request.args.get("status", "")

        account = Account.query.filter_by(user_id=user_id, account_id=account_id).first()
        if not account:
            return jsonify(error="Email account Not Found"), 404

        if per_page > 30: per_page = 30
        if per_page < 1: per_page = 20
        if page < 1: page = 1

        items = EmailMessage.query.filter_by(account_id=account.id)
        if job_stat and job_stat in ['queued', 'running', 'completed', 'failed']:
            items = items.filter_by(status=JobStatus(job_stat))
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
                "id": m.id,
                "message_id": m.message_id,
                "status": m.status.value,
                "subject": m.subject,
                "created_at": m.created_at.isoformat(),
                "updated_at": m.updated_at.isoformat(),
                "mode": m.mode
            } for m in messages]
        }), 200
    except Exception as e:
        return jsonify(error=f"Error occurred: {e}"), 500

@account_bp.route("/mails/<mail_id>", methods=["GET"])
@jwt_required()
@require_active_user
def email_message(mail_id):
    user = request.current_user
    user_id = get_jwt_identity()
    try:
        job = EmailMessage.query.get(mail_id)
        if not job:
            return jsonify(error="Mail not found"), 404
        if job.user_id != user.id:
            return jsonify(error="Mail not found"), 404
        return jsonify({
            "message_id": job.message_id,
            "status": job.status.value,
            "subject": job.subject,
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat(),
            "mode": job.mode,
            "account": account_schema.dump(job.account),
            "ip_address": job.ip_address,
            "recipients": job.recipients,
            "callback_url": job.callback_url,
            "callback_sent": job.callback_sent
        }), 200
    except Exception as e:
        return jsonify(error=f"Error occurred: {e}"), 500

@account_bp.route("/upload-rag-doc/<agent_id>", methods=["POST"])
@jwt_required()
def upload_rag_document(agent_id):
    user = request.current_user
    user_id = get_jwt_identity()
    if not request.files or "file" not in request.files:
        return jsonify(error="File Missing"), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify(error="Empty Filename"), 400
    if not allowed_file(file.filename):
        return jsonify(error="Invalid file type/extension"), 400
    if request.content_length > config.MAX_CONTENT_LENGTH:
        return jsonify(error="File too large"), 400
    try:
        agent = Agent.query.get(agent_id)
        if not agent or agent.user_id != user_id:
            return jsonify(error="Agent not found"), 404
        filename = save_uploaded_file(file, "rags")
        upload = Upload(owner=user.id, file=f"rags/{filename}")
        db.session.add(upload)
        db.session.commit()
        agent.document_id = upload.id
        db.session.commit()
        return jsonify(message="File uploaded successfully"), 201
    except Exception as e:
        return jsonify(error=f"Error occurred: {e}"), 500

