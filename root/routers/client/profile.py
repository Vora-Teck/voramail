from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity
)
from root.security.utils import *
from root.models import *
import uuid
from root.extensions import db
from root.security.auth_utils import require_active_user
from datetime import date, timedelta
from root.schemas import *

profile_bp = Blueprint("me", __name__, url_prefix="/me")

def register_me(app):
    app.register_blueprint(profile_bp)


# ----------- HTTP endpoints -------------------------------
@profile_bp.route("/", methods=["GET"])
@jwt_required()
@require_active_user
def user_profile():
    user = request.current_user
    return jsonify(user_schema.dump(user))

@profile_bp.route("/kpi", methods=["GET"])
@jwt_required()
@require_active_user
def user_kpi():
    try:
        user = request.current_user
        user_id = get_jwt_identity()
        today = date.today()
        today_date = today.day
        today_month = today.month
        today_year = today.year
        add_days = 31
        if today_month in [9, 4, 6, 11]:
            add_days = 30
        elif today_month in [2]:
            add_days = 28
        start = date(today_year, today_month, 1)
        end = start + timedelta(days=add_days)
        messages = EmailMessage.query.filter_by(user_id=user_id).order_by(EmailMessage.created_at.desc())
        api_calls = messages.filter_by(mode="api")
        categories = {
            "queued": 0, "completed": 0, "failed": 0
        }
        for c in categories:
            categories[c] = api_calls.filter_by(status=JobStatus(c)).count()
        usage = {}
        for i in range(1, today_date + 1):
            usage[str(i)] = 0
        usages = APIUsage.query.filter(
            user_id == user_id,
            APIUsage.date >= start,
            APIUsage.date < end
        )
        total_api_calls = 0
        for u in usages:
            usage[str(u.date.day)] += u.api_used
            total_api_calls += u.api_used

        jobs = messages.limit(5)
        accounts = Account.query.filter_by(user_id=user_id)
        total_accounts = accounts.count()
        active_accounts = accounts.filter_by(active=True).count()
        data = {
            "total_api_calls": total_api_calls,
            "daily_api_limit": user.daily_api_limit,
            "daily_api_used": user.daily_api_used,
            "monthly_api_limit": user.monthly_api_limit,
            "monthly_api_used": user.monthly_api_used,
            "max_accounts": user.plan.max_accounts,
            "total_accounts": total_accounts,
            "active_accounts": active_accounts,
            "categories": categories,
            "token_usage": usage,
            "jobs": [
                {
                    "job_id": j.message_id,
                    "account": j.account.name,
                    "mode": j.mode,
                    "status": j.status.value,
                    "created_at": j.created_at.isoformat()
                } for j in jobs
            ]
        }
        return jsonify(data)
    except Exception as e:
        return jsonify(error=f"Error occurred: {e}"), 500


@profile_bp.route("/api-key", methods=["GET"])
@jwt_required()
@require_active_user
def get_public_key():
    user = request.current_user
    if not user.public_key:
        public_key = generate(32)
        user.public_key = public_key
        db.session.commit()
    data = {
        "public_key": user.public_key
    }
    return jsonify(data)


@profile_bp.route("/webhook", methods=["GET", "POST"])
@jwt_required()
@require_active_user
def get_webhook_data():
    user = request.current_user
    if request.method == "GET":
        datam = {
            "callback_url": user.callback_url,
            "ip_whitelist": user.ip_whitelist,
            "token_warning": user.token_warning,
            "token_critical": user.token_critical
        }
        return jsonify(datam)
    elif request.method == "POST":
        data = clean_form(request.json)
        callback = data["callback_url"]
        ip = data.get("ip_whitelist", [])
        token_w = data.get("token_warning", 0)
        token_c = data.get("token_critical", 0)

        if callback and not is_valid_url(callback):
            return jsonify(error="Invalid callback URL. Kindly ensure it starts with http:// or https://"), 400
        ip = [a.strip() for a in ip if a.strip() != ""]
        ip_list = []
        if ip:
            if any([not is_valid_ipv4(i) for i in ip]):
                return jsonify(error=f"Invalid IP provided"), 400
            ip_list = [i for i in ip if is_valid_ipv4(i)]
        user.callback_url = callback
        user.ip_whitelist = ip_list
        user.token_warning = int(token_w)
        user.token_critical = int(token_c)
        db.session.commit()
        return jsonify(message="Changes saved!"), 200

@profile_bp.route("/change-password", methods=["POST"])
@jwt_required()
@require_active_user
def change_password():
    user = request.current_user
    data = clean_form(request.json)
    if not check_password_hash(user.password, data["old_password"]):
        return jsonify(error="Invalid password"), 403
    if not is_valid_password(data["new_password"]):
        return jsonify(error="Invalid new password combination."), 400
    user.password = generate_password_hash(data["new_password"])
    db.session.commit()
    return jsonify(message="Password changed successfully"), 200
