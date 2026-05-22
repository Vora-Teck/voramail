import re
import random
from datetime import datetime
import string
import html
from werkzeug.utils import secure_filename
from root import config
import os
import ipaddress
from urllib.parse import urlparse


# ===== FILE VALIDATION ============
def allowed_file(filename):
    return (
        "." in filename and filename.rsplit(".", 1)[1].lower() in config.ALLOWED_EXTENSIONS
    )

def save_uploaded_file(file, category):
    filename = secure_filename(file.filename)
    folder = config.UPLOAD_FOLDERS.get(category)
    if not folder:
        raise ValueError("Invalid upload category")
    file_path = os.path.join(folder, filename)
    file.save(file_path)
    return filename

def validate_attachments(files):
    total_size = 0
    validated_files = []
    for file in files:
        if not file:
            continue
        filename = secure_filename(file.filename)
        if filename == "":
            raise ValueError("Invalid filename")
        mime_type = file.mimetype
        if mime_type not in config.ALLOWED_MIME_TYPES:
            raise ValueError(
                f"Unsupported MIME type: {mime_type}"
            )
        file_bytes = file.read()
        file_size = len(file_bytes)
        # Reset stream pointer if needed later
        file.seek(0)
        if file_size > config.MAX_SINGLE_FILE_SIZE:
            raise ValueError(
                f"{filename} exceeds max size of 5MB"
            )
        total_size += file_size
        if total_size > config.MAX_TOTAL_ATTACHMENT_SIZE:
            raise ValueError(
                "Total attachment size exceeds 10MB"
            )
        validated_files.append({
            "filename": filename,
            "mime_type": mime_type,
            "data": file_bytes
        })

    return validated_files


# ===== FORM VALIDATION ============
def clean_form(data):
    """
    Recursively clean form data:
    - Escape HTML in strings
    - Leave ints, floats, bools unchanged
    - Recursively clean dicts, lists, tuples
    """
    # If it's a string, escape HTML & special characters
    if isinstance(data, str):
        return html.escape(data)
    # If it's a dictionary, clean each key/value
    if isinstance(data, dict):
        return {key: clean_form(value) for key, value in data.items()}
    # If it's a list, clean each item
    if isinstance(data, list):
        return [clean_form(item) for item in data]

    # If it's a tuple, clean each item and return tuple
    if isinstance(data, tuple):
        return tuple(clean_form(item) for item in data)
    # If it's another data type (int, float, bool, None, etc.)
    return data

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if re.match(pattern, email):
        return True
    else:
        return False

def is_valid_phone_number(phone):
    pattern = r'^0[789][01]\d{8}$'
    if re.match(pattern, phone):
        return True
    else:
        return False

def is_valid_password(password):
    if len(password) < 8:
        return False
    if not re.search(r'[a-zA-Z]', password) or not re.search(r'\d', password):
        return False
    return True

def is_valid_url(url: str) -> bool:
    URL_REGEX = re.compile(
        r'^(https?:\/\/)'
        r'(([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}'
        r"|"
        r'localhost)'
        r'(:\d{1,5})?'
        r'(\/[^\s]*)?$'
    )
    if not isinstance(url, str):
        return False
    return bool(URL_REGEX.match(url.strip()))

def is_valid_ip(ip: str) -> bool:
    if not isinstance(ip, str):
        return False
    try:
        ipaddress.ip_address(ip.strip())
        return True
    except Exception:
        return False

def is_valid_ipv4(ip: str) -> bool:
    if not isinstance(ip, str):
        return False
    try:
        ipaddress.IPv4Address(ip.strip())
        return True
    except Exception:
        return False

def validate_smtp_host(host: str) -> bool:
    """
    Validate SMTP host/domain.

    Examples of valid hosts:
    - smtp.gmail.com
    - mail.example.org
    - localhost
    - 127.0.0.1
    """

    if not host:
        return False

    host = host.strip().lower()

    # Remove protocol if mistakenly included
    parsed = urlparse(host)

    if parsed.scheme:
        host = parsed.netloc

    # Remove port if included
    if ":" in host:
        host = host.split(":")[0]

    # DOMAIN REGEX
    domain_pattern = re.compile(
        r"^(?:"
        r"localhost|"
        r"(?:(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,})|"
        r"(?:\d{1,3}\.){3}\d{1,3}"
        r")$"
    )

    return bool(
        domain_pattern.match(host)
    )

# ===== STRING MANIPULATION ============
def generate(n):
    chars = string.ascii_uppercase + string.digits
    random_combination = ''.join(random.choice(chars) for _ in range(n))
    return random_combination

def generate_lower(n):
    chars = string.ascii_lowercase + string.digits
    random_combination = ''.join(random.choice(chars) for _ in range(n))
    return random_combination

def slugify(s):
    s = s.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_-]+', '-', s)
    s = re.sub(r'^-+|-+$', '', s)
    return s

def generateCode(n):
    key = ''
    for i in range(n):
        rand_char = random.choice("1234567890")
        key += rand_char
    return key

def generateReference(prefix=None, extra=3):
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_part = ''.join(random.choices(string.digits, k=extra))
    return f"{prefix + '-' if prefix else ''}{timestamp}{random_part}"

