from functools import wraps
from flask import request, jsonify
from root.models import User, UserRole
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity
)

def require_superuser(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        admin = User.query.get(user_id)
        if not admin:
            return jsonify(error="Unauthorized request"), 401

        if not admin.is_superuser or not admin.is_active:
            return jsonify(error="Unauthorized request"), 401

        request.current_user = admin

        return fn(*args, **kwargs)
    return wrapper

def require_active_user(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify(error="Unauthorized request"), 401

        if not user.is_active:
            return jsonify(error="Unauthorized request"), 401

        request.current_user = user

        return fn(*args, **kwargs)
    return wrapper


def require_public_key(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        public_key = request.headers.get("X-API-KEY")
        if not public_key:
            return jsonify({"error": "missing_public_key"}), 401

        user = User.query.filter_by(
            public_key=public_key,
            is_active=True
        ).first()

        if not user:
            return jsonify({"error": "invalid_public_key"}), 401

        request.current_user = user
        request.limiter_key = public_key  # 🔥 important
        return fn(*args, **kwargs)
    return wrapper


def require_secret_key(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        public_key = request.headers.get("X-API-KEY")
        secret = request.headers.get("X-SECRET-KEY")

        if not public_key or not secret:
            return jsonify({"error": "missing_api_credentials"}), 401

        user = User.query.filter_by(
            public_key=public_key,
            is_active=True
        ).first()

        if not user or not user.check_secret_key(secret):
            return jsonify({"error": "invalid_api_credentials"}), 401

        request.current_user = user
        request.limiter_key = public_key  # 🔥 per-user rate limit
        return fn(*args, **kwargs)
    return wrapper