from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from ..extensions import db
from ..models import Poster
from .data_source_service import (
    create_crawl_log,
    finish_crawl_log,
    get_data_source,
)
from .dedup_service import check_duplicates, generate_source_key, generate_fingerprint
from .quality_service import score_poster

_REQUEST_TIMEOUT = 10
_MAX_RESPONSE_BYTES = 2 * 1024 * 1024  # 2 MB
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
_MAX_TITLE_LENGTH = 200
_MAX_SUMMARY_LENGTH = 500


def _fetch(url: str) -> str:
    resp = requests.get(
        url,
        timeout=_REQUEST_TIMEOUT,
        headers={"User-Agent": _USER_AGENT},
        stream=True,
    )
    resp.raise_for_status()

    content = b""
    for chunk in resp.iter_content(chunk_size=8192, decode_unicode=False):
        content += chunk
        if len(content) > _MAX_RESPONSE_BYTES:
            break
    return content.decode("utf-8", errors="replace")


def _parse_list_links(html: str, base_url: str, list_selector: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for tag in soup.select(list_selector):
        href = tag.get("href") or tag.get("src") or ""
        if href:
            absolute = urljoin(base_url, href)
            if absolute not in links:
                links.append(absolute)
    return links


def _parse_content(html: str, content_selector: str | None) -> str:
    soup = BeautifulSoup(html, "html.parser")
    if content_selector:
        elements = soup.select(content_selector)
        text = "\n".join(el.get_text(separator="\n", strip=True) for el in elements)
    else:
        text = soup.get_text(separator="\n", strip=True)

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def _clean_text(text: str) -> str:
    import re

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_title_from_html(html: str, url: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    if soup.title and soup.title.string:
        return soup.title.string.strip()[:_MAX_TITLE_LENGTH]
    from urllib.parse import unquote

    filename = url.rstrip("/").split("/")[-1]
    return unquote(filename).replace("_", " ").replace("-", " ")[:_MAX_TITLE_LENGTH]


def _parse_datetime(value: str) -> datetime | None:
    # Handle ISO 8601: strip trailing Z, strip fractional seconds
    val = value.strip()
    if val.endswith("Z"):
        val = val[:-1]
    # Remove trailing +00:00 timezone offset for simplicity
    if "+" in val:
        val = val.split("+")[0]
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(val, fmt)
        except ValueError:
            continue
    return None


def _extract_structured_fields(html: str) -> dict:
    """Extract structured fields (title, event_time, location, organizer) from a detail page."""
    soup = BeautifulSoup(html, "html.parser")
    fields: dict = {}

    # Title from <h1> (preferred over <title> for article pages)
    h1 = soup.select_one("h1")
    if h1:
        title_text = h1.get_text(strip=True)
        if title_text:
            fields["title"] = title_text[:_MAX_TITLE_LENGTH]

    # Event time from <time datetime="..."> inside .field-date-period
    time_tag = soup.select_one(".field-date-period time[datetime]") or soup.select_one("time[datetime]")
    if time_tag:
        dt_str = time_tag["datetime"]
        parsed = _parse_datetime(dt_str)
        if parsed:
            fields["event_time"] = parsed

    # Location from .field-event-location .field-item
    loc_tag = soup.select_one(".field-event-location .field-item")
    if loc_tag:
        loc_text = loc_tag.get_text(strip=True)
        if loc_text:
            fields["location"] = loc_text

    # Speaker / organizer from .field-speaker .field-item
    speaker_tag = soup.select_one(".field-speaker .field-item")
    if speaker_tag:
        speaker_text = speaker_tag.get_text(strip=True)
        if speaker_text:
            fields["organizer"] = speaker_text

    return fields


def _create_draft_poster(
    title: str,
    raw_text: str,
    source_url: str,
    created_by: int,
    event_time: datetime | None = None,
    location: str | None = None,
    organizer: str | None = None,
    is_official: bool = False,
) -> tuple[Poster | None, bool]:
    """Create a draft poster. Returns (poster, is_duplicate).

    Exact URL duplicates are skipped (returns None).
    Suspected content duplicates (same fingerprint, different source) are created
    with duplicate_group_key set.
    """
    # Check exact URL duplicate first — skip entirely
    existing_by_url = Poster.query.filter_by(source_url=source_url).first()
    if existing_by_url:
        return None, True

    # Content-based dedup check
    dup = check_duplicates(title, source_url, event_time, location, exclude_id=None)
    is_duplicate = dup["is_duplicate"]

    poster = Poster(
        title=title,
        raw_text=raw_text,
        summary=raw_text[:_MAX_SUMMARY_LENGTH].replace("\n", " ").strip(),
        event_time=event_time,
        location=location,
        organizer=organizer,
        status="draft",
        source_type="crawl",
        source_url=source_url,
        created_by=created_by,
    )

    # Set dedup fingerprint
    source_key = generate_source_key(source_url)
    poster.source_fingerprint = source_key or generate_fingerprint(title, event_time, location)
    if is_duplicate:
        poster.duplicate_group_key = dup["duplicate_group_key"]

    # Quality scoring
    quality, notes_list = score_poster(
        poster,
        is_suspected_duplicate=is_duplicate,
        is_official_source=is_official,
    )
    poster.quality_score = quality
    poster.quality_notes = "; ".join(notes_list) if notes_list else None

    db.session.add(poster)
    return poster, is_duplicate


def crawl_data_source(data_source_id: int, user_id: int) -> dict:
    ds = get_data_source(data_source_id)
    if ds is None:
        return {"success": False, "error": "Data source not found"}

    if not ds.enabled:
        return {"success": False, "error": "Data source is disabled"}

    is_official = ds.source_level == "official"
    log = create_crawl_log(data_source_id)

    try:
        html = _fetch(ds.base_url)
    except requests.RequestException as e:
        finish_crawl_log(log, "failed", message=f"HTTP fetch error: {e}")
        return {"success": False, "error": str(e)}

    if ds.list_selector:
        detail_urls = _parse_list_links(html, ds.base_url, ds.list_selector)
    else:
        detail_urls = [ds.base_url]

    if not detail_urls:
        finish_crawl_log(log, "completed", message="No links found", pages_found=0)
        return {"success": True, "posters_created": 0}

    posters_created = 0
    duplicates_skipped = 0
    pages_succeeded = 0
    pages_failed = 0
    quality_scores = []

    for url in detail_urls:
        try:
            detail_html = _fetch(url)
            raw_text = _parse_content(detail_html, ds.content_selector)
            raw_text = _clean_text(raw_text)

            if not raw_text:
                pages_failed += 1
                continue

            structured = _extract_structured_fields(detail_html)
            title = structured.get("title") or _extract_title_from_html(detail_html, url)
            poster, is_dup = _create_draft_poster(
                title,
                raw_text,
                url,
                user_id,
                event_time=structured.get("event_time"),
                location=structured.get("location"),
                organizer=structured.get("organizer"),
                is_official=is_official,
            )
            if poster:
                posters_created += 1
                quality_scores.append(poster.quality_score or 0)
            if is_dup:
                duplicates_skipped += 1
            pages_succeeded += 1
        except requests.RequestException:
            pages_failed += 1
        except Exception:
            pages_failed += 1

    db.session.commit()

    avg_quality = round(sum(quality_scores) / len(quality_scores), 1) if quality_scores else None

    status = "failed" if pages_succeeded == 0 and pages_failed > 0 else "completed"
    finish_crawl_log(
        log,
        status,
        pages_found=len(detail_urls),
        pages_succeeded=pages_succeeded,
        pages_failed=pages_failed,
        duplicates_skipped=duplicates_skipped,
        drafts_created=posters_created,
        average_quality_score=avg_quality,
    )

    # Update data source timestamps
    from datetime import datetime
    if pages_succeeded > 0:
        ds.last_success_at = datetime.utcnow()
    if pages_failed > 0:
        ds.last_failure_at = datetime.utcnow()
    db.session.commit()

    return {
        "success": True,
        "posters_created": posters_created,
        "duplicates_skipped": duplicates_skipped,
        "average_quality_score": avg_quality,
        "pages_found": len(detail_urls),
        "pages_succeeded": pages_succeeded,
        "pages_failed": pages_failed,
    }
