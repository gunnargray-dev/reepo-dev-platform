"""Reepo API — billing routes for Stripe integration."""
from __future__ import annotations

from fastapi import APIRouter, Query, Request, HTTPException

from src.monetization.stripe_billing import PRICING_TIERS

router = APIRouter()


@router.post("/api/billing/checkout")
def create_checkout(
    plan: str = Query(..., description="Plan: pro_monthly or pro_yearly"),
    user_id: int = Query(..., description="User ID"),
    success_url: str = Query("https://reepo.dev/billing/success", description="Success redirect URL"),
    cancel_url: str = Query("https://reepo.dev/billing/cancel", description="Cancel redirect URL"),
):
    from src.server import get_db_path
    from src.monetization.stripe_billing import create_checkout_session

    db_path = get_db_path()
    try:
        url = create_checkout_session(user_id, plan, success_url, cancel_url, path=db_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"checkout_url": url}


@router.post("/api/billing/webhook")
async def stripe_webhook(request: Request):
    from src.server import get_db_path
    from src.monetization.stripe_billing import handle_webhook
    import os

    db_path = get_db_path()
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    result = handle_webhook(payload, sig_header, webhook_secret, path=db_path)
    return result


@router.get("/api/billing/subscription")
def get_subscription(user_id: int = Query(..., description="User ID")):
    from src.server import get_db_path
    from src.monetization.stripe_billing import get_subscription_status

    db_path = get_db_path()
    return get_subscription_status(user_id, path=db_path)


@router.post("/api/billing/cancel")
def cancel_sub(user_id: int = Query(..., description="User ID")):
    from src.server import get_db_path
    from src.monetization.stripe_billing import cancel_subscription

    db_path = get_db_path()
    cancelled = cancel_subscription(user_id, path=db_path)
    if not cancelled:
        raise HTTPException(status_code=404, detail="No active subscription found")
    return {"status": "cancelled"}


@router.get("/api/pricing")
def get_pricing():
    return {"tiers": PRICING_TIERS}
