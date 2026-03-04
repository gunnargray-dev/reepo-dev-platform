"""Tests for OG card generator — PNG output, dimensions, score colors."""
import io

import pytest
from PIL import Image

from src.og_cards import generate_og_card, _score_color, WIDTH, HEIGHT


SAMPLE_REPO = {
    "owner": "openai",
    "name": "whisper",
    "full_name": "openai/whisper",
    "description": "Robust Speech Recognition via Large-Scale Weak Supervision",
    "reepo_score": 92,
    "stars": 50000,
    "category_primary": "models",
}


class TestScoreColor:
    def test_green_high(self):
        assert _score_color(80) == (74, 222, 128)
        assert _score_color(100) == (74, 222, 128)

    def test_yellow_medium(self):
        assert _score_color(60) == (250, 204, 21)
        assert _score_color(79) == (250, 204, 21)

    def test_orange_low(self):
        assert _score_color(40) == (251, 146, 60)
        assert _score_color(59) == (251, 146, 60)

    def test_red_very_low(self):
        assert _score_color(0) == (248, 113, 113)
        assert _score_color(39) == (248, 113, 113)


class TestGenerateOgCard:
    def test_returns_bytes(self):
        result = generate_og_card(SAMPLE_REPO)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_png_magic_bytes(self):
        result = generate_og_card(SAMPLE_REPO)
        assert result[:4] == b'\x89PNG'

    def test_correct_dimensions(self):
        result = generate_og_card(SAMPLE_REPO)
        img = Image.open(io.BytesIO(result))
        assert img.size == (WIDTH, HEIGHT)
        assert img.size == (1200, 630)

    def test_rgb_mode(self):
        result = generate_og_card(SAMPLE_REPO)
        img = Image.open(io.BytesIO(result))
        assert img.mode == "RGB"

    def test_minimal_repo_data(self):
        result = generate_og_card({"owner": "a", "name": "b"})
        assert isinstance(result, bytes)
        img = Image.open(io.BytesIO(result))
        assert img.size == (1200, 630)

    def test_empty_description(self):
        repo = {**SAMPLE_REPO, "description": ""}
        result = generate_og_card(repo)
        assert isinstance(result, bytes)

    def test_no_category(self):
        repo = {**SAMPLE_REPO}
        del repo["category_primary"]
        result = generate_og_card(repo)
        assert isinstance(result, bytes)

    def test_long_description_truncated(self):
        repo = {**SAMPLE_REPO, "description": "x" * 200}
        result = generate_og_card(repo)
        assert isinstance(result, bytes)
        img = Image.open(io.BytesIO(result))
        assert img.size == (1200, 630)

    def test_zero_score(self):
        repo = {**SAMPLE_REPO, "reepo_score": 0}
        result = generate_og_card(repo)
        assert isinstance(result, bytes)

    def test_none_score(self):
        repo = {**SAMPLE_REPO, "reepo_score": None}
        result = generate_og_card(repo)
        assert isinstance(result, bytes)

    def test_different_scores_produce_different_images(self):
        repo_high = {**SAMPLE_REPO, "reepo_score": 90}
        repo_low = {**SAMPLE_REPO, "reepo_score": 20}
        img_high = generate_og_card(repo_high)
        img_low = generate_og_card(repo_low)
        # Different scores should produce different images
        assert img_high != img_low
