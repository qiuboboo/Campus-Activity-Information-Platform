"""Email sending and verification-code management backed by Redis."""

import random
import smtplib
import time
from email.mime.text import MIMEText

from flask import current_app

_VERIFY_TTL = 300  # 5 minutes
_COOLDOWN = 60     # 60 seconds between resends
_CODE_LENGTH = 6
_MEMORY_CODES: dict[str, tuple[str, float]] = {}
_MEMORY_COOLDOWNS: dict[str, float] = {}


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


def send_verification_code(email: str, purpose: str = "register") -> dict:
    """Generate a 6-digit code, store in Redis, and send via email.

    Returns dict with ``message`` and ``expires_in``.  Local SQLite
    development deliberately runs without Redis and SMTP, so it uses a
    short-lived in-memory code and returns it to the local UI for testing.
    """
    if current_app.config.get("TESTING", False):
        return {"message": "验证码已发送", "expires_in": _VERIFY_TTL}

    redis = _get_redis()
    key_prefix = f"verify:{purpose}:{email}"
    cooldown_key = f"{key_prefix}:cooldown"
    code_key = f"{key_prefix}:code"
    code = _generate_code()
    use_memory = redis is None

    if redis is not None:
        try:
            if redis.exists(cooldown_key):
                raise RuntimeError(f"请 {redis.ttl(cooldown_key)} 秒后再试")
            redis.setex(code_key, _VERIFY_TTL, code)
            redis.setex(cooldown_key, _COOLDOWN, "1")
        except RuntimeError:
            raise
        except Exception:
            use_memory = True

    if use_memory:
        now = time.monotonic()
        memory_key = f"{purpose}:{email}"
        cooldown_until = _MEMORY_COOLDOWNS.get(memory_key, 0)
        if cooldown_until > now:
            raise RuntimeError(f"请 {int(cooldown_until - now) + 1} 秒后再试")
        _MEMORY_CODES[memory_key] = (code, now + _VERIFY_TTL)
        _MEMORY_COOLDOWNS[memory_key] = now + _COOLDOWN

        if not current_app.config.get("MAIL_DEFAULT_SENDER"):
            return {"message": "验证码已生成（本地开发模式）", "expires_in": _VERIFY_TTL, "code": code}

    action = "重置密码" if purpose == "password_reset" else "邮箱验证"
    body = f"您用于{action}的验证码是：{code}\n\n该验证码 {_VERIFY_TTL // 60} 分钟内有效，请勿泄露给他人。"
    try:
        send_email(email, "校园活动信息平台 — 邮箱验证", body)
    except Exception:
        if use_memory:
            return {"message": "验证码已生成（本地开发模式）", "expires_in": _VERIFY_TTL, "code": code}
        raise

    return {"message": "验证码已发送", "expires_in": _VERIFY_TTL}


def verify_code(email: str, code: str, purpose: str = "register") -> bool:
    """Check a verification code.  One-time use — deletes the key regardless."""
    # Bypass in test mode
    if current_app.config.get("TESTING", False):
        return True

    redis = _get_redis()
    code_key = f"verify:{purpose}:{email}:code"
    if redis is not None:
        try:
            stored = redis.get(code_key)
            if stored is not None:
                redis.delete(code_key)
                return stored.decode("utf-8") == code.strip()
        except Exception:
            pass

    stored = _MEMORY_CODES.pop(f"{purpose}:{email}", None)
    if stored is None:
        return False
    expected, expires_at = stored
    return time.monotonic() <= expires_at and expected == code.strip()
