from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from root.extensions import db
from root.models import User, APIUsage
from datetime import date

def token_limited(request):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = request.current_user

            if not user:
                return jsonify(error="user_not_found"), 404

            if not user.can_consume_api():
                if user.monthly_api_used >= user.monthly_api_limit:
                    return jsonify(
                        error="monthly_limit_exceeded",
                        monthly_limit=user.monthly_api_limit
                    ), 403

                return jsonify(
                    error="daily_limit_exceeded",
                    daily_limit=user.daily_api_limit
                ), 403

            response = fn(*args, **kwargs)

            user.consume_api()
            db.session.commit()

            return response
        return wrapper
    return decorator
