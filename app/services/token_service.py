"""
Token Service — v3.0
=====================

Secure token generation and verification for:
  - Email verification
  - Password reset
  - Referral codes

All tokens are stored as SHA-256 hashes — the plain token is
sent only once (in the email/SMS) and never persisted.
"""

from __future__ import annotations

import hashlib
import secrets
import string
from datetime import datetime, timedelta

import pytz


def _utcnow() -> datetime:
    return datetime.now(pytz.utc)


# ── Token generation ──────────────────────────────────────────────────────

def generate_token(nbytes: int = 32) -> tuple[str, str]:
    """
    Generate a secure random URL-safe token and its SHA-256 hash.

    Returns:
        (plain_token, token_hash)
        - plain_token: send to user via email/SMS — NEVER store this
        - token_hash:  store in the database
    """
    plain   = secrets.token_urlsafe(nbytes)
    hashed  = hashlib.sha256(plain.encode('utf-8')).hexdigest()
    return plain, hashed


def hash_token(plain_token: str) -> str:
    """Compute the SHA-256 hash of a plain token for database lookup."""
    return hashlib.sha256(plain_token.encode('utf-8')).hexdigest()


def verify_token(plain_token: str, stored_hash: str) -> bool:
    """
    Constant-time comparison of a submitted token against its stored hash.
    Prevents timing attacks.
    """
    computed = hashlib.sha256(plain_token.encode('utf-8')).hexdigest()
    return secrets.compare_digest(computed, stored_hash)


def token_expiry(hours: int) -> datetime:
    """Return a UTC datetime ``hours`` from now."""
    return _utcnow() + timedelta(hours=hours)


# ── Referral code ─────────────────────────────────────────────────────────

def generate_referral_code(prefix: str = 'REF') -> str:
    """
    Generate a human-readable referral code.

    Format: <PREFIX>-XXXXXXXX  (uppercase alphanumeric, 8 chars)
    Example: REF-3FKZ8P2A
    """
    chars  = string.ascii_uppercase + string.digits
    suffix = ''.join(secrets.choice(chars) for _ in range(8))
    return f"{prefix}-{suffix}"


def generate_patient_code() -> str:
    """
    Generate an anonymised patient ID.

    Format: LW-XXXXXXXX
    Example: LW-9ZBA12KF
    """
    return generate_referral_code(prefix='LW')
