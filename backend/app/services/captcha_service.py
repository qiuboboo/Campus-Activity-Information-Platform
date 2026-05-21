import io
import random
import string
import uuid

from flask import current_app

from ..extensions import create_redis_client

_CAPTCHA_TTL = 300  # 5 minutes
_CAPTCHA_LENGTH = 4
_IMG_WIDTH = 140
_IMG_HEIGHT = 48


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

    # Draw digits with random offsets
    try:
        from PIL import ImageFont

        font = ImageFont.load_default()
    except Exception:
        font = None

    char_width = _IMG_WIDTH // _CAPTCHA_LENGTH
    for i, ch in enumerate(code):
        x = i * char_width + random.randint(3, char_width - 14)
        y = random.randint(4, _IMG_HEIGHT - 16)
        draw.text((x, y), ch, fill=_random_color(0, 100), font=font)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _random_color(low: int, high: int) -> tuple[int, int, int]:
    return (random.randint(low, high), random.randint(low, high), random.randint(low, high))


def create_captcha() -> tuple[str, bytes]:
    """Generate a CAPTCHA image and return (token, image_bytes).

    The token is a UUID that maps to the correct answer in Redis.
    The caller returns the image to the client; the client must submit
    both the token and the user-entered code when logging in.
    """
    code = _generate_code()
    image_bytes = _draw_captcha(code)

    token = str(uuid.uuid4())
    redis_key = f"captcha:{token}"
    _get_redis().setex(redis_key, _CAPTCHA_TTL, code)

    return token, image_bytes


def validate_captcha(token: str, code: str) -> bool:
    """Verify a CAPTCHA answer.  One-time use — deletes the key regardless."""
    if not token or not code:
        return False

    redis_key = f"captcha:{token}"
    r = _get_redis()
    stored = r.get(redis_key)
    if stored is None:
        return False

    # Always delete so the token cannot be replayed
    r.delete(redis_key)

    return stored.decode("utf-8") == code.strip()
