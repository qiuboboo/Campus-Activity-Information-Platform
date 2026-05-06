from datetime import datetime


def _parse_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def _auto_title(raw_text: str) -> str:
    first_line = raw_text.strip().splitlines()[0]
    return first_line[:80]


def _auto_summary(raw_text: str) -> str:
    text = " ".join(raw_text.strip().split())
    return text[:120]


def build_poster_fields(payload: dict, fallback=None) -> dict:
    raw_text = (payload.get("raw_text") or getattr(fallback, "raw_text", "")).strip()
    title = (payload.get("title") or getattr(fallback, "title", "")).strip() or _auto_title(raw_text)
    summary = (payload.get("summary") or getattr(fallback, "summary", "")).strip() or _auto_summary(raw_text)
    location = (payload.get("location") or getattr(fallback, "location", "") or "").strip() or None
    organizer = (payload.get("organizer") or getattr(fallback, "organizer", "") or "").strip() or None
    source_type = (payload.get("source_type") or getattr(fallback, "source_type", "manual")).strip() or "manual"
    source_url = (payload.get("source_url") or getattr(fallback, "source_url", "") or "").strip() or None
    status = (payload.get("status") or getattr(fallback, "status", "draft")).strip() or "draft"

    event_time_input = payload.get("event_time", getattr(fallback, "event_time", None))
    event_time = _parse_datetime(event_time_input) if event_time_input else None

    return {
        "title": title,
        "raw_text": raw_text,
        "summary": summary,
        "event_time": event_time,
        "location": location,
        "organizer": organizer,
        "status": status,
        "source_type": source_type,
        "source_url": source_url,
    }
