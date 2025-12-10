import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from argon2 import PasswordHasher, Type
from argon2.low_level import hash_secret_raw, Type as ArgonType

# Constants
KDF_TIME_COST = 2
KDF_MEMORY_COST = 1024 * 64  # 64 MB
KDF_PARALLELISM = 2
KDF_HASH_LEN = 32
KDF_SALT_LEN = 16

def derive_key(password: str, salt: bytes) -> bytes:
    """
    Derive a 32-byte key from the password and salt using Argon2id.
    """
    if isinstance(password, str):
        password_bytes = password.encode('utf-8')
    else:
        password_bytes = password
        
    return hash_secret_raw(
        secret=password_bytes,
        salt=salt,
        time_cost=KDF_TIME_COST,
        memory_cost=KDF_MEMORY_COST,
        parallelism=KDF_PARALLELISM,
        hash_len=KDF_HASH_LEN,
        type=ArgonType.ID
    )

def encrypt(data: bytes, key: bytes) -> bytes:
    """
    Encrypt data using AES-256-GCM.
    Returns: nonce (12 bytes) + ciphertext + tag (16 bytes)
    """
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, data, None)
    # ciphertext already includes the tag at the end in cryptography library? 
    # Wait, AESGCM.encrypt returns ciphertext + tag.
    return nonce + ciphertext

def decrypt(data: bytes, key: bytes) -> bytes:
    """
    Decrypt data using AES-256-GCM.
    Expects: nonce (12 bytes) + ciphertext + tag
    """
    if len(data) < 12 + 16:
        raise ValueError("Data too short to contain nonce and tag")
    
    nonce = data[:12]
    ciphertext = data[12:]
    
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None)
