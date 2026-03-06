"""Reepo API — Discord integration endpoints."""
from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/api/integrations/discord", tags=["discord"])


@router.post("/interactions")
async def discord_interactions(request: Request):
    """Handle Discord interaction webhooks (PING + slash commands)."""
    from src.server import get_db_path
    from src.bots.discord_bot import verify_discord_signature, handle_interaction, DISCORD_PUBLIC_KEY

    body = await request.body()
    timestamp = request.headers.get("X-Signature-Timestamp", "")
    signature = request.headers.get("X-Signature-Ed25519", "")

    # Skip verification if no public key configured (development mode)
    if DISCORD_PUBLIC_KEY and not verify_discord_signature(body, timestamp, signature):
        raise HTTPException(status_code=401, detail="Invalid Discord signature")

    import json
    try:
        interaction = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    result = handle_interaction(interaction, db_path=get_db_path())
    return result
