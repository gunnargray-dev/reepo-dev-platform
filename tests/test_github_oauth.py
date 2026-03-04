"""Tests for GitHub OAuth module — mock-friendly auth URL, code exchange, user fetch."""
import pytest

from src.auth import github_oauth


class TestGetAuthUrl:
    def test_contains_client_id(self):
        url = github_oauth.get_auth_url()
        assert "client_id=" in url
        assert "github.com/login/oauth/authorize" in url

    def test_contains_scope(self):
        url = github_oauth.get_auth_url()
        assert "scope=" in url

    def test_with_state(self):
        url = github_oauth.get_auth_url(state="abc123")
        assert "state=abc123" in url

    def test_without_state(self):
        url = github_oauth.get_auth_url()
        assert "state=" not in url


class TestExchangeCode:
    def test_exchange_code_success(self, monkeypatch):
        def mock_post(url, data, headers=None):
            return {"access_token": "gho_test123", "token_type": "bearer"}

        monkeypatch.setattr(github_oauth, "_http_post", mock_post)
        result = github_oauth.exchange_code("test_code")
        assert result["access_token"] == "gho_test123"

    def test_exchange_code_error(self, monkeypatch):
        def mock_post(url, data, headers=None):
            return {"error": "bad_verification_code", "error_description": "The code is invalid"}

        monkeypatch.setattr(github_oauth, "_http_post", mock_post)
        with pytest.raises(ValueError, match="The code is invalid"):
            github_oauth.exchange_code("bad_code")

    def test_exchange_code_error_no_description(self, monkeypatch):
        def mock_post(url, data, headers=None):
            return {"error": "bad_verification_code"}

        monkeypatch.setattr(github_oauth, "_http_post", mock_post)
        with pytest.raises(ValueError):
            github_oauth.exchange_code("bad_code")


class TestGetGithubUser:
    def test_get_user_success(self, monkeypatch):
        def mock_get(url, headers=None):
            return {
                "id": 12345, "login": "testuser",
                "name": "Test User", "email": "test@example.com",
                "avatar_url": "https://example.com/avatar.png",
                "bio": "Hello world",
            }

        monkeypatch.setattr(github_oauth, "_http_get", mock_get)
        user = github_oauth.get_github_user("gho_test123")
        assert user["id"] == 12345
        assert user["login"] == "testuser"

    def test_get_user_sends_auth_header(self, monkeypatch):
        captured_headers = {}

        def mock_get(url, headers=None):
            captured_headers.update(headers or {})
            return {"id": 1, "login": "x"}

        monkeypatch.setattr(github_oauth, "_http_get", mock_get)
        github_oauth.get_github_user("my_token")
        assert "Bearer my_token" in captured_headers.get("Authorization", "")
