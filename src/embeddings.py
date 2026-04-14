"""Voyage AI embedding client wrapper for reepo.

Pure embedding I/O — no DB code. Used by downstream features (build
recommender, semantic similar-repos) to embed repo text and queries.
"""
from __future__ import annotations

import logging
import os
import time

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "voyage-3-lite"
EMBEDDING_DIM = 512
EMBEDDING_VERSION = 1

_MAX_BATCH = 128
_MAX_RETRIES = 4
_INITIAL_BACKOFF = 1.0

_client = None


def _get_client():
    """Lazy-init the Voyage client. Raises if API key is missing."""
    global _client
    if _client is not None:
        return _client
    api_key = os.environ.get("VOYAGE_API_KEY")
    if not api_key:
        raise RuntimeError("VOYAGE_API_KEY not set")
    import voyageai

    _client = voyageai.Client(api_key=api_key)
    return _client


def _reset_client_for_tests() -> None:
    """Test helper — drop the cached client so monkeypatched env is re-read."""
    global _client
    _client = None


def _transient_exc_types() -> tuple[type[BaseException], ...]:
    """Lazily resolve voyageai's transient exception classes.

    We retry only on rate-limit, server, connection, service-unavailable, and
    timeout errors. Auth / invalid-request errors surface immediately.
    """
    try:
        from voyageai import error as ve  # type: ignore

        return (
            ve.RateLimitError,
            ve.ServerError,
            ve.ServiceUnavailableError,
            ve.APIConnectionError,
            ve.Timeout,
        )
    except Exception:  # noqa: BLE001
        return ()


def _embed_with_retry(texts: list[str], input_type: str) -> list[list[float]]:
    """Call Voyage with exponential backoff on transient errors only."""
    client = _get_client()
    transient = _transient_exc_types()
    backoff = _INITIAL_BACKOFF
    last_err: BaseException | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            resp = client.embed(
                texts,
                model=EMBEDDING_MODEL,
                input_type=input_type,
            )
            return list(resp.embeddings)
        except transient as e:  # type: ignore[misc]
            last_err = e
            if attempt == _MAX_RETRIES - 1:
                break
            logger.warning(
                "Voyage embed attempt %d failed (transient): %s; retrying in %.1fs",
                attempt + 1,
                e,
                backoff,
            )
            time.sleep(backoff)
            backoff *= 2
    assert last_err is not None
    raise last_err


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of documents. Batched to <=128 per Voyage request."""
    if not texts:
        return []
    out: list[list[float]] = []
    for i in range(0, len(texts), _MAX_BATCH):
        chunk = texts[i : i + _MAX_BATCH]
        out.extend(_embed_with_retry(chunk, input_type="document"))
    return out


def embed_query(text: str) -> list[float]:
    """Embed a single query string (Voyage input_type='query')."""
    result = _embed_with_retry([text], input_type="query")
    return result[0]
