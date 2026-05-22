# app/config.py
import os
from dotenv import load_dotenv
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(BASE_DIR, ".env"))

DEBUG = True

LOGO_PATH = BASE_DIR / "logo.png"
LOGGING_PATH = BASE_DIR / "logs" / "requests.log"
IP_DB_PATH = BASE_DIR / "root" / "geoip" / "GeoLite2-City.mmdb"

# MEDIA UPLOAD
UPLOAD_BASE = os.path.expanduser("~/.uploads")
UPLOAD_FOLDERS = {
    "attachments": os.path.join(UPLOAD_BASE, "attachments")
}
for path in UPLOAD_FOLDERS.values():
    os.makedirs(path, exist_ok=True)

ALLOWED_EXTENSIONS = {"pdf", "docx", "doc"}
MAX_CONTENT_LENGTH = 5*1024*1024 #5MB

# MAX TOTAL ATTACHMENT SIZE (10MB)
MAX_TOTAL_ATTACHMENT_SIZE = 10 * 1024 * 1024

# MAX SINGLE FILE SIZE (5MB)
MAX_SINGLE_FILE_SIZE = 5 * 1024 * 1024

# ALLOWED MIME TYPES
ALLOWED_MIME_TYPES = {
    # Images
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/gif",

    # Documents
    "application/pdf",

    # Text
    "text/plain",
    "text/csv",
}

# PRODUCTION CONFIG
DEV_PORT = os.getenv("DEV_PORT")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if DEBUG:
    DATABASE_URL = os.getenv("TEST_DATABASE_URL")
else:
    DATABASE_URL = os.getenv("LIVE_DATABASE_URL")
# For security, set a shared internal API key between orchestrator and agents (optional)
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")
ENCRYPT_KEY = os.getenv("ENCRYPT_KEY")

JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)  # 2 hours
JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=1) # 3 days


