"""Reepo auth middleware — FastAPI dependencies for authentication."""
from fastapi import Depends, HTTPException, Request

from src.auth.jwt_auth import decode_token


def _extract_token(request: Request) -> str | None:
    """Extract bearer token from Authorization header."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return None


def optional_auth(request: Request) -> dict | None:
    """Return decoded token payload or None if no valid token."""
    token = _extract_token(request)
    if not token:
        return None
    try:
        return decode_token(token)
    except Exception:
        return None


def require_auth(request: Request) -> dict:
    """Require a valid JWT token. Raises 401 if missing or invalid."""
    token = _extract_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload


def require_pro(request: Request) -> dict:
    """Require a valid JWT token with pro status. Raises 401/403."""
    payload = require_auth(request)
    if not payload.get("is_pro"):
        raise HTTPException(status_code=403, detail="Pro subscription required")
    return payload
