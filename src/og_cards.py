"""Reepo OG card generator — 1200x630 PNG social cards via Pillow."""
import io

from PIL import Image, ImageDraw, ImageFont


# Colors
BG_COLOR = (15, 23, 42)          # #0f172a dark navy
WHITE = (255, 255, 255)
MUTED = (148, 163, 184)          # slate-400
BRAND_BLUE = (56, 189, 248)      # sky-400

# Score colors
SCORE_GREEN = (74, 222, 128)     # green-400
SCORE_YELLOW = (250, 204, 21)    # yellow-400
SCORE_ORANGE = (251, 146, 60)    # orange-400
SCORE_RED = (248, 113, 113)      # red-400

WIDTH = 1200
HEIGHT = 630


def _score_color(score: int) -> tuple:
    """Return RGB color tuple based on Reepo score."""
    if score >= 80:
        return SCORE_GREEN
    if score >= 60:
        return SCORE_YELLOW
    if score >= 40:
        return SCORE_ORANGE
    return SCORE_RED


def _get_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a TrueType font or fall back to the default bitmap font."""
    for path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    ]:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def generate_og_card(repo_data: dict) -> bytes:
    """Generate a 1200x630 PNG OG card for a repository.

    repo_data keys: owner, name, reepo_score, stars, category_primary, description
    """
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    font_large = _get_font(48)
    font_medium = _get_font(32)
    font_small = _get_font(24)
    font_brand = _get_font(28)

    owner = repo_data.get("owner", "")
    name = repo_data.get("name", "")
    score = repo_data.get("reepo_score") or 0
    stars = repo_data.get("stars", 0)
    category = repo_data.get("category_primary", "")
    description = repo_data.get("description", "")

    # Branding top-left
    draw.text((60, 40), "reepo.dev", fill=BRAND_BLUE, font=font_brand)

    # Owner/name
    draw.text((60, 120), f"{owner}/", fill=MUTED, font=font_medium)
    owner_bbox = draw.textbbox((60, 120), f"{owner}/", font=font_medium)
    draw.text((owner_bbox[2] + 4, 108), name, fill=WHITE, font=font_large)

    # Description (truncate at 100 chars)
    if description:
        desc_text = description[:100] + ("..." if len(description) > 100 else "")
        draw.text((60, 190), desc_text, fill=MUTED, font=font_small)

    # Score circle area
    score_color = _score_color(score)
    score_x = 60
    score_y = 300

    # Score label
    draw.text((score_x, score_y), "Reepo Score", fill=MUTED, font=font_small)
    draw.text((score_x, score_y + 40), str(score), fill=score_color, font=font_large)

    # Stars
    stars_x = 350
    draw.text((stars_x, score_y), "Stars", fill=MUTED, font=font_small)
    star_label = f"{stars:,}" if isinstance(stars, int) else str(stars)
    draw.text((stars_x, score_y + 40), star_label, fill=WHITE, font=font_large)

    # Category
    if category:
        cat_x = 650
        draw.text((cat_x, score_y), "Category", fill=MUTED, font=font_small)
        draw.text((cat_x, score_y + 40), category, fill=WHITE, font=font_medium)

    # Bottom bar accent
    draw.rectangle([0, HEIGHT - 6, WIDTH, HEIGHT], fill=BRAND_BLUE)

    # Bottom branding
    draw.text((60, HEIGHT - 60), "Open Source AI Discovery", fill=MUTED, font=font_small)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
