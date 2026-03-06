"""Reepo Slack bot — signature verification and slash command handling."""
import hashlib
import hmac
import os
import time


SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET", "")


def verify_slack_signature(
    body: bytes,
    timestamp: str,
    signature: str,
    signing_secret: str | None = None,
) -> bool:
    """Verify Slack request signature using HMAC-SHA256.

    Args:
        body: Raw request body bytes
        timestamp: X-Slack-Request-Timestamp header value
        signature: X-Slack-Signature header value (v0=...)
        signing_secret: Override for testing; defaults to env var
    """
    secret = signing_secret or SLACK_SIGNING_SECRET
    if not secret:
        return False

    # Reject requests older than 5 minutes to prevent replay attacks
    try:
        ts = int(timestamp)
    except (ValueError, TypeError):
        return False

    if abs(time.time() - ts) > 300:
        return False

    sig_basestring = f"v0:{timestamp}:{body.decode('utf-8', errors='replace')}"
    computed = "v0=" + hmac.new(
        secret.encode("utf-8"),
        sig_basestring.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(computed, signature)


def handle_slash_command(payload: dict, db_path: str) -> dict:
    """Handle a Slack slash command payload and return a Slack response.

    payload keys: command, text, user_id, channel_id, etc.
    """
    from src.bots.core import parse_command, execute_command, format_slack_response

    text = payload.get("text", "")
    parsed = parse_command(text)
    result = execute_command(parsed, db_path=db_path)
    return format_slack_response(result)
