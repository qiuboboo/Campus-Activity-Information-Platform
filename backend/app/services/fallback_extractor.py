"""Fallback Extractor — rule-based activity field extraction when LLM is unavailable.

Provides regex-based extraction for title, event time, location, organizer,
and summary.  Works without any external API call.  Used as a degradation
layer when ``ai_service.extract_from_text()`` cannot reach the LLM.

Usage::

    from .fallback_extractor import fallback_extract

    fields = fallback_extract("活动原文...")
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any


# ---------------------------------------------------------------------------
# Title
# ---------------------------------------------------------------------------

def _extract_title(text: str) -> str | None:
    """Take the first non-empty line as title, up to 80 characters."""
    for line in text.strip().splitlines():
        line = line.strip()
        if line:
            return line[:80]
    return None


# ---------------------------------------------------------------------------
# Event time
# ---------------------------------------------------------------------------

_TIME_PATTERNS: list[tuple[str, str]] = [
    # "2025年5月10日 19:00" or "2025年5月10日晚7点"
    (r"(?P<y>\d{4})\s*年\s*(?P<mo>\d{1,2})\s*月\s*(?P<d>\d{1,2})\s*[日号]",
     "%Y-%m-%d"),
    # "5月10日 19:00"
    (r"(?P<mo>\d{1,2})\s*月\s*(?P<d>\d{1,2})\s*[日号]",
     "%m-%d"),
    # ISO formats: 2025-05-10, 2025/05/10
    (r"(?P<y>\d{4})[-/](?P<mo>\d{1,2})[-/](?P<d>\d{1,2})",
     "%Y-%m-%d"),
]

_TIME_APPENDIX_PATTERNS: list[tuple[str, bool]] = [
    # 晚7点, 晚上7点, 晚7:00 → 19:00 (convert_12h=True)
    (r"(?:晚[上]?)\s*(\d{1,2})[: ]?(\d{2})\s*(?:点|分)?", True),
    (r"(?:晚[上]?)\s*(\d{1,2})\s*点\s*(?:(\d{1,2})\s*分)?", True),
    # 14:00, 14点30分 → 24h format
    (r"(\d{1,2})[: ](\d{2})\s*(?:[点时分])?", False),
    # 下午2点, 下午2:30 → pm conversion
    (r"(?:下[午]?)\s*(\d{1,2})[: ]?(\d{2})\s*(?:点|分)?", True),
    (r"(?:下[午]?)\s*(\d{1,2})\s*点\s*(?:(\d{1,2})\s*分)?", True),
]


def _extract_event_time(text: str) -> datetime | None:
    """Try to extract a date (and optionally time) from *text*."""
    found_date: str | None = None
    found_tm: tuple[int, int] | None = None

    # 1) Match date patterns
    for pattern, _ in _TIME_PATTERNS:
        m = re.search(pattern, text)
        if m:
            found_date = m.group(0)
            break

    if not found_date:
        return None

    # 2) Try to parse the date part
    parsed: datetime | None = None
    for pattern, fmt in _TIME_PATTERNS:
        m = re.search(pattern, text)
        if m:
            try:
                groups = m.groupdict()
                if "y" in groups:
                    parsed = datetime(
                        int(groups["y"]), int(groups["mo"]), int(groups["d"])
                    )
                else:
                    # Ambiguous month-day: use current year
                    now = datetime.now()
                    parsed = datetime(now.year, int(groups["mo"]), int(groups["d"]))
                break
            except (ValueError, KeyError):
                continue

    if parsed is None:
        return None

    # 3) Look for time appendix nearby (within 40 chars after the date)
    after_date = text[m.end():m.end() + 40]
    for time_pat, convert_12h in _TIME_APPENDIX_PATTERNS:
        tm = re.search(time_pat, after_date)
        if tm:
            hour = int(tm.group(1))
            minute = int(tm.group(2) if tm.lastindex and tm.lastindex >= 2 else 0)
            if convert_12h and 1 <= hour <= 11:
                hour += 12  # 晚7点 → 19:00
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                found_tm = (hour, minute)
            break

    if found_tm:
        parsed = parsed.replace(hour=found_tm[0], minute=found_tm[1])

    return parsed


# ---------------------------------------------------------------------------
# Location
# ---------------------------------------------------------------------------

_LOCATION_PATTERNS = [
    r"在\s*(?P<loc>[^，。,由]{2,40}?)\s*(?:举行|举办|召开|开展|开幕)",
    r"于\s*(?P<loc>[^，。,由]{2,40}?)\s*(?:举行|举办|召开|开展|开幕)",
    r"(?:地点|场地|会场)[：:\s]+(?P<loc>[^，。,\s]{2,40})",
    r"(?:位于|在)\s*(?P<loc>[^，。,由]{2,40}?(?:礼堂|厅|馆|中心|广场|场|楼|教室|报告厅))",
]


def _extract_location(text: str) -> str | None:
    """Extract location using pattern matching."""
    for pat in _LOCATION_PATTERNS:
        m = re.search(pat, text)
        if m:
            loc = m.group("loc").strip()
            if len(loc) >= 2:
                return loc[:100]
    return None


# ---------------------------------------------------------------------------
# Organizer
# ---------------------------------------------------------------------------

_ORGANIZER_PATTERNS = [
    r"(?:由|交[由给])\s*(?P<org>[^，。,]{2,30}?)\s*(?:主办|承办|组织|协办|举办)",
    r"(?:主办方|组织者|承办方)[：:\s]+(?P<org>[^，。,\s]{2,30})",
    r"(?P<org>[^，。,\s]{2,30}(?:团委|学生会|协会|社团|学院|系|部|处|中心|办公室))\s*(?:主办|承办|组织|协办)",
]


def _extract_organizer(text: str) -> str | None:
    """Extract organizer using pattern matching."""
    for pat in _ORGANIZER_PATTERNS:
        m = re.search(pat, text)
        if m:
            org = m.group("org").strip()
            if len(org) >= 2:
                return org[:80]
    return None


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def _extract_summary(text: str) -> str | None:
    """Take first ~120 characters of meaningful text as summary."""
    cleaned = " ".join(text.strip().split())
    if not cleaned:
        return None
    return cleaned[:120]


# ---------------------------------------------------------------------------
# Tags (keyword-based)
# ---------------------------------------------------------------------------

_TAG_KEYWORDS: list[tuple[str, str]] = [
    ("科技", "科技"),
    ("文化节", "校园文化"),
    ("讲座", "讲座"),
    ("论坛", "论坛"),
    ("竞赛", "竞赛"),
    ("比赛", "竞赛"),
    ("招聘", "招聘"),
    ("志愿", "志愿服务"),
    ("开幕式", "开幕式"),
    ("闭幕式", "闭幕式"),
    ("晚会", "晚会"),
    ("展览", "展览"),
    ("演出", "演出"),
    ("体育", "体育"),
    ("运动会", "体育"),
    ("宣讲", "宣讲"),
    ("培训", "培训"),
    ("工作坊", "工作坊"),
]


def _extract_tags(text: str) -> list[str]:
    """Extract tags by matching known keyword patterns."""
    found: list[str] = []
    seen: set[str] = set()
    for keyword, tag in _TAG_KEYWORDS:
        if keyword in text and tag not in seen:
            found.append(tag)
            seen.add(tag)
    return found


# ---------------------------------------------------------------------------
# Activity type
# ---------------------------------------------------------------------------

def _extract_activity_type(tags: list[str]) -> str | None:
    """Map tags back to an activity type."""
    type_map = {
        "晚会": "晚会",
        "讲座": "讲座",
        "论坛": "论坛",
        "竞赛": "竞赛",
        "招聘": "招聘",
        "展览": "展览",
        "体育": "体育",
        "志愿服务": "其他",
        "开幕式": "其他",
        "工作坊": "其他",
        "校园文化": "其他",
        "宣讲": "讲座",
        "培训": "讲座",
    }
    for tag in tags:
        if tag in type_map:
            return type_map[tag]
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def fallback_extract(raw_text: str) -> dict[str, Any]:
    """Extract structured activity fields using only rule-based methods.

    Returns a dict with the same schema as ``ai_service.extract_from_text``.
    Every field is best-effort — may be ``None`` when no pattern matches.
    """
    if not raw_text or not raw_text.strip():
        return {}

    text = raw_text.strip()
    title = _extract_title(text)
    event_time = _extract_event_time(text)
    location = _extract_location(text)
    organizer = _extract_organizer(text)
    summary = _extract_summary(text)
    tags = _extract_tags(text)
    activity_type = _extract_activity_type(tags)

    result: dict[str, Any] = {
        "title": title,
        "event_time": event_time,
        "location": location,
        "organizer": organizer,
        "summary": summary,
        "tags": tags,
        "activity_type": activity_type,
    }
    return result
