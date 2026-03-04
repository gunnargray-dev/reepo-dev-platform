"""Reepo GitHub OAuth — authorization URL, code exchange, user fetch."""
import os
import urllib.parse

# These can be overridden in tests via monkeypatch or direct assignment
CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "")
REDIRECT_URI = os.environ.get("GITHUB_REDIRECT_URI", "https://reepo.dev/api/auth/github/callback")

# Pluggable HTTP fetcher for testability — default uses urllib
_http_get = None
_http_post = None


def _default_post(url: str, data: dict, headers: dict | None = None) -> dict:
    """POST with urllib and return parsed JSON."""
    import json
    import urllib.request
    encoded = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=encoded, headers=headers or {})
    req.add_header("Accept", "application/json")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def _default_get(url: str, headers: dict | None = None) -> dict:
    """GET with urllib and return parsed JSON."""
    import json
    import urllib.request
    req = urllib.request.Request(url, headers=headers or {})
    req.add_header("Accept", "application/json")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def get_auth_url(state: str | None = None) -> str:
    """Build GitHub OAuth authorization URL."""
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "read:user user:email",
    }
    if state:
        params["state"] = state
    return f"https://github.com/login/oauth/authorize?{urllib.parse.urlencode(params)}"


def exchange_code(code: str) -> dict:
    """Exchange authorization code for access token."""
    post_fn = _http_post or _default_post
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    result = post_fn(
        "https://github.com/login/oauth/access_token",
        data=data,
        headers={"Accept": "application/json"},
    )
    if "error" in result:
        raise ValueError(result.get("error_description", result["error"]))
    return result


def get_github_user(access_token: str) -> dict:
    """Fetch authenticated GitHub user profile."""
    get_fn = _http_get or _default_get
    return get_fn(
        "https://api.github.com/user",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        },
    )
