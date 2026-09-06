"""
Model 3 Federation Secrets Governance: AES-256-GCM Cryptographic Vault.
Encrypts and decrypts external VMS credentials (passwords, tokens, ONVIF secrets) at rest.
Compliant with Ponytail Rule 5: Model 3 Federation & Secrets Governance.
"""
import os
import base64
from typing import Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# 256-bit key (32 bytes) derived from platform master secret or environment variable
_RAW_KEY = os.environ.get("VMS_VAULT_AES_KEY", "GUJARAT-CCTV-FEDERATION-256BIT-AES-KEY-2026").encode("utf-8")
MASTER_KEY = _RAW_KEY[:32].ljust(32, b"0")

def encrypt_vms_secret(plaintext: Optional[str]) -> str:
    """
    Encrypt an external VMS credential, token, or secret using AES-256-GCM.
    Returns ciphertext prefixed with 'aes-gcm:' for safe storage at rest.
    """
    if not plaintext:
        return ""
    if plaintext.startswith("aes-gcm:"):
        return plaintext  # Already encrypted

    aesgcm = AESGCM(MASTER_KEY)
    nonce = os.urandom(12)  # Standard 96-bit nonce for AES-GCM
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    encoded = base64.b64encode(nonce + ciphertext).decode("utf-8")
    return f"aes-gcm:{encoded}"

def decrypt_vms_secret(encrypted_token: Optional[str]) -> str:
    """
    Decrypt an AES-256-GCM credential token back to plaintext.
    """
    if not encrypted_token:
        return ""
    if not encrypted_token.startswith("aes-gcm:"):
        return encrypted_token

    raw_b64 = encrypted_token[len("aes-gcm:"):]
    data = base64.b64decode(raw_b64.encode("utf-8"))
    nonce = data[:12]
    ciphertext = data[12:]
    aesgcm = AESGCM(MASTER_KEY)
    plaintext_bytes = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext_bytes.decode("utf-8")
