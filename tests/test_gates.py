"""Tests for the Reepo Pro feature gates — pro checks and feature limits."""
import os
import tempfile

import pytest
from fastapi import HTTPException

from src.db import init_db
from src.monetization.db import init_monetization_db
from src.monetization.gates import (
    FREE_COLLECTION_LIMIT,
    FREE_API_LIMIT,
    PRO_API_LIMIT,
    is_pro,
    require_pro,
    get_collection_limit,
    get_api_limit,
)
from src.monetization.stripe_billing import create_checkout_session


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    init_monetization_db(path)
    yield path
    os.unlink(path)


def _make_pro_user(user_id: int, path: str) -> None:
    create_checkout_session(
        user_id=user_id,
        plan="pro_monthly",
        success_url="https://reepo.dev/success",
        cancel_url="https://reepo.dev/cancel",
        path=path,
    )


class TestIsPro:
    def test_free_user(self, db_path):
        assert is_pro(1, path=db_path) is False

    def test_pro_user(self, db_path):
        _make_pro_user(1, db_path)
        assert is_pro(1, path=db_path) is True

    def test_different_user_not_pro(self, db_path):
        _make_pro_user(1, db_path)
        assert is_pro(2, path=db_path) is False


class TestRequirePro:
    def test_raises_401_for_none_user(self, db_path):
        with pytest.raises(HTTPException) as exc_info:
            require_pro(None, path=db_path)
        assert exc_info.value.status_code == 401

    def test_raises_403_for_free_user(self, db_path):
        with pytest.raises(HTTPException) as exc_info:
            require_pro(1, path=db_path)
        assert exc_info.value.status_code == 403
        assert "Pro subscription required" in str(exc_info.value.detail)

    def test_passes_for_pro_user(self, db_path):
        _make_pro_user(1, db_path)
        require_pro(1, path=db_path)  # Should not raise


class TestGetCollectionLimit:
    def test_free_user_limit(self, db_path):
        assert get_collection_limit(1, path=db_path) == FREE_COLLECTION_LIMIT

    def test_pro_user_unlimited(self, db_path):
        _make_pro_user(1, db_path)
        limit = get_collection_limit(1, path=db_path)
        assert limit > FREE_COLLECTION_LIMIT

    def test_none_user_gets_free_limit(self, db_path):
        assert get_collection_limit(None, path=db_path) == FREE_COLLECTION_LIMIT


class TestGetApiLimit:
    def test_free_user_limit(self, db_path):
        assert get_api_limit(1, path=db_path) == FREE_API_LIMIT

    def test_pro_user_limit(self, db_path):
        _make_pro_user(1, db_path)
        assert get_api_limit(1, path=db_path) == PRO_API_LIMIT

    def test_none_user_gets_free_limit(self, db_path):
        assert get_api_limit(None, path=db_path) == FREE_API_LIMIT


class TestConstants:
    def test_free_collection_limit_is_3(self):
        assert FREE_COLLECTION_LIMIT == 3

    def test_free_api_limit_is_100(self):
        assert FREE_API_LIMIT == 100

    def test_pro_api_limit_is_10000(self):
        assert PRO_API_LIMIT == 10000
