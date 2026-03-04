"""Tests for JWT auth — token creation, decoding, and expiry."""
import time

import jwt as pyjwt
import pytest

from src.auth.jwt_auth import (
    create_access_token, create_refresh_token, decode_token,
    SECRET_KEY, ALGORITHM,
)


class TestCreateAccessToken:
    def test_returns_string(self):
        token = create_access_token(1)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_contains_user_id(self):
        token = create_access_token(42)
        payload = decode_token(token)
        assert payload["sub"] == 42

    def test_type_is_access(self):
        token = create_access_token(1)
        payload = decode_token(token)
        assert payload["type"] == "access"

    def test_has_expiry(self):
        token = create_access_token(1)
        payload = decode_token(token)
        assert "exp" in payload
        assert payload["exp"] > time.time()

    def test_extra_claims(self):
        token = create_access_token(1, extra={"is_pro": True})
        payload = decode_token(token)
        assert payload["is_pro"] is True


class TestCreateRefreshToken:
    def test_returns_string(self):
        token = create_refresh_token(1)
        assert isinstance(token, str)

    def test_type_is_refresh(self):
        token = create_refresh_token(1)
        payload = decode_token(token)
        assert payload["type"] == "refresh"

    def test_longer_expiry_than_access(self):
        access = create_access_token(1)
        refresh = create_refresh_token(1)
        a_payload = decode_token(access)
        r_payload = decode_token(refresh)
        assert r_payload["exp"] > a_payload["exp"]


class TestDecodeToken:
    def test_decode_valid_token(self):
        token = create_access_token(99)
        payload = decode_token(token)
        assert payload["sub"] == 99

    def test_expired_token(self):
        # Create a token that's already expired
        now = int(time.time())
        payload = {"sub": "1", "type": "access", "iat": now - 7200, "exp": now - 3600}
        token = pyjwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        with pytest.raises(pyjwt.ExpiredSignatureError):
            decode_token(token)

    def test_invalid_token(self):
        with pytest.raises(Exception):
            decode_token("not.a.valid.token")

    def test_wrong_secret(self):
        payload = {"sub": "1", "type": "access", "iat": int(time.time()), "exp": int(time.time()) + 3600}
        token = pyjwt.encode(payload, "wrong-secret", algorithm=ALGORITHM)
        with pytest.raises(pyjwt.InvalidSignatureError):
            decode_token(token)
