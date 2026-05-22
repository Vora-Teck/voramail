from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity
)
from root.models import *
import uuid
from root.extensions import db
from root.security.auth_utils import require_superuser


users_bp = Blueprint("users", __name__, url_prefix="/users")

def register_users(app):
    app.register_blueprint(users_bp)


# ----------- HTTP endpoints -------------------------------
@users_bp.route("/", methods=["GET"])
@jwt_required()
@require_superuser
def list_users():
    admin = request.current_user
    query = User.query
    users = query.order_by(User.email.asc()).all()
    out = []
    for j in users:
        out.append({
            "id": j.id,
            "email": j.email,
            "is_admin": j.is_superuser,
            "is_active": j.is_active,
            "total_tokens": j.total_tokens,
            "tokens_used": j.tokens_used,
            "tokens_remaining": j.tokens_remaining,
            "created_at": j.created_at.isoformat() if j.created_at else None,
        })
    return jsonify(out)

@users_bp.route("/<user_id>", methods=["GET"])
@jwt_required()
@require_superuser
def get_user_info(user_id):
    admin = request.current_user
    user = User.query.get(user_id)
    token_usages = TokenUsage.query.filter_by(user_id=user_id)
    data = {
        "id": user.id,
        "email": user.email,
        "is_admin": user.is_superuser,
        "is_active": user.is_active,
        "total_tokens": user.total_tokens,
        "tokens_used": user.tokens_used,
        "tokens_remaining": user.tokens_remaining,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "token_usages": [
            {
                "date": t.date.isoformat(),
                "tokens_used": t.token_used
            } for t in token_usages
        ]
    }
    return jsonify(data)

@users_bp.route("/me", methods=["GET"])
@jwt_required()
@require_superuser
def get_me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify(error="Unauthorized request"), 401
    token_usages = TokenUsage.query.filter_by(user_id=user_id)
    data = {
        "id": user.id,
        "email": user.email,
        "total_tokens": user.total_tokens,
        "tokens_used": user.tokens_used,
        "tokens_remaining": user.tokens_remaining,
        "token_usages": [
            {
                "date": t.date.isoformat(),
                "tokens_used": t.token_used
            } for t in token_usages
        ]
    }
    return jsonify(data)
