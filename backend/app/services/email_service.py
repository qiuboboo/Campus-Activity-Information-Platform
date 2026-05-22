"""Email sending and verification-code management backed by Redis."""

import random
import smtplib
from email.mime.text import MIMEText

from flask import current_app

_VERIFY_TTL = 300  # 5 minutes
_COOLDOWN = 60     # 60 seconds between resends
_CODE_LENGTH = 6


def _get_redis():
    return getattr(current_app, "redis", None)


def _generate_code() -> str:
    return "".join(random.choices("0123456789", k=_CODE_LENGTH))


def send_email(recipient: str, subject: str, body: str) -> None:
    """Send a plain-text email via SMTP.

    Raises smtplib.SMTPException on failure.
    """
    config = current_app.config
    sender = config["MAIL_DEFAULT_SENDER"]
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient

    with smtplib.SMTP(config["MAIL_SERVER"], config["MAIL_PORT"]) as server:
        if config.get("MAIL_USE_TLS", True):
            server.starttls()
        username = config.get("MAIL_USERNAME") or ""
        password = config.get("MAIL_PASSWORD") or ""
        if username and password:
            server.login(username, password)
        server.sendmail(sender, [recipient], msg.as_string())


def send_verification_code(email: str) -> dict:
    """Generate a 6-digit code, store in Redis, and send via email.

    Returns dict with ``message`` and ``expires_in``.
    Raises RuntimeError if Redis is unavailable.
    """
    if current_app.config.get("TESTING", False):
        return {"message": "验证码已发送", "expires_in": _VERIFY_TTL}

    redis = _get_redis()
    if redis is None:
        raise RuntimeError("Redis is not available — cannot send verification code")

    # Cooldown check
    cooldown_key = f"verify:cooldown:{email}"
    if redis.exists(cooldown_key):
        ttl = redis.ttl(cooldown_key)
        raise RuntimeError(f"请 {ttl} 秒后再试")

    code = _generate_code()
    code_key = f"verify:code:{email}"

    # Store code, set TTL
    redis.setex(code_key, _VERIFY_TTL, code)
    # Cooldown so user can't spam resend
    redis.setex(cooldown_key, _COOLDOWN, "1")

    body = f"您的验证码是：{code}\n\n该验证码 {_VERIFY_TTL // 60} 分钟内有效，请勿泄露给他人。"
    send_email(email, "校园活动信息平台 — 邮箱验证", body)

    return {"message": "验证码已发送", "expires_in": _VERIFY_TTL}


def verify_code(email: str, code: str) -> bool:
    """Check a verification code.  One-time use — deletes the key regardless."""
    redis = _get_redis()
    if redis is None:
        return False

    # Bypass in test mode
    if current_app.config.get("TESTING", False):
        return True

    code_key = f"verify:code:{email}"
    stored = redis.get(code_key)
    if stored is None:
        return False
    redis.delete(code_key)
    return stored.decode("utf-8") == code.strip()
