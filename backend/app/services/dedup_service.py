import hashlib
import re

from ..models import Poster


def _normalize_title(title: str) -> str:
    """Normalize title for dedup: lowercase, strip, remove extra spaces."""
    text = title.strip().lower()
    text = re.sub(r"[^a-z0-9一-鿿\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _normalize_location(location: str | None) -> str | None:
    if not location:
        return None
    text = location.strip().lower()
    text = re.sub(r"[^a-z0-9一-鿿\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _date_key(event_date) -> str | None:
    if event_date is None:
        return None
    return event_date.date().isoformat()


def generate_title_key(title: str) -> str:
    norm = _normalize_title(title)
    if not norm:
        return ""
    return hashlib.md5(norm.encode("utf-8")).hexdigest()


def generate_source_key(source_url: str | None) -> str | None:
    if not source_url:
        return None
    url = source_url.strip().rstrip("/")
    return hashlib.md5(url.encode("utf-8")).hexdigest()


def generate_fingerprint(title: str, event_date, location: str | None) -> str:
    parts = [generate_title_key(title)]
    dk = _date_key(event_date)
    if dk:
        parts.append(dk)
    lk = _normalize_location(location)
    if lk:
        parts.append(hashlib.md5(lk.encode("utf-8")).hexdigest())
    return hashlib.md5("|".join(parts).encode("utf-8")).hexdigest()


def check_duplicates(
    title: str,
    source_url: str | None,
    event_date,
    location: str | None,
    exclude_id: int | None = None,
) -> dict:
    """Check for existing duplicates. Returns dict with duplicate info."""
    source_key = generate_source_key(source_url)
    fingerprint = generate_fingerprint(title, event_date, location)

    result = {"is_duplicate": False, "duplicate_group_key": None, "existing": []}

    # Exact source_url match
    if source_key:
        existing = Poster.query.filter_by(source_fingerprint=source_key)
        if exclude_id is not None:
            existing = existing.filter(Poster.id != exclude_id)
        existing = existing.first()
        if existing:
            result["is_duplicate"] = True
            result["duplicate_group_key"] = existing.duplicate_group_key or source_key
            result["existing"].append(existing.id)
            return result

    # Fingerprint match (same title + date + location)
    existing = Poster.query.filter_by(source_fingerprint=fingerprint)
    if exclude_id is not None:
        existing = existing.filter(Poster.id != exclude_id)
    existing = existing.first()
    if existing:
        result["is_duplicate"] = True
        result["duplicate_group_key"] = existing.duplicate_group_key or fingerprint
        result["existing"].append(existing.id)
        return result

    return result
