import io
import time
import random
import string
import uuid

from flask import current_app

from ..extensions import create_redis_client


def _env(key: str) -> str:
    return _os.getenv(key, "")

_CAPTCHA_TTL = 300  # 5 minutes
_CAPTCHA_LENGTH = 4
_IMG_WIDTH = 176
_IMG_HEIGHT = 60
_MEMORY_CAPTCHAS: dict[str, tuple[str, float]] = {}


def _get_redis() -> object:
    if not hasattr(current_app, "redis"):
        current_app.redis = create_redis_client()
    return current_app.redis


def _generate_code() -> str:
    """Generate a random numeric CAPTCHA code."""
    return "".join(random.choices(string.digits, k=_CAPTCHA_LENGTH))


def _draw_captcha(code: str) -> bytes:
    """Render the code as a noisy PNG image and return raw bytes."""
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (_IMG_WIDTH, _IMG_HEIGHT), _random_color(200, 255))
    draw = ImageDraw.Draw(img)

    # Noise lines
    for _ in range(random.randint(3, 6)):
        x1 = random.randint(0, _IMG_WIDTH)
        y1 = random.randint(0, _IMG_HEIGHT)
        x2 = random.randint(0, _IMG_WIDTH)
        y2 = random.randint(0, _IMG_HEIGHT)
        draw.line([(x1, y1), (x2, y2)], fill=_random_color(100, 200), width=2)

    # Noise dots
    for _ in range(random.randint(50, 120)):
        draw.point(
            (random.randint(0, _IMG_WIDTH), random.randint(0, _IMG_HEIGHT)),
            fill=_random_color(0, 255),
        )

    # Draw large, high-contrast digits.  The former Pillow default bitmap font
    # became unreadable after the browser scaled the image down.
    try:
        from PIL import ImageFont
        try:
            font = ImageFont.truetype("arialbd.ttf", 34)
        except OSError:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", 34)
    except Exception:
        font = None

    char_width = _IMG_WIDTH // _CAPTCHA_LENGTH
    for i, ch in enumerate(code):
        x = i * char_width + random.randint(7, 15)
        y = random.randint(8, 14)
        draw.text((x, y), ch, fill=_random_color(0, 70), font=font, stroke_width=1)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _random_color(low: int, high: int) -> tuple[int, int, int]:
    return (random.randint(low, high), random.randint(low, high), random.randint(low, high))


def create_captcha() -> tuple[str, bytes]:
    """Generate a CAPTCHA image and store its one-time answer."""
    code = _generate_code()
    image_bytes = _draw_captcha(code)
    token = str(uuid.uuid4())
    redis_key = f"captcha:{token}"
    redis = _get_redis()
    if redis is not None:
        try:
            redis.setex(redis_key, _CAPTCHA_TTL, code)
        except Exception:
            _MEMORY_CAPTCHAS[token] = (code, time.monotonic() + _CAPTCHA_TTL)
    else:
        _MEMORY_CAPTCHAS[token] = (code, time.monotonic() + _CAPTCHA_TTL)
    return token, image_bytes


def validate_captcha(token: str, code: str) -> bool:
    """Verify a one-time CAPTCHA answer with a local development fallback."""
    if current_app.config.get("TESTING", False):
        return True
    if not token or not code:
        return False
    redis_key = f"captcha:{token}"
    redis = _get_redis()
    if redis is not None:
        try:
            stored = redis.get(redis_key)
            if stored is not None:
                redis.delete(redis_key)
                return stored.decode("utf-8") == code.strip()
        except Exception:
            pass
    stored = _MEMORY_CAPTCHAS.pop(token, None)
    if stored is None:
        return False
    stored_code, expires_at = stored
    return time.monotonic() <= expires_at and stored_code == code.strip()
