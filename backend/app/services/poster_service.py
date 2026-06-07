from datetime import datetime
from html import escape


def generate_poster_html(
    title: str,
    summary: str,
    event_time: datetime | None = None,
    location: str | None = None,
    organizer: str | None = None,
    activity_type: str | None = None,
) -> str:
    """Generate a clean HTML poster card for an activity.

    Returns a self-contained HTML fragment suitable for embedding in
    a page or returning via the API.
    """
    time_str = event_time.strftime("%Y-%m-%d %H:%M") if event_time else ""

    lines = [f'<div class="activity-poster">']
    lines.append(f'  <h2 class="poster-title">{escape(title)}</h2>')

    if time_str:
        lines.append(f'  <p class="poster-time"><strong>时间：</strong>{escape(time_str)}</p>')
    if location:
        lines.append(f'  <p class="poster-location"><strong>地点：</strong>{escape(location)}</p>')
    if organizer:
        lines.append(f'  <p class="poster-organizer"><strong>主办方：</strong>{escape(organizer)}</p>')
    if activity_type:
        lines.append(f'  <p class="poster-type"><strong>类型：</strong>{escape(activity_type)}</p>')

    if summary:
        lines.append(f'  <p class="poster-summary">{escape(summary)}</p>')

    lines.append("</div>")
    return "\n".join(lines)


def auto_extract_fields(title: str, content: str) -> dict:
    """Extract structured fields from title + content using fallback extraction."""
    from .fallback_extractor import fallback_extract

    text = f"{title}\n{content}"
    extracted = fallback_extract(text)
    if "title" not in extracted or not extracted["title"]:
        extracted["title"] = title
    if "summary" not in extracted or not extracted["summary"]:
        extracted["summary"] = content[:120]
    return extracted


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


def auto_extract_fields(title: str, content: str) -> dict:
    """Synthesize structured fields from a title and text body.

    Delegates to ``fallback_extractor.fallback_extract`` for rule-based
    extraction.  Returns at minimum ``{"summary": title}``.
    """
    from .fallback_extractor import fallback_extract

    full_text = f"{title}\n{content}"
    extracted = fallback_extract(full_text)
    return {
        "title": extracted.get("title", title),
        "summary": extracted.get("summary", content[:120]),
        "event_time": extracted.get("event_time"),
        "location": extracted.get("location"),
        "organizer": extracted.get("organizer"),
    }
