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
    """Generate a self-contained HTML poster card with inline CSS.

    Returns a complete HTML document suitable for viewing standalone
    (e.g. opened in a new browser tab or embedded in an iframe).
    """
    time_str = event_time.strftime("%Y-%m-%d %H:%M") if event_time else ""

    css = """
    *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
    body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:#f0f5f3;display:flex;justify-content:center;align-items:center;min-height:100vh;padding:24px}
    .poster{max-width:520px;width:100%;background:#fff;border-radius:20px;overflow:hidden;box-shadow:0 12px 40px rgba(13,94,60,0.12)}
    .poster-header{background:linear-gradient(135deg,#0d5e3c,#27a66b);padding:32px 28px 24px;color:#fff}
    .poster-header .type-badge{display:inline-block;padding:4px 14px;border-radius:999px;background:rgba(255,255,255,0.2);font-size:13px;margin-bottom:14px}
    .poster-header h1{font-size:26px;font-weight:800;line-height:1.35}
    .poster-body{padding:24px 28px}
    .poster-meta{display:grid;grid-template-columns:1fr 1fr;gap:14px 20px;margin-bottom:22px}
    .poster-meta .field{display:grid;gap:4px}
    .poster-meta .field-label{font-size:12px;color:#889e93;text-transform:uppercase;letter-spacing:0.05em}
    .poster-meta .field-value{font-size:15px;color:#1a2e25;font-weight:600}
    .poster-summary{border-top:1px solid #e8f2ea;padding-top:18px;font-size:15px;color:#37423e;line-height:1.8}
    .poster-footer{padding:16px 28px;background:#f7fbf8;text-align:center;font-size:12px;color:#889e93}
    """.strip()

    meta_rows = ""
    if time_str:
        meta_rows += f'<div class="field"><span class="field-label">时间</span><span class="field-value">{escape(time_str)}</span></div>'
    if location:
        meta_rows += f'<div class="field"><span class="field-label">地点</span><span class="field-value">{escape(location)}</span></div>'
    if organizer:
        meta_rows += f'<div class="field"><span class="field-label">主办方</span><span class="field-value">{escape(organizer)}</span></div>'
    if activity_type:
        meta_rows += f'<div class="field"><span class="field-label">类型</span><span class="field-value">{escape(activity_type)}</span></div>'

    type_badge = f'<div class="type-badge">{escape(activity_type)}</div>' if activity_type else ""
    summary_html = f'<div class="poster-summary">{escape(summary)}</div>' if summary else ""

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)}</title>
<style>{css}</style>
</head>
<body>
<div class="poster">
  <header class="poster-header">
    {type_badge}
    <h1>{escape(title)}</h1>
  </header>
  <section class="poster-body">
    <div class="poster-meta">{meta_rows}</div>
    {summary_html}
  </section>
  <footer class="poster-footer">逸仙活动云 · Campus Activity Hub</footer>
</div>
</body>
</html>"""


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
    def text_value(key: str, default: str = "") -> str:
        value = payload.get(key)
        if value is None and fallback is not None:
            value = getattr(fallback, key, None)
        if value is None:
            value = default
        return str(value).strip()

    raw_text = text_value("raw_text")
    title = text_value("title") or _auto_title(raw_text)
    summary = text_value("summary") or _auto_summary(raw_text)
    location = text_value("location") or None
    organizer = text_value("organizer") or None
    source_type = text_value("source_type", "manual") or "manual"
    source_url = text_value("source_url") or None
    cover_image_url = text_value("cover_image_url") or None
    status = text_value("status", "draft") or "draft"

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
        "cover_image_url": cover_image_url,
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
