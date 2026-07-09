import hashlib
import hmac
import json
import time
import base64
from datetime import datetime
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from django.conf import settings
import secrets


SECRET_KEY = getattr(settings, 'API_SECRET_KEY', getattr(settings, 'API_SHARED_SECRET', settings.SECRET_KEY))
SIGNATURE_TIMEOUT = 300

def generate_signature(data: dict, secret_key: str = SECRET_KEY) -> str:
    sorted_data = sorted(data.items())
    sign_str = '&'.join([f'{k}={v}' for k, v in sorted_data if v is not None])
    signature = hmac.new(
        secret_key.encode('utf-8'),
        sign_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature


def verify_signature(data: dict, signature: str, secret_key: str = SECRET_KEY) -> bool:
    expected = generate_signature(data, secret_key)
    return hmac.compare_digest(expected, signature)

def generate_nonce(length: int = 16) -> str:
    return secrets.token_hex(length)


def verify_timestamp(timestamp: int, timeout: int = SIGNATURE_TIMEOUT) -> bool:
    current = int(time.time())
    return abs(current - timestamp) <= timeout


def generate_rsa_key_pair():
    key = RSA.generate(2048)
    private_key = key.export_key().decode('utf-8')
    public_key = key.publickey().export_key().decode('utf-8')
    return private_key, public_key


def rsa_sign(data: str, private_key: str) -> str:
    key = RSA.import_key(private_key)
    h = SHA256.new(data.encode('utf-8'))
    signature = pkcs1_15.new(key).sign(h)
    return base64.b64encode(signature).decode('utf-8')


def rsa_verify(data: str, signature: str, public_key: str) -> bool:
    try:
        key = RSA.import_key(public_key)
        h = SHA256.new(data.encode('utf-8'))
        pkcs1_15.new(key).verify(h, base64.b64decode(signature))
        return True
    except (ValueError, TypeError):
        return False