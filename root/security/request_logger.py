import logging
from datetime import datetime
from flask import request, g
import geoip2.database
from logging.handlers import RotatingFileHandler
from root import config

# Setup file logger
logger = logging.getLogger("request_logger")
logger.setLevel(logging.INFO)

file_handler = RotatingFileHandler(
    config.LOGGING_PATH,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | IP=%(ip)s | LOCATION=%(location)s | METHOD=%(method)s | PATH=%(path)s | USER=%(user)s"
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# GeoIP reader (load once)
geo_reader = geoip2.database.Reader(config.IP_DB_PATH)


def get_location_from_ip(ip):
    try:
        response = geo_reader.city(ip)
        country = response.country.name or "Unknown"
        city = response.city.name or "Unknown"
        return f"{city}, {country}"
    except Exception:
        return "Unknown"


def log_request_data():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    location = get_location_from_ip(ip)

    user = getattr(g, "current_user", None)
    user_id = user.id if user else "Anonymous"

    extra = {
        "ip": ip,
        "location": location,
        "method": request.method,
        "path": request.path,
        "user": user_id
    }

    logger.info("Request", extra=extra)





