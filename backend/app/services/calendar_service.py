"""Calendar service: generate .ics files and manage user calendar events."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta

from ..models import Poster


def generate_ics(poster: Poster) -> str:
    """Return a standard iCalendar (.ics) string for a single poster.

    The output follows RFC 5545 so that it can be imported by Apple/Google/
    Outlook calendars.
    """
    dtstart, dtend = _ics_datetimes(poster)
    uid = f"poster-{poster.id}@campus-activity-platform"
    stamp = _format_dt(datetime.utcnow())

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Campus Activity Platform//CN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{stamp}",
        f"DTSTART:{dtstart}",
        f"DTEND:{dtend}",
        f"SUMMARY:{_escape_text(poster.title)}",
    ]

    if poster.summary:
        lines.append(f"DESCRIPTION:{_escape_text(poster.summary)}")
    if poster.location:
        lines.append(f"LOCATION:{_escape_text(poster.location)}")
    if poster.organizer:
        lines.append(f"ORGANIZER:{_escape_text(poster.organizer)}")

    lines.extend(["END:VEVENT", "END:VCALENDAR"])
    return "\r\n".join(lines) + "\r\n"


def _ics_datetimes(poster: Poster) -> tuple[str, str]:
    """Return (DTSTART, DTEND) iCalendar formatted strings.

    Uses event_time if available, otherwise falls back to created_at.
    Defaults to a 2-hour duration.
    """
    start = poster.event_time if poster.event_time else poster.created_at
    end = start + timedelta(hours=2) if poster.event_time else start + timedelta(days=1)
    return _format_dt(start), _format_dt(end)


def _format_dt(dt: datetime) -> str:
    """Format a datetime as iCalendar UTC datetime (YYYYMMDDTHHMMSSZ)."""
    return dt.strftime("%Y%m%dT%H%M%SZ")


def _escape_text(text: str) -> str:
    """Escape text per RFC 5545."""
    text = text.replace("\\", "\\\\")
    text = text.replace(";", "\\;")
    text = text.replace(",", "\\,")
    text = text.replace("\n", "\\n")
    return text
