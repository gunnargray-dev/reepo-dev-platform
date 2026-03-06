"""Tests for bot API endpoints — Slack commands/events and Discord interactions."""
import json
import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from src.db import init_db, insert_repo
from src.search import init_fts
from src.trending import init_trending_tables
from src.server import create_app


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    init_fts(path)
    init_trending_tables(path)
    insert_repo({
        "github_id": 1, "owner": "org1", "name": "repo1",
        "full_name": "org1/repo1", "description": "An AI framework",
        "stars": 5000, "language": "Python", "category_primary": "frameworks",
        "reepo_score": 85, "url": "https://github.com/org1/repo1",
    }, path)
    init_fts(path)
    yield path
    os.unlink(path)


@pytest.fixture
def client(db_path):
    app = create_app(db_path=db_path)
    return TestClient(app)


# --- Slack /commands ---

class TestSlackCommands:
    def test_search_command(self, client):
        resp = client.post(
            "/api/integrations/slack/commands",
            data={"command": "/reepo", "text": "search AI"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["response_type"] == "in_channel"
        assert len(body["blocks"]) > 0

    def test_help_command(self, client):
        resp = client.post(
            "/api/integrations/slack/commands",
            data={"command": "/reepo", "text": "help"},
        )
        assert resp.status_code == 200
        assert resp.json()["response_type"] == "in_channel"

    def test_info_command(self, client):
        resp = client.post(
            "/api/integrations/slack/commands",
            data={"command": "/reepo", "text": "info org1/repo1"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert any("org1/repo1" in str(b) for b in body["blocks"])

    def test_empty_text(self, client):
        resp = client.post(
            "/api/integrations/slack/commands",
            data={"command": "/reepo", "text": ""},
        )
        assert resp.status_code == 200

    def test_categories_command(self, client):
        resp = client.post(
            "/api/integrations/slack/commands",
            data={"command": "/reepo", "text": "categories"},
        )
        assert resp.status_code == 200

    def test_trending_command(self, client):
        resp = client.post(
            "/api/integrations/slack/commands",
            data={"command": "/reepo", "text": "trending"},
        )
        assert resp.status_code == 200


# --- Slack /events ---

class TestSlackEvents:
    def test_url_verification(self, client):
        resp = client.post(
            "/api/integrations/slack/events",
            json={"type": "url_verification", "challenge": "test_challenge_token"},
        )
        assert resp.status_code == 200
        assert resp.json()["challenge"] == "test_challenge_token"

    def test_app_mention(self, client):
        resp = client.post(
            "/api/integrations/slack/events",
            json={
                "type": "event_callback",
                "event": {
                    "type": "app_mention",
                    "text": "<@U12345> search AI",
                },
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["response_type"] == "in_channel"

    def test_app_mention_with_reepo_prefix(self, client):
        resp = client.post(
            "/api/integrations/slack/events",
            json={
                "type": "event_callback",
                "event": {
                    "type": "app_mention",
                    "text": "<@U12345> /reepo help",
                },
            },
        )
        assert resp.status_code == 200

    def test_unknown_event_type(self, client):
        resp = client.post(
            "/api/integrations/slack/events",
            json={"type": "event_callback", "event": {"type": "message"}},
        )
        assert resp.status_code == 200
        assert resp.json() == {"ok": True}

    def test_invalid_json(self, client):
        resp = client.post(
            "/api/integrations/slack/events",
            content=b"not json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 400


# --- Discord /interactions ---

class TestDiscordInteractions:
    def test_ping(self, client):
        resp = client.post(
            "/api/integrations/discord/interactions",
            json={"type": 1},
        )
        assert resp.status_code == 200
        assert resp.json()["type"] == 1

    def test_slash_command_search(self, client):
        resp = client.post(
            "/api/integrations/discord/interactions",
            json={
                "type": 2,
                "data": {
                    "name": "reepo",
                    "options": [{
                        "name": "search",
                        "options": [{"name": "query", "value": "AI"}],
                    }],
                },
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["type"] == 4
        assert len(body["data"]["embeds"]) > 0

    def test_slash_command_help(self, client):
        resp = client.post(
            "/api/integrations/discord/interactions",
            json={
                "type": 2,
                "data": {
                    "name": "reepo",
                    "options": [{"name": "help", "options": []}],
                },
            },
        )
        assert resp.status_code == 200
        assert resp.json()["type"] == 4

    def test_slash_command_info(self, client):
        resp = client.post(
            "/api/integrations/discord/interactions",
            json={
                "type": 2,
                "data": {
                    "name": "reepo",
                    "options": [{
                        "name": "info",
                        "options": [{"name": "repo", "value": "org1/repo1"}],
                    }],
                },
            },
        )
        assert resp.status_code == 200

    def test_invalid_json(self, client):
        resp = client.post(
            "/api/integrations/discord/interactions",
            content=b"not json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 400

    def test_unknown_type(self, client):
        resp = client.post(
            "/api/integrations/discord/interactions",
            json={"type": 99},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["type"] == 4
