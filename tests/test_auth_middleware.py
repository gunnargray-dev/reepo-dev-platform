"""Tests for auth middleware — optional_auth, require_auth, require_pro."""
import os
import tempfile

import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from src.auth.jwt_auth import create_access_token
from src.auth.middleware import optional_auth, require_auth, require_pro


@pytest.fixture
def app():
    application = FastAPI()

    @application.get("/optional")
    def opt(payload=Depends(optional_auth)):
        return {"user": payload}

    @application.get("/required")
    def req(payload=Depends(require_auth)):
        return {"user_id": payload["sub"]}

    @application.get("/pro")
    def pro(payload=Depends(require_pro)):
        return {"user_id": payload["sub"]}

    return application


@pytest.fixture
def client(app):
    return TestClient(app)


class TestOptionalAuth:
    def test_no_token_returns_none(self, client):
        resp = client.get("/optional")
        assert resp.status_code == 200
        assert resp.json()["user"] is None

    def test_valid_token(self, client):
        token = create_access_token(42)
        resp = client.get("/optional", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["user"]["sub"] == 42

    def test_invalid_token_returns_none(self, client):
        resp = client.get("/optional", headers={"Authorization": "Bearer invalid.token"})
        assert resp.status_code == 200
        assert resp.json()["user"] is None


class TestRequireAuth:
    def test_no_token_returns_401(self, client):
        resp = client.get("/required")
        assert resp.status_code == 401

    def test_valid_token(self, client):
        token = create_access_token(42)
        resp = client.get("/required", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["user_id"] == 42

    def test_invalid_token_returns_401(self, client):
        resp = client.get("/required", headers={"Authorization": "Bearer bad.token"})
        assert resp.status_code == 401

    def test_missing_bearer_prefix(self, client):
        token = create_access_token(42)
        resp = client.get("/required", headers={"Authorization": token})
        assert resp.status_code == 401


class TestRequirePro:
    def test_no_token_returns_401(self, client):
        resp = client.get("/pro")
        assert resp.status_code == 401

    def test_non_pro_returns_403(self, client):
        token = create_access_token(42)
        resp = client.get("/pro", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_pro_user_succeeds(self, client):
        token = create_access_token(42, extra={"is_pro": True})
        resp = client.get("/pro", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["user_id"] == 42
