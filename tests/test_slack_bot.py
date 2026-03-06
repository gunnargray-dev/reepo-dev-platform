"""Tests for Slack bot — signature verification and slash command handling."""
import hashlib
import hmac
import os
import tempfile
import time

import pytest

from src.db import init_db, insert_repo
from src.search import init_fts
from src.trending import init_trending_tables
from src.bots.slack_bot import verify_slack_signature, handle_slash_command


FAKE_SECRET = "test_slack_signing_secret_12345"


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


def _make_signature(body: bytes, timestamp: str, secret: str = FAKE_SECRET) -> str:
    """Create a valid Slack signature for the given body and timestamp."""
    sig_basestring = f"v0:{timestamp}:{body.decode('utf-8', errors='replace')}"
    return "v0=" + hmac.new(
        secret.encode("utf-8"),
        sig_basestring.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


# --- verify_slack_signature ---

class TestVerifySlackSignature:
    def test_valid_signature(self):
        body = b"text=search+ai"
        ts = str(int(time.time()))
        sig = _make_signature(body, ts)
        assert verify_slack_signature(body, ts, sig, signing_secret=FAKE_SECRET) is True

    def test_invalid_signature(self):
        body = b"text=search+ai"
        ts = str(int(time.time()))
        assert verify_slack_signature(body, ts, "v0=bad", signing_secret=FAKE_SECRET) is False

    def test_expired_timestamp(self):
        body = b"text=search+ai"
        ts = str(int(time.time()) - 600)  # 10 minutes ago
        sig = _make_signature(body, ts)
        assert verify_slack_signature(body, ts, sig, signing_secret=FAKE_SECRET) is False

    def test_empty_secret(self):
        body = b"text=search+ai"
        ts = str(int(time.time()))
        sig = _make_signature(body, ts)
        assert verify_slack_signature(body, ts, sig, signing_secret="") is False

    def test_none_secret(self):
        body = b"text=test"
        ts = str(int(time.time()))
        assert verify_slack_signature(body, ts, "v0=abc", signing_secret=None) is False

    def test_bad_timestamp(self):
        body = b"text=test"
        assert verify_slack_signature(body, "notanumber", "v0=abc", signing_secret=FAKE_SECRET) is False

    def test_empty_timestamp(self):
        body = b"text=test"
        assert verify_slack_signature(body, "", "v0=abc", signing_secret=FAKE_SECRET) is False

    def test_tampered_body(self):
        body = b"text=search+ai"
        ts = str(int(time.time()))
        sig = _make_signature(body, ts)
        # Tamper with the body
        assert verify_slack_signature(b"text=search+hacked", ts, sig, signing_secret=FAKE_SECRET) is False

    def test_different_secret(self):
        body = b"text=search+ai"
        ts = str(int(time.time()))
        sig = _make_signature(body, ts, secret="correct_secret")
        assert verify_slack_signature(body, ts, sig, signing_secret="wrong_secret") is False


# --- handle_slash_command ---

class TestHandleSlashCommand:
    def test_search_command(self, db_path):
        result = handle_slash_command({"text": "search AI"}, db_path)
        assert result["response_type"] == "in_channel"
        assert len(result["blocks"]) > 0

    def test_help_command(self, db_path):
        result = handle_slash_command({"text": "help"}, db_path)
        assert result["response_type"] == "in_channel"

    def test_empty_text(self, db_path):
        result = handle_slash_command({"text": ""}, db_path)
        assert result["response_type"] == "in_channel"

    def test_no_text_key(self, db_path):
        result = handle_slash_command({}, db_path)
        assert result["response_type"] == "in_channel"

    def test_info_command(self, db_path):
        result = handle_slash_command({"text": "info org1/repo1"}, db_path)
        assert result["response_type"] == "in_channel"
        assert any("org1/repo1" in str(b) for b in result["blocks"])

    def test_categories_command(self, db_path):
        result = handle_slash_command({"text": "categories"}, db_path)
        assert result["response_type"] == "in_channel"
