"""Reepo Stripe billing — mock/stub implementation for Pro subscriptions."""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone

from src.db import _connect, DEFAULT_DB_PATH

PLANS = {
    "pro_monthly": {"name": "Pro Monthly", "price": 900, "interval": "month", "display_price": "$9/mo"},
    "pro_yearly": {"name": "Pro Yearly", "price": 7900, "interval": "year", "display_price": "$79/yr"},
}

PRICING_TIERS = {
    "free": {
        "name": "Free",
        "price": "$0",
        "features": [
            "Search and browse all repos",
            "View Reepo Scores",
            "Up to 3 collections",
            "100 API requests/day",
            "Community features",
        ],
    },
    "pro": {
        "name": "Pro",
        "price": "$9/mo or $79/yr",
        "features": [
            "Everything in Free",
            "Unlimited collections",
            "Comparison tool",
            "Export to JSON/CSV",
            "10,000 API requests/day",
            "No ads",
            "Priority support",
        ],
    },
}


def _is_stripe_configured() -> bool:
    return bool(os.environ.get("STRIPE_SECRET_KEY"))


def create_checkout_session(
    user_id: int,
    plan: str,
    success_url: str,
    cancel_url: str,
    path: str = DEFAULT_DB_PATH,
) -> str:
    """Create a Stripe checkout session. Returns checkout URL (mock if no Stripe key)."""
    if plan not in PLANS:
        raise ValueError(f"Invalid plan: {plan}. Choose from: {list(PLANS.keys())}")

    if _is_stripe_configured():
        import stripe
        stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": plan, "quantity": 1}],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"user_id": str(user_id)},
        )
        return session.url

    # Mock implementation
    session_id = uuid.uuid4().hex[:16]
    now = datetime.now(timezone.utc)
    if plan == "pro_yearly":
        period_end = now + timedelta(days=365)
    else:
        period_end = now + timedelta(days=30)

    conn = _connect(path)
    conn.execute(
        "INSERT OR REPLACE INTO subscriptions "
        "(user_id, stripe_customer_id, stripe_subscription_id, plan, status, "
        "current_period_start, current_period_end, updated_at) "
        "VALUES (?, ?, ?, ?, 'active', ?, ?, ?)",
        (
            user_id,
            f"cus_mock_{user_id}",
            f"sub_mock_{session_id}",
            plan,
            now.isoformat(),
            period_end.isoformat(),
            now.isoformat(),
        ),
    )
    conn.commit()
    conn.close()
    return f"{success_url}?session_id=mock_{session_id}"


def handle_webhook(
    payload: bytes, sig_header: str, webhook_secret: str, path: str = DEFAULT_DB_PATH
) -> dict:
    """Process a Stripe webhook event. Returns event type and status."""
    if _is_stripe_configured():
        import stripe
        stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        event_type = event["type"]
        if event_type == "checkout.session.completed":
            session = event["data"]["object"]
            user_id = int(session["metadata"]["user_id"])
            _activate_subscription(user_id, session, path)
        elif event_type == "customer.subscription.deleted":
            sub = event["data"]["object"]
            _cancel_subscription_by_stripe_id(sub["id"], path)
        return {"event_type": event_type, "status": "processed"}

    # Mock: just return success
    return {"event_type": "mock_event", "status": "processed"}


def get_subscription_status(user_id: int, path: str = DEFAULT_DB_PATH) -> dict:
    """Get the current subscription status for a user."""
    conn = _connect(path)
    row = conn.execute(
        "SELECT * FROM subscriptions WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    conn.close()

    if not row:
        return {"plan": "free", "status": "active", "is_pro": False}

    sub = dict(row)
    now = datetime.now(timezone.utc).isoformat()
    is_active = sub["status"] == "active" and (
        sub["current_period_end"] is None or sub["current_period_end"] > now
    )
    return {
        "plan": sub["plan"],
        "status": sub["status"],
        "is_pro": is_active and sub["plan"] in PLANS,
        "current_period_start": sub["current_period_start"],
        "current_period_end": sub["current_period_end"],
        "stripe_subscription_id": sub["stripe_subscription_id"],
    }


def cancel_subscription(user_id: int, path: str = DEFAULT_DB_PATH) -> bool:
    """Cancel a user's subscription. Returns True if cancelled."""
    conn = _connect(path)
    cur = conn.execute(
        "UPDATE subscriptions SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP "
        "WHERE user_id = ? AND status = 'active'",
        (user_id,),
    )
    changed = cur.rowcount > 0
    conn.commit()
    conn.close()

    if _is_stripe_configured() and changed:
        sub_status = get_subscription_status(user_id, path)
        if sub_status.get("stripe_subscription_id"):
            import stripe
            stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
            stripe.Subscription.delete(sub_status["stripe_subscription_id"])

    return changed


def _activate_subscription(user_id: int, session: dict, path: str) -> None:
    """Activate a subscription from a checkout session."""
    conn = _connect(path)
    conn.execute(
        "INSERT OR REPLACE INTO subscriptions "
        "(user_id, stripe_customer_id, stripe_subscription_id, plan, status, "
        "current_period_start, current_period_end, updated_at) "
        "VALUES (?, ?, ?, 'pro_monthly', 'active', ?, ?, ?)",
        (
            user_id,
            session.get("customer"),
            session.get("subscription"),
            datetime.now(timezone.utc).isoformat(),
            (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    conn.close()


def _cancel_subscription_by_stripe_id(stripe_sub_id: str, path: str) -> None:
    """Cancel a subscription by Stripe subscription ID."""
    conn = _connect(path)
    conn.execute(
        "UPDATE subscriptions SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP "
        "WHERE stripe_subscription_id = ?",
        (stripe_sub_id,),
    )
    conn.commit()
    conn.close()
