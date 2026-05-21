"""Crawler security: URL validation, content sanitisation, rate limiting."""

import re
import time
from urllib.parse import urlparse

import html

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ALLOWED_SCHEMES = ("http", "https")

# Prefixes that indicate a private / internal IPv4 address.
_BLOCKED_HOST_PREFIXES = (
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "10.",
    "172.16.",
    "172.17.",
    "172.18.",
    "172.19.",
    "172.20.",
    "172.21.",
    "172.22.",
    "172.23.",
    "172.24.",
    "172.25.",
    "172.26.",
    "172.27.",
    "172.28.",
    "172.29.",
    "172.30.",
    "172.31.",
    "192.168.",
)

_SENSITIVE_PATTERNS: dict[str, re.Pattern] = {
    "phone": re.compile(r"1[3-9]\d{9}"),
    "id_card": re.compile(r"\d{17}[\dXx]"),
    "email": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
}


class SecurityError(ValueError):
    """Raised when a crawler request violates a security constraint."""

    pass


# ---------------------------------------------------------------------------
# URL validation
# ---------------------------------------------------------------------------


def validate_target_url(url: str, allowed_domains: list[str] | None = None) -> str:
    """Check that *url* is safe to crawl.

    Raises :class:`SecurityError` if the URL:
    - uses a disallowed scheme
    - points to an internal / private IP
    - does not match any entry in *allowed_domains*

    Returns the normalised URL on success.
    """
    parsed = urlparse(url)

    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise SecurityError(f"Disallowed URL scheme: {parsed.scheme}")

    host = (parsed.hostname or "").lower()

    if _is_internal(host):
        raise SecurityError(f"Internal address blocked: {host}")

    if allowed_domains:
        if not _matches_any_domain(host, allowed_domains):
            raise SecurityError(
                f"Domain '{host}' not in allowed domains: {allowed_domains}"
            )

    return url


def _is_internal(host: str) -> bool:
    for prefix in _BLOCKED_HOST_PREFIXES:
        if host.startswith(prefix):
            return True
    return False


def _matches_any_domain(host: str, allowed_domains: list[str]) -> bool:
    for domain in allowed_domains:
        domain = domain.strip().lower()
        if domain.startswith("*."):
            # Wildcard: *.sysu.edu.cn matches anything.sysu.edu.cn
            suffix = domain[1:]  # remove *
            if host == suffix.lstrip(".") or host.endswith(suffix):
                return True
        elif host == domain or host.endswith("." + domain):
            return True
    return False


# ---------------------------------------------------------------------------
# Redirect safety
# ---------------------------------------------------------------------------


def check_redirect_safety(original_url: str, redirect_url: str | None) -> str:
    """Validate the final URL after a redirect chain.

    Returns the final URL, or raises :class:`SecurityError` if the redirect
    leads to a different domain that isn't allowed.
    """
    if redirect_url is None or redirect_url == original_url:
        return original_url

    orig_host = urlparse(original_url).hostname or ""
    redir_host = urlparse(redirect_url).hostname or ""

    if redir_host != orig_host:
        raise SecurityError(
            f"Cross-domain redirect blocked: {orig_host} -> {redir_host}"
        )
    return redirect_url


# ---------------------------------------------------------------------------
# Content sanitisation
# ---------------------------------------------------------------------------


def sanitise_crawled_text(text: str) -> str:
    """Strip control characters and escape HTML entities."""
    # Strip control chars except tab, newline, carriage-return
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # Escape angle-brackets & ampersands (defence-in-depth)
    text = html.escape(text, quote=True)
    return text.strip()


def mask_sensitive(text: str) -> str:
    """Mask common Chinese personal-identifier patterns.

    Only a best-effort pass — not a replacement for proper PII detection.
    """
    for _name, pattern in _SENSITIVE_PATTERNS.items():
        text = pattern.sub(lambda m: m.group()[:3] + "****" + m.group()[-2:], text)
    return text


# ---------------------------------------------------------------------------
# Rate limiting (in-process per-data-source)
# ---------------------------------------------------------------------------

_last_request_time: dict[int, float] = {}


def rate_limit(data_source_id: int, interval: int | None = None) -> None:
    """Sleep if needed to enforce *interval* seconds between requests.

    Call this before every HTTP request made on behalf of a data source.
    """
    if interval is None:
        try:
            from flask import current_app
            interval = current_app.config.get("CRAWL_REQUEST_INTERVAL", 2)
        except (RuntimeError, ImportError):
            interval = 2

    last = _last_request_time.get(data_source_id, 0.0)
    elapsed = time.time() - last
    if elapsed < interval:
        time.sleep(interval - elapsed)
    _last_request_time[data_source_id] = time.time()


def reset_rate_limit(data_source_id: int) -> None:
    """Clear the rate-limit tracker (e.g. after a crawl finishes)."""
    _last_request_time.pop(data_source_id, None)
