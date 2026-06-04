# app/security/encryption.py
import base64
import hashlib
from cryptography.fernet import Fernet
from root.config import ENCRYPT_KEY
import json


def _derive_fernet_key(api_key: str) -> bytes:
    """
    Convert user-provided API key into a valid Fernet key (32-byte base64 URL-safe).
    AES-256 key derived using SHA256.
    """
    sha = hashlib.sha256(api_key.encode()).digest()
    return base64.urlsafe_b64encode(sha)


def encrypt_payload(data: dict, api_key: str) -> str:
    """
    Encrypt JSON-serializable data using the API key.
    Returns encrypted string.
    """

    fernet_key = _derive_fernet_key(api_key)
    f = Fernet(fernet_key)
    payload = json.dumps(data).encode()
    token = f.encrypt(payload)

    return token.decode()


def encrypt(data):
    fernet_key = _derive_fernet_key(ENCRYPT_KEY)
    f = Fernet(fernet_key)
    payload = data.encode()
    token = f.encrypt(payload)
    return token.decode()


def decrypt(token):
    fernet_key = _derive_fernet_key(ENCRYPT_KEY)
    f = Fernet(fernet_key)
    decrypted = f.decrypt(token.encode())
    return decrypted.decode()


def decrypt_payload(token: str, api_key: str) -> dict:
    """
    Decrypt encrypted payload using the API key.
    Returns Python dictionary.
    """

    fernet_key = _derive_fernet_key(api_key)
    f = Fernet(fernet_key)
    decrypted = f.decrypt(token.encode())
    return json.loads(decrypted.decode())
