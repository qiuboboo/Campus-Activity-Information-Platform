"""Subscription matching and notification dispatch.

Called after a poster is published.  Finds all users whose subscriptions
match the poster (by knowledge node or keyword) and creates in-platform
notification records.
"""

from __future__ import annotations

import logging
from typing import List

from sqlalchemy import or_

from ..extensions import db
from ..models import KnowledgeNode, Notification, Poster, PosterNode, Subscription

logger = logging.getLogger(__name__)


def dispatch_notifications(poster: Poster) -> list[Notification]:
    """Match *poster* against all subscriptions and create notifications.

    Called from the review flow when a poster transitions to ``published``.
    Returns the list of created :class:`Notification` objects.
    """
    if poster.status != "published":
        return []

    poster_node_ids = _collect_node_ids(poster)
    matched_user_ids: set[int] = set()
    notifications: list[Notification] = []

    # 1. Match by knowledge node
    if poster_node_ids:
        node_subscriptions = Subscription.query.filter(
            Subscription.node_id.in_(poster_node_ids),
        ).all()
        for sub in node_subscriptions:
            if sub.user_id not in matched_user_ids:
                matched_user_ids.add(sub.user_id)
                notifications.append(_build_notification(sub.user_id, poster, "node"))

    # 2. Match by keyword (title, activity_type, tags)
    keyword_subscriptions = Subscription.query.filter(
        Subscription.node_id.is_(None),
        Subscription.keyword.isnot(None),
    ).all()
    poster_text = _poster_searchable_text(poster).lower()
    for sub in keyword_subscriptions:
        if sub.user_id in matched_user_ids:
            continue  # already got a notification from node match
        kw = (sub.keyword or "").lower().strip()
        if kw and kw in poster_text:
            matched_user_ids.add(sub.user_id)
            notifications.append(_build_notification(sub.user_id, poster, "keyword"))

    if notifications:
        db.session.bulk_save_objects(notifications)
        db.session.flush()
        logger.info(
            "Dispatched %d notifications for poster #%d '%s'",
            len(notifications),
            poster.id,
            poster.title,
        )

    return notifications


def _collect_node_ids(poster: Poster) -> list[int]:
    """Return list of knowledge-node IDs associated with *poster*."""
    rows = (
        PosterNode.query.with_entities(PosterNode.node_id)
        .filter_by(poster_id=poster.id)
        .all()
    )
    return [r.node_id for r in rows]


def _poster_searchable_text(poster: Poster) -> str:
    """Build a lower-cased search string from a poster's matchable fields."""
    parts = [
        poster.title or "",
        poster.activity_type or "",
        poster.tags or "",
        poster.location or "",
        poster.organizer or "",
    ]
    return " ".join(parts)


def _build_notification(user_id: int, poster: Poster, match_type: str) -> Notification:
    """Create a single notification record (not yet flushed)."""
    if match_type == "node":
        body = f"您订阅的内容有新活动：{poster.title}"
    else:
        body = f"您订阅的关键词匹配到新活动：{poster.title}"
    return Notification(
        user_id=user_id,
        poster_id=poster.id,
        title="新活动发布：" + poster.title,
        body=body,
    )
