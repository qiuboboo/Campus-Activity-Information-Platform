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


def _create_draft_poster(
    title: str,
    raw_text: str,
    source_url: str,
    created_by: int,
) -> Poster | None:
    existing = Poster.query.filter_by(source_url=source_url).first()
    if existing:
        return None

    summary = raw_text[:_MAX_SUMMARY_LENGTH].replace("\n", " ").strip()

    poster = Poster(
        title=title,
        raw_text=raw_text,
        summary=summary,
        status="draft",
        source_type="crawl",
        source_url=source_url,
        created_by=created_by,
    )
    db.session.add(poster)
    return poster


def crawl_data_source(data_source_id: int, user_id: int) -> dict:
    ds = get_data_source(data_source_id)
    if ds is None:
        return {"success": False, "error": "Data source not found"}

    if not ds.enabled:
        return {"success": False, "error": "Data source is disabled"}

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
    pages_succeeded = 0
    pages_failed = 0

    for url in detail_urls:
        try:
            detail_html = _fetch(url)
            raw_text = _parse_content(detail_html, ds.content_selector)
            raw_text = _clean_text(raw_text)

            if not raw_text:
                pages_failed += 1
                continue

            title = _extract_title_from_html(detail_html, url)
            poster = _create_draft_poster(title, raw_text, url, user_id)
            if poster:
                posters_created += 1
            pages_succeeded += 1
        except requests.RequestException:
            pages_failed += 1
        except Exception:
            pages_failed += 1

    db.session.commit()

    status = "failed" if pages_succeeded == 0 and pages_failed > 0 else "completed"
    finish_crawl_log(
        log,
        status,
        pages_found=len(detail_urls),
        pages_succeeded=pages_succeeded,
        pages_failed=pages_failed,
    )

    return {
        "success": True,
        "posters_created": posters_created,
        "pages_found": len(detail_urls),
        "pages_succeeded": pages_succeeded,
        "pages_failed": pages_failed,
    }
