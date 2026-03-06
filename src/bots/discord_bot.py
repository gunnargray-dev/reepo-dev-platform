"""Reepo Discord bot — signature verification stub and interaction handling."""
import os


DISCORD_PUBLIC_KEY = os.environ.get("DISCORD_PUBLIC_KEY", "")


def verify_discord_signature(
    body: bytes,
    timestamp: str,
    signature: str,
    public_key: str | None = None,
) -> bool:
    """Verify Discord interaction signature using Ed25519 (stub).

    In production, this would use a library like PyNaCl to verify Ed25519
    signatures. For now, returns True if a public key is configured and the
    signature is non-empty.

    Args:
        body: Raw request body bytes
        timestamp: X-Signature-Timestamp header value
        signature: X-Signature-Ed25519 header value
        public_key: Override for testing; defaults to env var
    """
    key = public_key or DISCORD_PUBLIC_KEY
    if not key or not signature or not timestamp:
        return False

    # Stub: in production, verify Ed25519 signature with PyNaCl
    # from nacl.signing import VerifyKey
    # verify_key = VerifyKey(bytes.fromhex(key))
    # verify_key.verify(timestamp.encode() + body, bytes.fromhex(signature))
    try:
        # Basic sanity: signature should be hex-decodable
        bytes.fromhex(signature)
        return True
    except (ValueError, TypeError):
        return False


def handle_interaction(interaction: dict, db_path: str) -> dict:
    """Handle a Discord interaction payload.

    interaction type 1 = PING → respond with PONG (type 1)
    interaction type 2 = APPLICATION_COMMAND → handle slash command
    """
    interaction_type = interaction.get("type")

    # PING → PONG
    if interaction_type == 1:
        return {"type": 1}

    # APPLICATION_COMMAND
    if interaction_type == 2:
        from src.bots.core import parse_command, execute_command, format_discord_response

        data = interaction.get("data", {})
        command_name = data.get("name", "")
        options = data.get("options", [])

        # Build command text from interaction data
        if command_name == "reepo" and options:
            subcommand = options[0].get("name", "")
            sub_options = options[0].get("options", [])
            args_parts = []
            for opt in sub_options:
                args_parts.append(str(opt.get("value", "")))
            text = f"{subcommand} {' '.join(args_parts)}".strip()
        else:
            text = command_name

        parsed = parse_command(text)
        result = execute_command(parsed, db_path=db_path)
        return format_discord_response(result)

    # Unknown interaction type
    return {"type": 4, "data": {"content": "Unknown interaction type."}}
