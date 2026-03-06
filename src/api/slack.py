"""Reepo API — Slack integration endpoints."""
from fastapi import APIRouter, HTTPException, Request, Response

router = APIRouter(prefix="/api/integrations/slack", tags=["slack"])


@router.post("/commands")
async def slack_slash_command(request: Request):
    """Handle Slack slash commands (/reepo)."""
    from src.server import get_db_path
    from src.bots.slack_bot import verify_slack_signature, handle_slash_command, SLACK_SIGNING_SECRET

    body = await request.body()
    timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
    signature = request.headers.get("X-Slack-Signature", "")

    # Skip verification if no signing secret configured (development mode)
    if SLACK_SIGNING_SECRET and not verify_slack_signature(body, timestamp, signature):
        raise HTTPException(status_code=401, detail="Invalid Slack signature")

    # Parse form-encoded body
    form = await request.form()
    payload = dict(form)

    result = handle_slash_command(payload, db_path=get_db_path())
    return result


@router.post("/events")
async def slack_events(request: Request):
    """Handle Slack Events API (url_verification + app_mention)."""
    from src.server import get_db_path
    from src.bots.slack_bot import verify_slack_signature, SLACK_SIGNING_SECRET
    from src.bots.core import parse_command, execute_command, format_slack_response

    body = await request.body()
    timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
    signature = request.headers.get("X-Slack-Signature", "")

    if SLACK_SIGNING_SECRET and not verify_slack_signature(body, timestamp, signature):
        raise HTTPException(status_code=401, detail="Invalid Slack signature")

    import json
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # URL verification challenge
    if data.get("type") == "url_verification":
        return {"challenge": data.get("challenge", "")}

    # Event callback
    if data.get("type") == "event_callback":
        event = data.get("event", {})
        if event.get("type") == "app_mention":
            text = event.get("text", "")
            # Strip the bot mention (<@BOTID> /reepo ...)
            import re
            text = re.sub(r"<@\w+>\s*", "", text).strip()
            parsed = parse_command(text)
            result = execute_command(parsed, db_path=get_db_path())
            return format_slack_response(result)

    return {"ok": True}
