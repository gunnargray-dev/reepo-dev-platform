"""Tests for Discord bot — signature verification and interaction handling."""
import os
import tempfile

import pytest

from src.db import init_db, insert_repo
from src.search import init_fts
from src.trending import init_trending_tables
from src.bots.discord_bot import verify_discord_signature, handle_interaction


FAKE_PUBLIC_KEY = "a" * 64  # 32-byte hex-encoded key


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


# --- verify_discord_signature ---

class TestVerifyDiscordSignature:
    def test_valid_signature(self):
        sig = "ab" * 32  # Valid hex string
        assert verify_discord_signature(b"body", "12345", sig, public_key=FAKE_PUBLIC_KEY) is True

    def test_empty_key(self):
        assert verify_discord_signature(b"body", "12345", "ab" * 32, public_key="") is False

    def test_none_key(self):
        assert verify_discord_signature(b"body", "12345", "ab" * 32, public_key=None) is False

    def test_empty_signature(self):
        assert verify_discord_signature(b"body", "12345", "", public_key=FAKE_PUBLIC_KEY) is False

    def test_empty_timestamp(self):
        assert verify_discord_signature(b"body", "", "ab" * 32, public_key=FAKE_PUBLIC_KEY) is False

    def test_invalid_hex_signature(self):
        assert verify_discord_signature(b"body", "12345", "not-hex!!", public_key=FAKE_PUBLIC_KEY) is False

    def test_no_key_configured(self):
        # With default env var (empty)
        assert verify_discord_signature(b"body", "12345", "ab" * 32) is False


# --- handle_interaction ---

class TestHandleInteraction:
    def test_ping_pong(self, db_path):
        result = handle_interaction({"type": 1}, db_path)
        assert result == {"type": 1}

    def test_application_command_search(self, db_path):
        interaction = {
            "type": 2,
            "data": {
                "name": "reepo",
                "options": [{
                    "name": "search",
                    "options": [{"name": "query", "value": "AI"}],
                }],
            },
        }
        result = handle_interaction(interaction, db_path)
        assert result["type"] == 4
        assert "data" in result
        assert len(result["data"]["embeds"]) > 0

    def test_application_command_help(self, db_path):
        interaction = {
            "type": 2,
            "data": {
                "name": "reepo",
                "options": [{"name": "help", "options": []}],
            },
        }
        result = handle_interaction(interaction, db_path)
        assert result["type"] == 4

    def test_application_command_info(self, db_path):
        interaction = {
            "type": 2,
            "data": {
                "name": "reepo",
                "options": [{
                    "name": "info",
                    "options": [{"name": "repo", "value": "org1/repo1"}],
                }],
            },
        }
        result = handle_interaction(interaction, db_path)
        assert result["type"] == 4

    def test_application_command_trending(self, db_path):
        interaction = {
            "type": 2,
            "data": {
                "name": "reepo",
                "options": [{"name": "trending", "options": []}],
            },
        }
        result = handle_interaction(interaction, db_path)
        assert result["type"] == 4

    def test_non_reepo_command(self, db_path):
        interaction = {
            "type": 2,
            "data": {"name": "other_command", "options": []},
        }
        result = handle_interaction(interaction, db_path)
        assert result["type"] == 4

    def test_unknown_interaction_type(self, db_path):
        result = handle_interaction({"type": 99}, db_path)
        assert result["type"] == 4
        assert "Unknown" in result["data"]["content"]

    def test_empty_interaction(self, db_path):
        result = handle_interaction({}, db_path)
        assert result["type"] == 4

    def test_command_with_no_options(self, db_path):
        interaction = {
            "type": 2,
            "data": {"name": "reepo", "options": []},
        }
        result = handle_interaction(interaction, db_path)
        assert result["type"] == 4
