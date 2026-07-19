from datetime import datetime
<<<<<<< Updated upstream
from urllib.parse import urlparse
from urllib.parse import urljoin
=======
import re
import time
from urllib.parse import urldefrag, urljoin, urlparse
>>>>>>> Stashed changes

import requests
from bs4 import BeautifulSoup
from flask import current_app

from ..extensions import db
from ..models import Poster
from .data_source_service import (
    create_crawl_log,
    finish_crawl_log,
    get_data_source,
)
from .dedup_service import check_duplicates, generate_source_key, generate_fingerprint
from .quality_service import score_poster
from collections import defaultdict

from .security_service import (
    SecurityError,
    check_redirect_safety,
    mask_sensitive,
    rate_limit,
    reset_rate_limit,
    sanitise_crawled_text,
    validate_target_url,
)

# Track consecutive security failures per data source (process-local)
_security_failures: dict[int, int] = defaultdict(int)

_MAX_RESPONSE_BYTES = 2 * 1024 * 1024  # 2 MB
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
_MAX_TITLE_LENGTH = 200
_MAX_SUMMARY_LENGTH = 180
_ACTIVITY_KEYWORDS = (
    "活动", "讲座", "报告", "论坛", "会议", "竞赛", "比赛", "培训", "招新",
    "开放日", "宣讲", "研讨会", "学术交流", "seminar", "lecture", "forum",
    "competition", "workshop",
)
_DATE_OR_TIME_PATTERN = re.compile(
    r"(?:20\d{2}[年./-]\s*\d{1,2}[月./-]\s*\d{1,2}|\d{1,2}月\d{1,2}日|\d{1,2}:\d{2})"
)
_NON_CONTENT_SUFFIXES = (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip", ".rar")
_LISTING_TITLE_MARKERS = (
    "列表", "通知", "公告", "新闻", "资讯", "活动中心",
    "学术活动", "精品活动", "活动预告",
)


def _fetch(url: str, allowed_domains: list[str] | None = None) -> str:
    validate_target_url(url, allowed_domains)
    connect_timeout = current_app.config.get("CRAWL_CONNECT_TIMEOUT", 5)
    read_timeout = current_app.config.get("CRAWL_READ_TIMEOUT", 30)
    retries = max(0, current_app.config.get("CRAWL_REQUEST_RETRIES", 2))
    backoff = max(0, current_app.config.get("CRAWL_RETRY_BACKOFF_SECONDS", 1))

    for attempt in range(retries + 1):
        response = None
        try:
            response = requests.get(url, timeout=(connect_timeout, read_timeout), headers={"User-Agent": _USER_AGENT}, stream=True, allow_redirects=True)
            response.raise_for_status()
            if response.history:
                check_redirect_safety(url, response.url)
            content = b""
            for chunk in response.iter_content(chunk_size=8192, decode_unicode=False):
                content += chunk
                if len(content) > _MAX_RESPONSE_BYTES:
                    break
            return content.decode("utf-8", errors="replace")
        except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            retryable = isinstance(exc, (requests.Timeout, requests.ConnectionError)) or status == 429 or (status is not None and status >= 500)
            if not retryable or attempt >= retries:
                raise
            time.sleep(backoff * (2 ** attempt))
        finally:
            if response is not None:
                response.close()


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


def _discover_activity_links(html: str, base_url: str, allowed_domains: list[str]) -> list[str]:
    """Find likely activity detail pages on an unconfigured official homepage.

    A homepage is an index, not an activity.  We therefore only retain same-site
    links whose visible text or path looks event-related; each retained URL is
    subsequently fetched as its own candidate activity.
    """
    soup = BeautifulSoup(html, "html.parser")
    base_host = (urlparse(base_url).hostname or "").lower()
    ranked: list[tuple[int, str]] = []
    seen: set[str] = set()

    for anchor in soup.select("a[href]"):
        href = (anchor.get("href") or "").strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        absolute, _fragment = urldefrag(urljoin(base_url, href))
        parsed = urlparse(absolute)
        host = (parsed.hostname or "").lower()
        if parsed.scheme not in ("http", "https") or not host:
            continue
        if not any(host == domain.lower() or host.endswith("." + domain.lower()) for domain in allowed_domains):
            continue
        if absolute in seen or absolute.rstrip("/") == base_url.rstrip("/"):
            continue
        if parsed.path.lower().endswith(_NON_CONTENT_SUFFIXES):
            continue

        text = " ".join(anchor.get_text(" ", strip=True).split())
        haystack = f"{text} {parsed.path}".lower()
        keyword_hits = sum(keyword.lower() in haystack for keyword in _ACTIVITY_KEYWORDS)
        has_date = bool(_DATE_OR_TIME_PATTERN.search(text))
        is_detail_like = bool(re.search(r"(?:info|notice|news|article|content|view|detail|show|\d{4,})", parsed.path.lower()))
        # Do not crawl the site's generic navigation or section landing pages.
        if keyword_hits == 0 and not has_date:
            continue
        score = keyword_hits * 3 + (2 if has_date else 0) + (1 if is_detail_like else 0)
        if score < 3:
            continue
        seen.add(absolute)
        ranked.append((score, absolute))

    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [url for _score, url in ranked]


def _looks_like_activity_document(title: str, raw_text: str) -> bool:
    """Reject category/navigation pages that slipped through link discovery."""
    text = f"{title}\n{raw_text}".lower()
    keyword_hits = sum(keyword.lower() in text for keyword in _ACTIVITY_KEYWORDS)
    return keyword_hits > 0 and (bool(_DATE_OR_TIME_PATTERN.search(text)) or keyword_hits >= 2)


def _looks_like_listing_title(title: str) -> bool:
    """Identify short section names such as ``学术活动 | 学院名称``.

    This is only used together with the "multiple child detail links" check,
    so a real event with a short title is not discarded merely by its name.
    """
    normalized = " ".join((title or "").split()).lower()
    if any(marker in normalized for marker in _LISTING_TITLE_MARKERS):
        return True
    heading = re.split(r"[|｜]", normalized, maxsplit=1)[0].strip()
    return len(heading) <= 12 and heading.endswith(
        ("活动", "公告", "通知", "新闻", "资讯", "报告", "讲座", "论坛", "会议")
    )


def _normalise_lines(text: str) -> str:
    """Remove repeated navigation-like lines without flattening article paragraphs."""
    seen, lines = set(), []
    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        if not line or line in seen:
            continue
        lowered = line.lower()
        if len(line) < 60 and any(marker in lowered for marker in ("版权所有", "copyright", "网站地图", "联系我们", "设为首页", "繁體", "english")):
            continue
        seen.add(line)
        lines.append(line)
    return "\n".join(lines)


def _remove_page_noise(soup: BeautifulSoup) -> None:
    for tag in soup.select("script,style,noscript,svg,iframe,nav,header,footer,aside,form,button"):
        tag.decompose()
    for tag in soup.find_all(True):
        # Descendants of a decomposed container remain in BeautifulSoup's
        # iterator snapshot but no longer have an attrs mapping.
        if tag.attrs is None:
            continue
        # Some real-world pages use `class` without a value.  Treat it as an
        # empty list instead of allowing BeautifulSoup's `None` to abort the
        # entire crawl for this one node.
        classes = tag.get("class") or []
        hint = " ".join(classes) + " " + (tag.get("id") or "") + " " + (tag.get("role") or "")
        hint = hint.lower()
        if any(word in hint for word in ("nav", "menu", "footer", "header", "sidebar", "breadcrumb", "recommend", "related", "share", "copyright", "pagination")):
            tag.decompose()


def _content_score(element) -> int:
    text = element.get_text(" ", strip=True)
    if not text:
        return -1
    links = " ".join(link.get_text(" ", strip=True) for link in element.select("a"))
    link_penalty = min(len(text), len(links))
    paragraphs = len(element.select("p,br"))
    signals = sum(keyword.lower() in text.lower() for keyword in _ACTIVITY_KEYWORDS)
    return len(text) - link_penalty * 2 + paragraphs * 80 + signals * 120


def _parse_content(html: str, content_selector: str | None) -> str:
    """Extract article content, preferring a source selector then a generic main block."""
    soup = BeautifulSoup(html, "html.parser")
    _remove_page_noise(soup)
    candidates = soup.select(content_selector) if content_selector else []
    if not candidates:
        candidates = soup.select("article, main, [role='main'], .article-content, .article_content, .news-content, .content, .detail, .article")
    if not candidates:
        candidates = [soup.body or soup]
    main = max(candidates, key=_content_score)
    return _normalise_lines(main.get_text(separator="\n", strip=True))


def _summarize_activity(raw_text: str) -> str:
    """Produce a concise, event-oriented summary rather than page-leading boilerplate."""
    paragraphs = [line.strip() for line in raw_text.splitlines() if line.strip()]
    relevant = [line for line in paragraphs if _DATE_OR_TIME_PATTERN.search(line) or any(keyword.lower() in line.lower() for keyword in _ACTIVITY_KEYWORDS)]
    source = " ".join(relevant or paragraphs)
    sentences = re.split(r"(?<=[。！？!?\.])\s*", source)
    summary = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        candidate = f"{summary} {sentence}".strip()
        if len(candidate) > _MAX_SUMMARY_LENGTH:
            break
        summary = candidate
    return (summary or source)[:_MAX_SUMMARY_LENGTH].rstrip("，、；; ")


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
    val = value.strip()
    if val.endswith("Z"):
        val = val[:-1]
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

    h1 = soup.select_one("h1")
    if h1:
        title_text = h1.get_text(strip=True)
        if title_text:
            fields["title"] = title_text[:_MAX_TITLE_LENGTH]

    time_tag = soup.select_one(".field-date-period time[datetime]") or soup.select_one("time[datetime]")
    if time_tag:
        dt_str = time_tag["datetime"]
        parsed = _parse_datetime(dt_str)
        if parsed:
            fields["event_time"] = parsed

    loc_tag = soup.select_one(".field-event-location .field-item")
    if loc_tag:
        loc_text = loc_tag.get_text(strip=True)
        if loc_text:
            fields["location"] = loc_text

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
    existing_by_url = Poster.query.filter_by(source_url=source_url).first()
    if existing_by_url:
        return None, True

    dup = check_duplicates(title, source_url, event_time, location, exclude_id=None)
    is_duplicate = dup["is_duplicate"]

    poster = Poster(
        title=title,
        raw_text=raw_text,
        summary=_summarize_activity(raw_text),
        event_time=event_time,
        location=location,
        organizer=organizer,
        status="draft",
        source_type="crawl",
        source_url=source_url,
        created_by=created_by,
    )

    source_key = generate_source_key(source_url)
    poster.source_fingerprint = source_key or generate_fingerprint(title, event_time, location)
    if is_duplicate:
        poster.duplicate_group_key = dup["duplicate_group_key"]

    quality, notes_list = score_poster(
        poster,
        is_suspected_duplicate=is_duplicate,
        is_official_source=is_official,
    )
    poster.quality_score = quality
    poster.quality_notes = "; ".join(notes_list) if notes_list else None

    db.session.add(poster)
    return poster, is_duplicate


def collect_crawl_candidates(data_source_id: int, limit: int = 10) -> list[dict]:
    """Execute crawl + extraction without creating Poster records.

    Returns a list of candidate dicts for frontend preview.
    """
    source = DataSource.query.get(data_source_id)
    if source is None:
        raise ValueError(f"DataSource {data_source_id} not found")

    now_iso = datetime.utcnow().isoformat()

    # 1) Fetch list page
    list_html = _fetch(source.base_url)
    page_urls = _parse_list_links(list_html, source.base_url, source.list_selector)

    candidates: list[dict] = []
    for url in page_urls[:limit]:
        try:
            html = _fetch(url)
            raw_text = _parse_content(html, source.content_selector)
            raw_text = _clean_text(raw_text)
            raw_text = sanitise_crawled_text(raw_text)
            raw_text = mask_sensitive(raw_text)

            fields = _extract_structured_fields(raw_text, url)

            # Check duplicates without creating poster
            dup = check_duplicates(
                fields.get("title", ""), url,
                fields.get("event_time"), fields.get("location"),
                exclude_id=None,
            )

            candidates.append({
                "title": fields.get("title", ""),
                "raw_text": raw_text,
                "summary": raw_text[:_MAX_SUMMARY_LENGTH].replace("\n", " ").strip(),
                "event_time": fields.get("event_time"),
                "location": fields.get("location") or "",
                "organizer": fields.get("organizer") or "",
                "source_url": url,
                "is_duplicate": dup["is_duplicate"],
                "duplicate_group_key": dup.get("duplicate_group_key", ""),
            })
        except Exception:
            continue

    candidates.sort(key=lambda c: c["is_duplicate"])  # non-duplicates first
    return candidates


def crawl_data_source(data_source_id: int, user_id: int) -> dict:
    ds = get_data_source(data_source_id)
    if ds is None:
        return {"success": False, "error": "Data source not found"}

    if not ds.enabled:
        return {"success": False, "error": "Data source is disabled"}

    is_official = ds.source_level == "official"
    allowed_domains = ds.get_allowed_domains()
    if ds.crawl_mode == "basic" and not allowed_domains:
        hostname = urlparse(ds.base_url).hostname
        if hostname:
            allowed_domains = [hostname]
    interval = ds.request_interval or current_app.config.get("CRAWL_REQUEST_INTERVAL", 2)
    max_pages = current_app.config.get("CRAWL_MAX_PAGES", 50)

    # Older data sources were created before allowed_domains became required.
    # Safely migrate them to the exact host in their configured base URL.
    if ds.crawl_mode == "basic" and not allowed_domains:
        host = urlparse(ds.base_url).hostname
        if not host:
            return {"success": False, "error": "base_url does not contain a valid allowed domain"}
        ds.allowed_domains = host
        db.session.commit()
        allowed_domains = [host]

    log = create_crawl_log(data_source_id)

    try:
        rate_limit(data_source_id, interval)
        html = _fetch(ds.base_url, allowed_domains)
    except (SecurityError, requests.RequestException) as e:
        finish_crawl_log(log, "failed", message=f"Fetch error: {e}")
        return {"success": False, "error": str(e)}

    auto_discovery = not bool(ds.list_selector)
    if ds.list_selector:
        detail_urls = _parse_list_links(html, ds.base_url, ds.list_selector)
    else:
        detail_urls = _discover_activity_links(html, ds.base_url, allowed_domains)

    if not detail_urls:
        finish_crawl_log(log, "completed", message="No links found", pages_found=0)
        return {"success": True, "posters_created": 0}

    # Enforce max pages
    if len(detail_urls) > max_pages:
        detail_urls = detail_urls[:max_pages]
    queued_urls = set(detail_urls)

    posters_created = 0
    duplicates_skipped = 0
    pages_succeeded = 0
    pages_failed = 0
    pages_rejected = 0
    quality_scores = []
    failure_samples: list[str] = []

    for url in detail_urls:
        try:
            rate_limit(data_source_id, interval)
            detail_html = _fetch(url, allowed_domains)
            raw_text = _parse_content(detail_html, ds.content_selector)
            raw_text = _clean_text(raw_text)
            # Security: sanitise and mask sensitive data
            raw_text = sanitise_crawled_text(raw_text)
            raw_text = mask_sensitive(raw_text)

            if not raw_text:
                pages_failed += 1
                continue

            structured = _extract_structured_fields(detail_html)
            title = structured.get("title") or _extract_title_from_html(detail_html, url)
            child_urls = _discover_activity_links(detail_html, url, allowed_domains) if auto_discovery else []
            is_listing_page = len(child_urls) >= 2 and (
                not _looks_like_activity_document(title, raw_text)
                or _looks_like_listing_title(title)
            )
            if auto_discovery and is_listing_page:
                # A homepage often links to an event/notice category first.
                # Expand that listing one level, but never turn the listing
                # page itself into a single false activity.
                for child_url in child_urls:
                    if child_url not in queued_urls and len(detail_urls) < max_pages:
                        detail_urls.append(child_url)
                        queued_urls.add(child_url)
                pages_rejected += 1
                pages_succeeded += 1
                continue
            if auto_discovery and not _looks_like_activity_document(title, raw_text):
                pages_rejected += 1
                pages_succeeded += 1
                continue
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
        except SecurityError as e:
            pages_failed += 1
            if len(failure_samples) < 3:
                failure_samples.append(mask_sensitive(str(e)))
            # Auto-disable data source after 3 consecutive security failures
            _security_failures[data_source_id] += 1
            if _security_failures[data_source_id] >= 3:
                ds.enabled = False
                ds.last_error_message = f"Auto-disabled after {_security_failures[data_source_id]} consecutive security violations"
        except requests.RequestException as e:
            pages_failed += 1
            if len(failure_samples) < 3:
                failure_samples.append(mask_sensitive(str(e)))
        except Exception as e:
            pages_failed += 1
            if len(failure_samples) < 3:
                failure_samples.append(f"{type(e).__name__}: {mask_sensitive(str(e))}")

    db.session.commit()

    avg_quality = round(sum(quality_scores) / len(quality_scores), 1) if quality_scores else None

    status = "failed" if pages_succeeded == 0 and pages_failed > 0 else "completed"
    if status == "failed":
        message = "所有详情页抓取失败"
        if failure_samples:
            message += f"：{failure_samples[0]}"
    elif duplicates_skipped and not posters_created:
        message = f"抓取完成；{duplicates_skipped} 条均为已有活动，未新建草稿"
    elif pages_failed:
        message = f"抓取完成；{pages_failed} 页失败，已新建 {posters_created} 条草稿"
    else:
        message = f"抓取完成；新建 {posters_created} 条草稿"
    finish_crawl_log(
        log,
        status,
        message=message,
        pages_found=len(detail_urls),
        pages_succeeded=pages_succeeded,
        pages_failed=pages_failed,
        duplicates_skipped=duplicates_skipped,
        drafts_created=posters_created,
        average_quality_score=avg_quality,
    )

    if pages_succeeded > 0:
        ds.last_success_at = datetime.utcnow()
    if pages_failed > 0:
        ds.last_failure_at = datetime.utcnow()
    db.session.commit()

    reset_rate_limit(data_source_id)
    _security_failures.pop(data_source_id, None)

    return {
        "success": True,
        "posters_created": posters_created,
        "duplicates_skipped": duplicates_skipped,
        "average_quality_score": avg_quality,
        "pages_found": len(detail_urls),
        "pages_succeeded": pages_succeeded,
        "pages_failed": pages_failed,
        "pages_rejected": pages_rejected,
    }


# ---------------------------------------------------------------------------
# MCP-based crawling (e.g. Xiaohongshu)
# ---------------------------------------------------------------------------


def crawl_mcp_source(data_source_id: int, user_id: int) -> dict:
    """Crawl a data source configured with ``crawl_mode=mcp``.

    Uses the MCP client instead of HTTP requests.  The ``base_url`` field
    of the data source is used as the MCP server name (e.g. ``xiaohongshu``).
    """
    ds = get_data_source(data_source_id)
    if ds is None:
        return {"success": False, "error": "Data source not found"}
    if not ds.enabled:
        return {"success": False, "error": "Data source is disabled"}
    if ds.crawl_mode != "mcp":
        return {"success": False, "error": f"Expected crawl_mode=mcp, got {ds.crawl_mode}"}

    from .mcp_service import call_tool

    is_official = ds.source_level == "official"
    log = create_crawl_log(data_source_id)

    try:
        # The data source name serves as the MCP server name
        server_name = ds.name.strip().lower().replace(" ", "_")
        # Use base_url as the search query or fall back to data source notes
        query = ds.notes or "校园活动"
        result = call_tool(server_name, "search_notes", {"query": query})
        if result is None:
            raise RuntimeError(f"MCP call to '{server_name}' returned no result")
    except Exception as e:
        finish_crawl_log(log, "failed", message=f"MCP crawl error: {e}")
        return {"success": False, "error": str(e)}

    # Normalise results — different MCP servers return different shapes
    raw_items = []
    if isinstance(result, list):
        raw_items = result
    elif isinstance(result, dict):
        raw_items = result.get("notes", result.get("results", result.get("items", [result])))

    if not raw_items:
        finish_crawl_log(log, "completed", message="No items found", pages_found=0)
        return {"success": True, "posters_created": 0}

    posters_created = 0
    duplicates_skipped = 0
    pages_succeeded = 0
    pages_failed = 0
    quality_scores = []

    for item in raw_items[:50]:
        try:
            title = (item.get("title") or item.get("name") or "未命名活动")[:_MAX_TITLE_LENGTH]
            raw_text = item.get("content") or item.get("description") or item.get("text") or ""
            url = item.get("url") or item.get("link") or ""
            event_time_str = item.get("time") or item.get("date") or item.get("event_time")

            # Use AI to extract structured fields if available
            from .ai_service import extract_from_text

            ai_fields = extract_from_text(raw_text) if raw_text else {}

            poster, is_dup = _create_draft_poster(
                title,
                raw_text[:10000],
                url or f"mcp://{server_name}/{item.get('id', '')}",
                user_id,
                event_time=ai_fields.get("event_time") or _parse_datetime(event_time_str) if event_time_str else None,
                location=ai_fields.get("location") or item.get("location"),
                organizer=ai_fields.get("organizer") or item.get("author") or item.get("organizer"),
                is_official=is_official,
            )
            if poster:
                posters_created += 1
                quality_scores.append(poster.quality_score or 0)
            if is_dup:
                duplicates_skipped += 1
            pages_succeeded += 1
        except Exception:
            pages_failed += 1

    db.session.commit()

    avg_quality = round(sum(quality_scores) / len(quality_scores), 1) if quality_scores else None
    status = "failed" if pages_succeeded == 0 else "completed"
    finish_crawl_log(
        log,
        status,
        pages_found=len(raw_items),
        pages_succeeded=pages_succeeded,
        pages_failed=len(raw_items) - pages_succeeded,
        duplicates_skipped=duplicates_skipped,
        drafts_created=posters_created,
        average_quality_score=avg_quality,
    )

    if pages_succeeded > 0:
        ds.last_success_at = datetime.utcnow()
    if pages_succeeded == 0:
        ds.last_failure_at = datetime.utcnow()
    db.session.commit()

    return {
        "success": True,
        "posters_created": posters_created,
        "duplicates_skipped": duplicates_skipped,
        "average_quality_score": avg_quality,
        "pages_found": len(raw_items),
        "pages_succeeded": pages_succeeded,
    }
