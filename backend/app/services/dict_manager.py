"""Dict Manager — controlled vocabulary for location, organization, and topic normalization.

Provides CRUD operations and a ``normalize()`` helper that transforms
user-facing aliases into canonical ``standard_name`` values.

Usage::

    from .dict_manager import normalize, add_entry

    name = normalize("大活礼堂", category="place")
    # -> "大学生活动中心大礼堂"  (if that mapping exists)
"""

from __future__ import annotations

import logging
from typing import Any

from ..extensions import db
from ..models import DictEntry

logger = logging.getLogger(__name__)

_VALID_CATEGORIES = {"place", "org", "topic"}


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


def add_entry(
    category: str,
    standard_name: str,
    aliases: str | None = None,
    description: str | None = None,
) -> DictEntry:
    """Add a new dictionary entry.

    Raises ``ValueError`` for invalid categories.
    """
    _validate_category(category)
    entry = DictEntry(
        category=category,
        standard_name=standard_name.strip(),
        aliases=aliases.strip() if aliases else None,
        description=description.strip() if description else None,
    )
    db.session.add(entry)
    db.session.flush()
    return entry


def update_entry(entry_id: int, **kwargs) -> DictEntry | None:
    """Update an existing dictionary entry."""
    entry = db.session.get(DictEntry, entry_id)
    if entry is None:
        return None
    if "category" in kwargs:
        _validate_category(kwargs["category"])
    for key in ("category", "standard_name", "aliases", "description"):
        if key in kwargs:
            setattr(entry, key, kwargs[key].strip() if kwargs[key] else None)
    db.session.flush()
    return entry


def delete_entry(entry_id: int) -> bool:
    """Delete an entry. Returns ``True`` if deleted, ``False`` if not found."""
    entry = db.session.get(DictEntry, entry_id)
    if entry is None:
        return False
    db.session.delete(entry)
    db.session.flush()
    return True


def list_entries(
    category: str | None = None,
    query: str | None = None,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[DictEntry], int]:
    """List dictionary entries, optionally filtered by category and keyword."""
    q = DictEntry.query.order_by(DictEntry.category, DictEntry.standard_name)
    if category:
        _validate_category(category)
        q = q.filter(DictEntry.category == category)
    if query:
        like = f"%{query}%"
        q = q.filter(
            db.or_(DictEntry.standard_name.like(like), DictEntry.aliases.like(like))
        )
    items = q.paginate(page=page, per_page=per_page, error_out=False)
    return items.items, items.total


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------


def normalize(name: str, category: str) -> str:
    """Look up *name* (or any of its known aliases) and return the canonical form.

    If no match is found, the original *name* is returned unchanged.
    """
    _validate_category(category)
    if not name or not name.strip():
        return name

    stripped = name.strip()
    # Direct match on standard_name
    entry = DictEntry.query.filter_by(category=category, standard_name=stripped).first()
    if entry is not None:
        return entry.standard_name

    # Fuzzy match via alias list
    all_entries = DictEntry.query.filter_by(category=category).all()
    for entry in all_entries:
        if stripped in entry.alias_list():
            return entry.standard_name

    return name


def normalize_all(names: list[str], category: str) -> list[str]:
    """Normalize multiple names at once."""
    return [normalize(n, category) for n in names]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_KNOWN_ALIASES: dict[str, dict[str, str]] = {
    "place": {
        "大活": "大学生活动中心",
        "大活礼堂": "大学生活动中心大礼堂",
        "梁銶琚堂": "梁銶琚礼堂",
        "逸夫楼": "逸夫楼报告厅",
        "丰盛堂": "丰盛堂",
        "岭南堂": "岭南堂",
        "怀士堂": "怀士堂",
        "一教": "第一教学楼",
        "二教": "第二教学楼",
        "三教": "第三教学楼",
        "文科楼": "文科大楼",
        "理科楼": "理科大楼",
    },
    "org": {
        "校团委": "共青团中山大学委员会",
        "团委": "共青团中山大学委员会",
        "学生会": "中山大学学生会",
        "校学生会": "中山大学学生会",
        "研会": "中山大学研究生会",
        "研究生会": "中山大学研究生会",
        "青协": "中山大学青年志愿者协会",
        "社联": "中山大学学生社团联合会",
    },
}


def suggest_from_posters(category: str) -> list[dict]:
    """Scan published posters for values not yet in the dictionary.

    Returns a list of ``{value, count}`` sorted by count descending.
    Only includes values that do NOT already normalize to an existing entry.
    """
    from ..models import DictEntry, Poster

    column = {"place": "location", "org": "organizer", "topic": "activity_type"}.get(category)
    if column is None:
        return []

    existing_standards = {
        e.standard_name for e in DictEntry.query.filter_by(category=category).all()
    }
    # Gather values and normalize them
    raw_values = (
        Poster.query
        .filter(Poster.status == "published")
        .with_entities(getattr(Poster, column))
        .all()
    )
    counts: dict[str, int] = {}
    for (val,) in raw_values:
        val = (val or "").strip()
        if not val:
            continue
        normalized = normalize(val, category)
        if normalized not in existing_standards:
            counts[val] = counts.get(val, 0) + 1

    return sorted(
        [{"value": v, "count": c} for v, c in counts.items()],
        key=lambda x: x["count"],
        reverse=True,
    )


def seed_builtin_aliases() -> int:
    """Insert hard-coded alias mappings into the database.

    Idempotent — skips entries whose ``standard_name`` already exists.
    Returns the number of entries created.
    """
    count = 0
    for category, aliases in _KNOWN_ALIASES.items():
        for alias, standard in aliases.items():
            existing = DictEntry.query.filter_by(
                category=category, standard_name=standard
            ).first()
            if existing is not None:
                continue
            entry = DictEntry(
                category=category,
                standard_name=standard,
                aliases=alias,
                description=f"内置别名映射：{alias}",
            )
            db.session.add(entry)
            count += 1
    if count:
        db.session.flush()
    return count


def _validate_category(category: str) -> None:
    if category not in _VALID_CATEGORIES:
        raise ValueError(
            f"Invalid category '{category}'. Must be one of: {', '.join(sorted(_VALID_CATEGORIES))}"
        )
