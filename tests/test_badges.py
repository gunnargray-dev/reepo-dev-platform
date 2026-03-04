"""Tests for badges module — SVG output, color mapping, styles, well-formedness."""
import pytest

from src.growth.badges import generate_badge_svg, _score_color


class TestScoreColor:
    def test_green_high_score(self):
        assert _score_color(80) == "#4c1"
        assert _score_color(100) == "#4c1"

    def test_yellowgreen_medium_score(self):
        assert _score_color(60) == "#a4a61d"
        assert _score_color(79) == "#a4a61d"

    def test_yellow_low_score(self):
        assert _score_color(40) == "#dfb317"
        assert _score_color(59) == "#dfb317"

    def test_red_very_low_score(self):
        assert _score_color(0) == "#e05d44"
        assert _score_color(39) == "#e05d44"


class TestGenerateBadgeSvg:
    def test_flat_style_default(self):
        svg = generate_badge_svg("org", "repo", 85)
        assert svg.startswith("<svg")
        assert svg.endswith("</svg>")
        assert "reepo score" in svg
        assert "85" in svg

    def test_flat_square_style(self):
        svg = generate_badge_svg("org", "repo", 75, style="flat-square")
        assert "<svg" in svg
        assert "</svg>" in svg
        assert 'rx="3"' not in svg

    def test_for_the_badge_style(self):
        svg = generate_badge_svg("org", "repo", 90, style="for-the-badge")
        assert "<svg" in svg
        assert 'height="28"' in svg

    def test_green_color_for_high_score(self):
        svg = generate_badge_svg("org", "repo", 85)
        assert "#4c1" in svg

    def test_red_color_for_low_score(self):
        svg = generate_badge_svg("org", "repo", 20)
        assert "#e05d44" in svg

    def test_yellow_color_for_medium_score(self):
        svg = generate_badge_svg("org", "repo", 50)
        assert "#dfb317" in svg

    def test_yellowgreen_color(self):
        svg = generate_badge_svg("org", "repo", 65)
        assert "#a4a61d" in svg

    def test_svg_well_formed(self):
        svg = generate_badge_svg("org", "repo", 75)
        assert svg.count("<svg") == 1
        assert svg.count("</svg>") == 1
        assert 'xmlns="http://www.w3.org/2000/svg"' in svg

    def test_svg_contains_score_value(self):
        for score in [0, 25, 50, 75, 100]:
            svg = generate_badge_svg("org", "repo", score)
            assert str(score) in svg

    def test_all_styles_produce_valid_svg(self):
        for style in ["flat", "flat-square", "for-the-badge"]:
            svg = generate_badge_svg("org", "repo", 70, style=style)
            assert svg.startswith("<svg")
            assert svg.endswith("</svg>")
