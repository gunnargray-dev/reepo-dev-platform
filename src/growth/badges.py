"""Reepo badges — generate SVG badges for repo scores."""
from __future__ import annotations

from src.db import _connect, get_repo, DEFAULT_DB_PATH


def _score_color(score: int) -> str:
    """Map score to badge color."""
    if score >= 80:
        return "#4c1"
    if score >= 60:
        return "#a4a61d"
    if score >= 40:
        return "#dfb317"
    return "#e05d44"


def _text_width(text: str) -> int:
    """Estimate text width in pixels."""
    return len(text) * 7 + 10


def generate_badge_svg(
    owner: str,
    name: str,
    score: int,
    style: str = "flat",
) -> str:
    """Generate a shields.io-style SVG badge for a repo's Reepo score."""
    label = "reepo score"
    value = str(score)
    color = _score_color(score)

    label_width = _text_width(label)
    value_width = _text_width(value)
    total_width = label_width + value_width

    if style == "for-the-badge":
        label = label.upper()
        value = value.upper()
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="28">'
            f'<rect width="{label_width}" height="28" fill="#555"/>'
            f'<rect x="{label_width}" width="{value_width}" height="28" fill="{color}"/>'
            f'<text x="{label_width // 2}" y="18" fill="#fff" '
            f'text-anchor="middle" font-family="Verdana,sans-serif" font-size="11" '
            f'font-weight="bold">{label}</text>'
            f'<text x="{label_width + value_width // 2}" y="18" fill="#fff" '
            f'text-anchor="middle" font-family="Verdana,sans-serif" font-size="11" '
            f'font-weight="bold">{value}</text>'
            f'</svg>'
        )

    radius = "" if style == "flat-square" else ' rx="3"'

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="20">'
        f'<rect width="{label_width}" height="20" fill="#555"{radius}/>'
        f'<rect x="{label_width}" width="{value_width}" height="20" fill="{color}"{radius}/>'
        f'<text x="{label_width // 2}" y="14" fill="#fff" '
        f'text-anchor="middle" font-family="Verdana,sans-serif" font-size="11">{label}</text>'
        f'<text x="{label_width + value_width // 2}" y="14" fill="#fff" '
        f'text-anchor="middle" font-family="Verdana,sans-serif" font-size="11">{value}</text>'
        f'</svg>'
    )


def get_badge_for_repo(
    owner: str, name: str, style: str = "flat", path: str = DEFAULT_DB_PATH
) -> str | None:
    """Get badge SVG for a repo by owner/name. Returns None if repo not found."""
    repo = get_repo(owner, name, path)
    if not repo:
        return None
    score = repo.get("reepo_score") or 0
    return generate_badge_svg(owner, name, score, style)
