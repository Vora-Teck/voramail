# main.py
from flask import Flask, jsonify, request, render_template, send_file, abort
from flask_migrate import Migrate
from flask_limiter.errors import RateLimitExceeded
from flask_cors import CORS

from dotenv import load_dotenv
import os
from threading import Thread
import signal

from root import config
from root.extensions import db, jwt, limiter, ma
from root.security.handler import HTTPException
from root.security.request_logger import log_request_data
from root.routers.client import (
    register_account, register_api, register_me, register_auth
)
from root.routers.admin.users import register_users
from root.cli import create_superuser
from flask_jwt_extended import (
    jwt_required
)
from root.models import Upload
from root.smtp_host import smtp_hosts



# load environment
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# import registration helpers


app = Flask(__name__)

app.config.update(
    SQLALCHEMY_DATABASE_URI=config.DATABASE_URL,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    JWT_SECRET_KEY=config.JWT_SECRET_KEY,
    JWT_TOKEN_LOCATION="headers",
    JWT_HEADER_NAME="Authorization",
    JWT_HEADER_TYPE="Bearer",
    JWT_ACCESS_TOKEN_EXPIRES=config.JWT_ACCESS_TOKEN_EXPIRES,
    JWT_REFRESH_TOKEN_EXPIRES=config.JWT_REFRESH_TOKEN_EXPIRES,
    TEMPLATES_AUTO_RELOAD=config.DEBUG,
    SEND_FILE_MAX_AGE_DEFAULT=0 if config.DEBUG else 3600*2
)

CORS(app,
     resources={
        r"/*": {
            "origins": []
        }
    },
     methods=["GET", "POST", "OPTIONS"],
     allow_headers=["Content-Type", "X-API-Key", 'Authorization'],
     supports_credentials=False
     )

# Initialize database, Rate limiter and JWT
db.init_app(app)
jwt.init_app(app)
ma.init_app(app)
limiter.init_app(app)
# Register migrations
migrate = Migrate(app, db)
# Register blueprints (general routes)
register_auth(app)
# client routes
register_account(app)
register_api(app)
register_me(app)
# admin routes
register_users(app)

app.cli.add_command(create_superuser)

app.jinja_env.auto_reload = config.DEBUG

@app.before_request
def before_every_request():
    log_request_data()


@app.route("/files/<upload_id>")
@jwt_required()
def get_file(upload_id):
    user = request.current_user
    base_path = config.UPLOAD_BASE
    upload = Upload.query.get(upload_id)
    if not upload:
        abort(404)
    file_path = os.path.join(base_path, upload.file)
    if not os.path.exists(file_path):
        abort(404)
    if upload.owner_id != user.id:
        abort(403)
    return send_file(file_path)


# ============ GENERAL PAGES ======================
@app.route("/", methods=["GET"])
def index():
    return render_template("landing/index.html")

@app.route("/pricing", methods=["GET"])
def index_pricing():
    return render_template("landing/pricing.html")

@app.route("/docs", methods=["GET"])
def api_documentation():
    return render_template("landing/docs.html")

@app.route("/login")
def login():
    return render_template("landing/login.html")


# ============ AUTH PAGES ======================

@app.route("/dashboard", methods=["GET"])
def dashboard():
    return render_template("user/dashboard.html")

@app.route("/email-accounts", methods=["GET"])
def email_accounts():
    return render_template("user/account.html", smtp_hosts=smtp_hosts)

@app.route("/payments", methods=["GET"])
def index_payments():
    return render_template("user/payments.html")

@app.route("/analytics", methods=["GET"])
def index_analytics():
    return render_template("user/analytics.html")

@app.route("/settings", methods=["GET"])
def index_settings():
    return render_template("user/settings.html")

@app.route("/sandbox", methods=["GET"])
def sandbox():
    return render_template("user/sandbox.html")


# Graceful shutdown handling for background thread
stop_flag = {"stop": False}

def handle_sigterm(*args):
    stop_flag["stop"] = True

@app.errorhandler(HTTPException)
def handle_custom_http_exception(err):
    response = jsonify({
        "detail": err.detail,
        "status_code": err.status_code
    })
    response.status_code = err.status_code
    return response

@jwt.expired_token_loader
def expired(jwt_header, jwt_payload):
    return {"error": "token_expired"}, 401

@jwt.token_verification_failed_loader
def expired(jwt_header, jwt_payload):
    return {"error": "token_verification_failed"}, 401

@jwt.invalid_token_loader
def invalid(e):
    return {
        "error": f"invalid_token",
        "detail": str(e)
    }, 422

@jwt.unauthorized_loader
def missing(e):
    return {
        "error": "authorization_required",
        "detail": str(e)
    }, 401

@app.errorhandler(RateLimitExceeded)
def rate_limit_handler(e):
    return {
        "error": "rate_limit_exceeded",
        "detail": str(e)
    }, 429

signal.signal(signal.SIGINT, handle_sigterm)
signal.signal(signal.SIGTERM, handle_sigterm)

_runner_thread = None
def start_job_runner_thread(start_func, loop_func):
    print("Requeuing Jobs...")
    start_func()
    global _runner_thread
    if _runner_thread and _runner_thread.is_alive():
        return
    _runner_thread = Thread(target=loop_func, args=(stop_flag,), daemon=True)
    _runner_thread.start()

with app.app_context():
    db.create_all()

"""
if __name__ == "__main__":
    # Start job runner thread
    #start_job_runner_thread(stop_flag)
    # dev server
    app.run(host="0.0.0.0", port=int(config.DEV_PORT), debug=config.DEBUG)
"""