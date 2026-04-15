"""Rule-based classifier deciding whether a query is natural-language.

Used by GET /api/search to optionally route NL queries through the AI build
pipeline. Pure, deterministic, no I/O — safe to call on every request.
"""
from __future__ import annotations

import re

# Multi-word phrases checked via substring match (case-insensitive).
_NL_PHRASES = (
    "looking for",
    "help me",
    "how do i",
)

# Single-word action verbs checked via whole-word match.
_NL_VERBS = {
    "build",
    "make",
    "create",
    "want",
    "need",
}

_WORD_RE = re.compile(r"\b[\w']+\b", re.UNICODE)


def is_natural_language(query: str) -> bool:
    """Return True if the query looks like natural language rather than keywords.

    Rules (any one triggers True):
      - Word count > 6
      - Contains an action verb / NL phrase
      - Ends with a question mark
    """
    if not query:
        return False
    q = query.strip()
    if not q:
        return False

    if q.endswith("?"):
        return True

    lower = q.lower()
    for phrase in _NL_PHRASES:
        if phrase in lower:
            return True

    words = _WORD_RE.findall(lower)
    if len(words) > 6:
        return True

    for w in words:
        if w in _NL_VERBS:
            return True

    return False
