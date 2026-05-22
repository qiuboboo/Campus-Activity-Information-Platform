"""Sogou WeChat Search — search public WeChat articles and extract content."""

import re
import time
from datetime import datetime, timezone
from urllib.parse import quote

import requests
from flask import current_app
from lxml import html

from .security_service import mask_sensitive, sanitise_crawled_text

_REQUEST_TIMEOUT = 15
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0"
)

# Sogou anti-spider patterns
_ANTI_SPIDER_PATHS = ("antispider", "seccoderight")


def _is_antispider(response: requests.Response) -> bool:
    url_lower = response.url.lower()
    body_lower = response.text.lower()
    for path in _ANTI_SPIDER_PATHS:
        if path in url_lower or path in body_lower:
            return True
    return "anti.min.css" in body_lower


def _convert_time(ts_str: str) -> str:
    """Convert Sogou's timeConvert(timestamp) to ISO datetime string."""
    match = re.search(r"(\d{10,})", ts_str)
    if match:
        dt = datetime.fromtimestamp(int(match.group(1)), tz=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return ts_str


def sogou_search(query: str, page: int = 1) -> list[dict]:
    """Search WeChat articles via Sogou WeChat search.

    Returns a list of dicts with keys:
        title, sogou_url, publish_time, source_account
    """
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": f"https://weixin.sogou.com/weixin?query={quote(query)}",
        "User-Agent": _USER_AGENT,
    }
    params = {
        "type": "2",
        "s_from": "input",
        "query": query,
        "ie": "utf8",
        "page": page,
        "_sug_": "n",
        "_sug_type_": "",
    }

    resp = requests.get(
        "https://weixin.sogou.com/weixin",
        params=params,
        headers=headers,
        timeout=_REQUEST_TIMEOUT,
    )
    if resp.status_code != 200:
        return []

    if _is_antispider(resp):
        return []

    tree = html.fromstring(resp.text)
    titles = tree.xpath("//a[contains(@id, 'sogou_vr_11002601_title_')]")
    time_elems = tree.xpath(
        "//li[contains(@id, 'sogou_vr_11002601_box_')]"
        "/div[@class='txt-box']/div[@class='s-p']/span[@class='s2']"
    )

    results = []
    for title_elem, time_elem in zip(titles, time_elems):
        sogou_url = title_elem.get("href", "")
        if sogou_url and not sogou_url.startswith("http"):
            sogou_url = "https://weixin.sogou.com" + sogou_url

        results.append({
            "title": title_elem.text_content().strip(),
            "sogou_url": sogou_url,
            "publish_time": _convert_time(time_elem.text_content().strip()),
        })

    return results


def sogou_search_all(query: str, max_pages: int = 10) -> list[dict]:
    """Search all pages of results (auto-pagination)."""
    all_results = []
    for page in range(1, max_pages + 1):
        results = sogou_search(query, page=page)
        if not results:
            break
        all_results.extend(results)
        if page < max_pages:
            time.sleep(1)
    return all_results


def _get_sogou_cookies() -> dict[str, str]:
    """Parse SOGOU_COOKIES from config into a dict for requests."""
    try:
        raw = current_app.config.get("SOGOU_COOKIES", "")
    except RuntimeError:
        return {}
    if not raw:
        return {}
    cookies = {}
    for part in raw.split(";"):
        part = part.strip()
        if "=" in part:
            key, _, val = part.partition("=")
            cookies[key.strip()] = val.strip()
    return cookies


def resolve_real_url(sogou_url: str) -> str:
    """Resolve the real mp.weixin.qq.com URL from a Sogou redirect link."""
    headers = {
        "Accept": "text/html,*/*;q=0.9",
        "User-Agent": _USER_AGENT,
    }
    cookies = _get_sogou_cookies()
    try:
        resp = requests.get(sogou_url, headers=headers, cookies=cookies, timeout=_REQUEST_TIMEOUT)
        if _is_antispider(resp):
            return ""

        script = resp.text
        # The real URL is constructed via JS: url += '...' fragments
        parts = re.findall(r"url\s*\+=\s*'([^']*)'", script)
        if not parts:
            return ""

        full_url = "".join(parts).replace("@", "")
        if full_url and not full_url.startswith("http"):
            full_url = "https://mp." + full_url
        return full_url if "mp.weixin.qq.com" in full_url else ""
    except requests.RequestException:
        return ""


def fetch_article_content(real_url: str) -> str:
    """Extract clean text content from a WeChat article page."""
    headers = {
        "Accept": "text/html,*/*;q=0.9",
        "User-Agent": _USER_AGENT,
        "Accept-Language": "zh-CN,zh;q=0.9",
    }
    try:
        resp = requests.get(real_url, headers=headers, timeout=_REQUEST_TIMEOUT)
        resp.raise_for_status()
        tree = html.fromstring(resp.text)
        nodes = tree.xpath("//div[@id='js_content']//text()")
        text = "\n".join(t.strip() for t in nodes if t.strip())
        return sanitise_crawled_text(mask_sensitive(text))
    except requests.RequestException:
        return ""


def search_and_fetch(query: str, max_results: int = 10) -> list[dict]:
    """One-stop: search → resolve URL → fetch content (best-effort)."""
    results = sogou_search(query)
    articles = []
    for r in results[:max_results]:
        real_url = resolve_real_url(r["sogou_url"])
        content = ""
        if real_url:
            try:
                content = fetch_article_content(real_url)
            except Exception:
                pass  # content fetch is best-effort
        articles.append({
            "title": r["title"],
            "publish_time": r["publish_time"],
            "source_url": real_url or r["sogou_url"],
            "content": content,
        })
    return articles
