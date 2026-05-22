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

@account_bp.route("/<account_id>", methods=["GET", "POST"])
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
            print(data)
            acc_name = data["name"]
            acc_username = data["username"]
            smtp_host = data["host"]
            smtp_pass = data.get("password", "")
            callback = data.get("callback", "")
            ips = data.get("ips", [])

            ips = list(set([i.strip() for i in ips if i.strip() != ""]))

            if not acc_name:
                return jsonify(error=f"Account name not provided"), 400
            if not acc_username:
                return jsonify(error=f"Account email address not provided"), 400
            if not is_valid_email(acc_username):
                return jsonify(error=f"Invalid email address provided"), 400
            if not smtp_host:
                return jsonify(error=f"SMTP host not provided"), 400
            if callback and not is_valid_url(callback):
                return jsonify(error=f"Invalid URL pattern for callback"), 400
            if len(ips) > 0 and any([not is_valid_ip(i) for i in ips]):
                return jsonify(error=f"Invalid IP address provided in IP whitelist"), 400

            email_host = None
            encryp = None
            if account.smtp_host != smtp_host:
                for s in smtp_hosts:
                    if s["smtp_host"] == smtp_host:
                        email_host = s
                        break
                if not email_host:
                    return jsonify(error=f"Invalid email host"), 400
                for p in email_host["ports"]:
                    if p["port"] == 587:
                        encryp = p
                        break

            account.name = acc_name
            account.callback_url = callback
            account.ip_whitelist = ips
            account.smtp_username = acc_username
            if email_host:
                account.smtp_host = smtp_host
                account.smtp_data = email_host
            if encryp:
                account.encryption = encryp
            if smtp_pass:
                account.encrypt_password(smtp_pass)
            db.session.commit()
            return jsonify(message="Email account updated successfully!"), 201
    except Exception as e:
        return jsonify(error=f"Error occurred: {e}"), 500


@account_bp.route("/jobs", methods=["GET"])
@jwt_required()
def list_jobs():
    tenant_id = request.args.get("tenant_id")
    status = request.args.get("status")
    limit = int(request.args.get("limit") or 50)
    offset = int(request.args.get("offset") or 0)
    x_api_key = request.headers.get("X-API-Key")
    query = Job.query()

    if x_api_key != INTERNAL_API_KEY:
        return jsonify(error="Unauthorized request"), 401
    if tenant_id:
        query = query.filter_by(tenant_id=tenant_id)
    if status:
        try:
            query = query.filter(Job.status == JobStatus(status))
        except Exception:
            return jsonify(error="Invalid status filter"), 400
    jobs = query.order_by(Job.created_at.desc()).limit(limit).offset(offset).all()
    out = []
    for j in jobs:
        out.append({
            "job_id": j.job_id,
            "tenant_id": j.tenant_id,
            "task": j.task,
            "status": j.status.value,
            "created_at": j.created_at.isoformat() if j.created_at else None,
            "updated_at": j.updated_at.isoformat() if j.updated_at else None
        })
    return jsonify(out)

@account_bp.route("/jobs/<job_id>", methods=["GET"])
@jwt_required()
def get_job(job_id):
    x_api_key = request.headers.get("X-API-Key")
    if x_api_key != INTERNAL_API_KEY:
        return jsonify(error="Unauthorized request"), 401
    job = Job.query.filter_by(job_id=job_id).first()
    if not job:
        return jsonify(error="job not found"), 404
    return jsonify({
        "job_id": job.job_id,
        "tenant_id": job.tenant_id,
        "task": job.task,
        "status": job.status.value,
        "payload": job.payload,
        "result": job.result,
        "callback_sent": job.callback_sent,
        "callback_url": job.callback_url,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None
    })


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

