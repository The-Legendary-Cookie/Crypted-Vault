import os
import hashlib
import hmac

def generate_salt(size: int = 16) -> bytes:
    """Generate a random salt."""
    return os.urandom(size)

def generate_nonce(size: int = 12) -> bytes:
    """Generate a random nonce for AES-GCM."""
    return os.urandom(size)

def hash_data(data: bytes) -> str:
    """Return SHA256 hash of data as hex string."""
    return hashlib.sha256(data).hexdigest()

def hmac_sign(data: bytes, key: bytes) -> str:
    """Return HMAC-SHA256 signature of data using key as hex string."""
    return hmac.new(key, data, hashlib.sha256).hexdigest()
