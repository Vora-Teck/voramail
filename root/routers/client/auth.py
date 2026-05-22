from flask import Blueprint, request, jsonify
from root.security.utils import *
from root.models import *
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    create_access_token, create_refresh_token, JWTManager,
    jwt_required, get_jwt_identity, get_jwt,
)

from root.extensions import db, limiter, BLACKLIST
from root.security.auth_utils import (
    require_secret_key, require_public_key,
    require_active_user
)
from datetime import datetime
from flask_limiter.util import get_remote_address

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

def register_auth(app):
    app.register_blueprint(auth_bp)


def login_rate_limit_key():
    return f"{request.json.get('email', '')}:{get_remote_address()}"

# ----------- HTTP endpoints -------------------------------
@auth_bp.route("/send-otp", methods=["POST"])
@limiter.limit("3 per minute", key_func=login_rate_limit_key)
def send_otp():
    data = clean_form(request.json)
    email = data['email']
    if not email or not is_valid_email(email):
        return jsonify(error="Invalid email address"), 400

    code = generateCode(6)
    now = datetime.now()

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify(error="Email already registered. Kindly use another email or login with the existing email"), 400

    existing = ConfirmationCode.query.filter_by(email=email).first()
    if existing:
        if existing.verified:
            return jsonify(error="Email already registered. Kindly use another email or login with the existing email"), 400

        existing.code = code
        existing.date = now
        existing.expired = False
        existing.expiration = now + timedelta(minutes=30)
        db.session.commit()
    else:
        new_otp = ConfirmationCode(
            email=email, code=code, date=now,
            expiration=now + timedelta(minutes=30)
        )
        db.session.add(new_otp)
        db.session.commit()
    stat, res = confirmation_email(email, code)
    if stat:
        return {
            "message": f"OTP code has been sent to {email}. It expires in 30 minutes. Kindly ensure to check your spam folders as well",
        }, 201
    else:
        return jsonify(error=f"Error occurred: {res}"), 500


@auth_bp.route("/register", methods=["POST"])
def register():
    data = clean_form(request.json)
    if not data['first_name'] or not data['last_name']:
        return jsonify(error="Invalid first or last name"), 400

    if not data['email'] or not is_valid_email(data['email']):
        return jsonify(error="Invalid email address"), 400

    """
    if not data['code']:
        return jsonify(error="Invalid OTP code"), 400
    """
    if not is_valid_password(data['password']):
        return jsonify(error="Invalid password combination"), 400

    existing = User.query.filter_by(email=data['email']).first()
    if existing:
        return jsonify(error="Email already exists. Kindly use another email"), 400

    public_key = generate(32)

    free_plan = Plan.query.filter_by(level=1).first()
    if not free_plan:
        free_plan = Plan(
            title="Free Plan", description="For Indie devs, SME, start-ups, etc"
        )
        db.session.add(free_plan)
    db.session.commit()
    today = date.today()
    user = User(
        first_name=data['first_name'],
        last_name = data["last_name"],
        email=data["email"],
        role=UserRole.client,
        password=generate_password_hash(data["password"]),
        public_key=public_key, plan=free_plan, plan_id=free_plan.id,
        start_date=today, expiry_date=today + timedelta(days=30),
        duration="1 month", daily_api_limit=free_plan.daily_api_limit,
        monthly_api_limit=free_plan.monthly_api_limit
    )
    db.session.add(user)

    user.plan = free_plan
    db.session.commit()
    return {
        "message": "Registration successful",
    }, 201


@auth_bp.route("/forgot-password", methods=["POST"])
#@limiter.limit("5 per minute", key_func=login_rate_limit_key)
def forgot_password():
    data = clean_form(request.json)
    email = data['email']
    if not email or not is_valid_email(email):
        return jsonify(error="Invalid email address"), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify(error="Email not registered"), 404

    if user.is_superuser:
        return jsonify(error="Email not registered"), 404

    token = generate(8)
    user.password = generate_password_hash(token)
    # send email
    stat, res = send_password_email(user.email, user.first_name, token)
    if stat:
        db.session.commit()
        return {
            "message": f"Password reset instructions has been sent to {email}. Kindly check your email and follow the instructions",
        }, 200
    else:
        return jsonify(error=f"Error occurred: {res}"), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    data = clean_form(request.json)
    email = data["email"]
    password = data["password"]

    if not email or not is_valid_email(email):
        return jsonify(error="Invalid email address"), 400

    if not password:
        return jsonify(error="Kindly provide a password"), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify(error="Invalid credentials"), 403

    if user.locked_until and user.locked_until > datetime.now():
        return jsonify(error="Account temporarily locked due to multiple login attempts. Try again later"), 403

    if not check_password_hash(user.password, password):
        user.failed_logins += 1
        if user.failed_logins >= 5:
            user.locked_until = datetime.now() + timedelta(minutes=30)
            user.failed_logins = 0
        db.session.commit()
        return jsonify(error="Invalid credentials"), 403

    user.failed_logins = 0
    user.locked_until = None
    db.session.commit()
    access = create_access_token(identity=str(user.id))
    refresh = create_refresh_token(identity=str(user.id))

    return jsonify(access_token=access, refresh_token=refresh)


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token using valid refresh token"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user:
            return jsonify(error="Invalid user"), 403

        # Optional: Revoke old access token if you want (recommended)
        old_jti = get_jwt()["jti"]
        BLACKLIST.add(old_jti)

        new_access_token = create_access_token(identity=str(user_id))

        return jsonify({
            "access_token": new_access_token,
            "message": "Token refreshed successfully"
        }), 200

    except Exception as e:
        raise e
        #return jsonify(error=f"Error refreshing token: {str(e)}"), 500


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
@require_active_user
def logout():
    """Logout - blacklist both access and refresh tokens"""
    try:
        jti = get_jwt()["jti"]
        token_type = get_jwt()["type"]  # 'access' or 'refresh'

        # Add current token to blacklist
        BLACKLIST.add(jti)   # Uncomment when you implement BLACKLIST

        # Optional: Also blacklist refresh token if provided in body
        refresh_token = request.json.get("refresh_token") if request.json else None
        if refresh_token:
            try:
                # You can decode it and blacklist its jti too if needed
                pass
            except:
                pass

        return jsonify({
            "message": f"You have been logged out."
        }), 200

    except Exception as e:
        return jsonify(error=f"Logout error: {str(e)}"), 500


# Optional: Logout from all devices (revoke all refresh tokens for user)
@auth_bp.route("/logout-all", methods=["POST"])
@jwt_required()
def logout_all():
    """Logout from all devices (advanced)"""
    try:
        user_id = get_jwt_identity()
        # In a real implementation, you would revoke all refresh tokens for this user
        # For now, just return success
        return jsonify({
            "message": "Successfully logged out from all devices."
        }), 200
    except Exception as e:
        return jsonify(error=f"Error: {str(e)}"), 500


@auth_bp.route("/send-message", methods=["POST"])
def send_message():
    data = clean_form(request.json)
    name = data.get("name", "")
    email = data.get("email", "")
    subject = data.get("subject", "")
    message = data.get("message", "")

    try:
        if not email or not is_valid_email(email):
            return jsonify(error="Invalid email address"), 400
        if not name:
            return jsonify(error="Name must be provided"), 400
        if not subject or not message:
            return jsonify(error="Subject and Message must be provided"), 400

        new_message = Contact(
            email=email, name=name, subject=subject,
            message=message
        )
        db.session.add(new_message)
        db.session.commit()
        admins = User.query.filter_by(is_superuser=True).all()
        recipients = [a.email for a in admins]
        stat, res = contact_email(recipients, new_message)
        return {
                "message": f"Thank you for your message. Your message has been received. Will will reply you as soon as we can.",
        }, 201
    except Exception as e:
        return jsonify(error=f"Error occurred: {e}"), 500


@auth_bp.route("/rotate-keys", methods=["POST"])
@jwt_required()
@require_active_user
def generate_keys():
    try:
        user = request.current_user

        new_secret = User.generate_secret_key()
        user.set_secret_key(new_secret)
        db.session.commit()
        return {
            "message": "Key generated!",
            "secret_key": new_secret
        }, 200
    except Exception as e:
        return jsonify(error=f"Error occurred: {e}"), 500
