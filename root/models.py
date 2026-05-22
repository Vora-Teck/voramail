# models.py
import enum
from datetime import datetime, date, timedelta
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
from root.extensions import db
from root.security.encryption import encrypt, decrypt


class Plan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    level = db.Column(db.Integer, default=1)
    description = db.Column(db.String(120), nullable=True)
    monthly_price = db.Column(db.Numeric(10, 2), default=0.00)
    quarterly_price = db.Column(db.Numeric(10, 2), default=0.00)
    biannual_price = db.Column(db.Numeric(10, 2), default=0.00)
    annual_price = db.Column(db.Numeric(10, 2), default=0.00)
    monthly_api_limit = db.Column(db.Integer, default=2000)
    daily_api_limit = db.Column(db.Integer, default=100)
    max_accounts = db.Column(db.Integer, default=3)
    features = db.Column(db.JSON, default=list)


class ConfirmationCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    code = db.Column(db.String(6), nullable=True)
    date = db.Column(db.DateTime, default=datetime.now)
    expiration = db.Column(db.DateTime, nullable=True)
    expired = db.Column(db.Boolean, default=False)
    verified = db.Column(db.Boolean, default=False)


class APIUsage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", backref="api_usages")
    date = db.Column(db.Date, default=date.today)
    api_used = db.Column(db.Integer, default=0)


class UserRole(enum.Enum):
    admin = "admin"
    client = "client"
    superuser = "superuser"

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(120), nullable=True)
    last_name = db.Column(db.String(120), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    public_key = db.Column(db.String(64), unique=True, index=True, nullable=True)
    secret_key_hash = db.Column(db.String(255), nullable=True)

    role = db.Column(db.Enum(UserRole), default=UserRole.client, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    failed_logins = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    plan_id = db.Column(db.Integer, db.ForeignKey("plan.id"), nullable=True)
    plan = db.relationship("Plan", backref="users")

    start_date = db.Column(db.Date, default=date.today)
    expiry_date = db.Column(db.Date, nullable=True)
    duration = db.Column(db.String(120), default="", nullable=False)
    expired = db.Column(db.Boolean, default=False)
    auto_renewal = db.Column(db.Boolean, default=True)

    daily_api_limit = db.Column(db.Integer, default=100)
    daily_api_used = db.Column(db.Integer, default=0)
    last_api_reset = db.Column(db.Date, default=date.today)

    monthly_api_limit = db.Column(db.Integer, default=2000)
    monthly_api_used = db.Column(db.Integer, default=0)
    monthly_api_reset = db.Column(db.Date, default=date.today)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_secret_key(self, raw_secret: str):
        self.secret_key_hash = generate_password_hash(raw_secret)

    def check_secret_key(self, raw_secret: str) -> bool:
        return check_password_hash(self.secret_key_hash, raw_secret)

    @staticmethod
    def generate_secret_key():
        return secrets.token_urlsafe(64)

    def reset_monthly_api_if_needed(self):
        if self.monthly_api_reset + timedelta(days=30) < date.today():
            self.monthly_api_used = 0
            self.monthly_api_reset = date.today()

    def reset_daily_api_if_needed(self):
        if self.last_api_reset < date.today():
            self.daily_api_used = 0
            self.last_api_reset = date.today()

    def can_consume_api(self):
        self.reset_monthly_api_if_needed()
        self.reset_daily_api_if_needed()
        return (
            self.daily_api_used < self.daily_api_limit
            and self.monthly_api_used < self.monthly_api_limit
        )

    def consume_api(self):
        self.daily_api_used += 1
        self.monthly_api_used += 1
        usage = APIUsage.query.filter_by(
            user_id=self.id,
            date=date.today()
        ).first()
        if not usage:
            usage = APIUsage(user_id=self.id, user=self, api_used=0)
            db.session.add(usage)
            db.session.commit()
        usage.api_used += 1


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", backref="transactions")

    amount = db.Column(db.Numeric(10, 2))
    tokens_bought = db.Column(db.Integer)
    status = db.Column(db.String(50))
    reference = db.Column(db.String(100), unique=True)
    description = db.Column(db.String(255))
    details = db.Column(db.JSON)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Upload(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    file = db.Column(db.String(255), nullable=True)


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True)
    account_id = db.Column(db.String(64), unique=True, index=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    user = db.relationship("User", backref="email_accounts")
    name = db.Column(db.String(120), nullable=False)
    smtp_username = db.Column(db.String(120), nullable=False, unique=True)
    smtp_host = db.Column(db.String(100), nullable=True, default="smtp.gmail.com")
    smtp_password = db.Column(db.Text, nullable=True)
    encryption = db.Column(db.JSON, nullable=True, default=dict)
    smtp_data = db.Column(db.JSON, nullable=True, default=dict)
    ip_whitelist = db.Column(db.JSON, nullable=True, default=list)
    callback_url = db.Column(db.Text, default="")
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now)
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=datetime.now, default=datetime.now)

    def encrypt_password(self, password: str):
        self.smtp_password = encrypt(password)
    
    def decrypt_password(self):
        if self.smtp_password:
            return decrypt(self.smtp_password)
        return ""


class JobStatus(enum.Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"

class EmailMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True)
    message_id = db.Column(db.String(64), unique=True, index=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    user = db.relationship("User", backref="email_messages")
    mode = db.Column(db.String(20), nullable=False, default="api")
    account_id = db.Column(db.Integer, db.ForeignKey("account.id"), nullable=True)
    account = db.relationship("Account", backref="email_messages")
    subject = db.Column(db.String(64), nullable=False)
    recipients = db.Column(db.JSON, nullable=True, default=list)
    message = db.Column(db.Text, nullable=True)
    status = db.Column(db.Enum(JobStatus), default=JobStatus.queued, nullable=False)
    callback_url = db.Column(db.Text, nullable=True)
    callback_sent = db.Column(db.Boolean, default=False)
    document_id = db.Column(db.Integer, db.ForeignKey("upload.id"), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now)
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=datetime.now, default=datetime.now)
