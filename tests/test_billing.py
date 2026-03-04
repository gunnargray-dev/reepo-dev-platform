"""Tests for the Reepo Stripe billing — checkout flow, webhook handling, subscription status."""
import os
import tempfile

import pytest

from src.db import init_db
from src.monetization.db import init_monetization_db
from src.monetization.stripe_billing import (
    PLANS,
    PRICING_TIERS,
    create_checkout_session,
    handle_webhook,
    get_subscription_status,
    cancel_subscription,
)


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    init_monetization_db(path)
    yield path
    os.unlink(path)


class TestPlans:
    def test_plans_has_monthly(self):
        assert "pro_monthly" in PLANS
        assert PLANS["pro_monthly"]["price"] == 900

    def test_plans_has_yearly(self):
        assert "pro_yearly" in PLANS
        assert PLANS["pro_yearly"]["price"] == 7900

    def test_pricing_tiers_has_free_and_pro(self):
        assert "free" in PRICING_TIERS
        assert "pro" in PRICING_TIERS
        assert PRICING_TIERS["free"]["price"] == "$0"


class TestCreateCheckoutSession:
    def test_mock_monthly(self, db_path):
        url = create_checkout_session(
            user_id=1,
            plan="pro_monthly",
            success_url="https://reepo.dev/success",
            cancel_url="https://reepo.dev/cancel",
            path=db_path,
        )
        assert "success" in url
        assert "mock" in url

    def test_mock_yearly(self, db_path):
        url = create_checkout_session(
            user_id=1,
            plan="pro_yearly",
            success_url="https://reepo.dev/success",
            cancel_url="https://reepo.dev/cancel",
            path=db_path,
        )
        assert "success" in url

    def test_invalid_plan(self, db_path):
        with pytest.raises(ValueError, match="Invalid plan"):
            create_checkout_session(
                user_id=1,
                plan="invalid_plan",
                success_url="https://reepo.dev/success",
                cancel_url="https://reepo.dev/cancel",
                path=db_path,
            )

    def test_creates_subscription(self, db_path):
        create_checkout_session(
            user_id=42,
            plan="pro_monthly",
            success_url="https://reepo.dev/success",
            cancel_url="https://reepo.dev/cancel",
            path=db_path,
        )
        status = get_subscription_status(42, path=db_path)
        assert status["is_pro"] is True
        assert status["plan"] == "pro_monthly"

    def test_yearly_creates_subscription(self, db_path):
        create_checkout_session(
            user_id=42,
            plan="pro_yearly",
            success_url="https://reepo.dev/success",
            cancel_url="https://reepo.dev/cancel",
            path=db_path,
        )
        status = get_subscription_status(42, path=db_path)
        assert status["is_pro"] is True
        assert status["plan"] == "pro_yearly"


class TestHandleWebhook:
    def test_mock_webhook_returns_success(self, db_path):
        result = handle_webhook(b"payload", "sig", "secret", path=db_path)
        assert result["status"] == "processed"
        assert result["event_type"] == "mock_event"


class TestGetSubscriptionStatus:
    def test_no_subscription(self, db_path):
        status = get_subscription_status(1, path=db_path)
        assert status["plan"] == "free"
        assert status["is_pro"] is False

    def test_active_subscription(self, db_path):
        create_checkout_session(
            user_id=1,
            plan="pro_monthly",
            success_url="https://reepo.dev/success",
            cancel_url="https://reepo.dev/cancel",
            path=db_path,
        )
        status = get_subscription_status(1, path=db_path)
        assert status["plan"] == "pro_monthly"
        assert status["status"] == "active"
        assert status["is_pro"] is True
        assert "current_period_start" in status
        assert "current_period_end" in status

    def test_different_users_independent(self, db_path):
        create_checkout_session(
            user_id=1,
            plan="pro_monthly",
            success_url="https://reepo.dev/success",
            cancel_url="https://reepo.dev/cancel",
            path=db_path,
        )
        status_1 = get_subscription_status(1, path=db_path)
        status_2 = get_subscription_status(2, path=db_path)
        assert status_1["is_pro"] is True
        assert status_2["is_pro"] is False


class TestCancelSubscription:
    def test_cancel_active(self, db_path):
        create_checkout_session(
            user_id=1,
            plan="pro_monthly",
            success_url="https://reepo.dev/success",
            cancel_url="https://reepo.dev/cancel",
            path=db_path,
        )
        assert cancel_subscription(1, path=db_path) is True
        status = get_subscription_status(1, path=db_path)
        assert status["status"] == "cancelled"
        assert status["is_pro"] is False

    def test_cancel_nonexistent(self, db_path):
        assert cancel_subscription(999, path=db_path) is False

    def test_double_cancel(self, db_path):
        create_checkout_session(
            user_id=1,
            plan="pro_monthly",
            success_url="https://reepo.dev/success",
            cancel_url="https://reepo.dev/cancel",
            path=db_path,
        )
        assert cancel_subscription(1, path=db_path) is True
        assert cancel_subscription(1, path=db_path) is False
