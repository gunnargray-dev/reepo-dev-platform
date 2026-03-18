"""Reepo JWT auth — token creation and verification using PyJWT."""
import os
import time

import jwt

SECRET_KEY = os.environ.get("REEPO_JWT_SECRET", "reepo-dev-secret-change-in-production")
SUPABASE_JWT_SECRET = os.environ.get(
    "SUPABASE_JWT_SECRET",
    "super-secret-jwt-token-with-at-least-32-characters-long",
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE = 3600       # 1 hour
REFRESH_TOKEN_EXPIRE = 86400 * 30  # 30 days


def create_access_token(user_id: int, extra: dict | None = None) -> str:
    """Create a short-lived JWT access token."""
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": now,
        "exp": now + ACCESS_TOKEN_EXPIRE,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    """Create a long-lived JWT refresh token."""
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": now,
        "exp": now + REFRESH_TOKEN_EXPIRE,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and verify a Supabase JWT token. Raises jwt.ExpiredSignatureError or jwt.InvalidTokenError."""
    data = jwt.decode(
        token,
        SUPABASE_JWT_SECRET,
        algorithms=[ALGORITHM],
        options={"verify_aud": False},
    )
    return data
