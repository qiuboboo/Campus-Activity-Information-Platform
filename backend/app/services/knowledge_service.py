from datetime import datetime
import json
import re

from sqlalchemy import or_

from ..extensions import db
from ..models import (
    ActivityFavorite,
    ActivityRegistration,
    KnowledgeNode,
    Poster,
    PosterLink,
    PosterNode,
    Subscription,
    UserCalendarEvent,
)


NODE_RELATION_TYPES = {
    "time": "has_time",
    "place": "has_place",
    "organization": "has_org",
    "topic": "has_topic",
    "source": "has_source",
}


LINK_RULES = {
    "same_day": "event_date",
    "same_place": "location",
    "same_org": "organizer",
    "same_topic": "topic",
}


def _normalize(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = " ".join(str(value).strip().split())
    return normalized or None


def _date_name(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.date().isoformat()


def _topic_from_poster(poster: Poster) -> str | None:
    title = poster.title or ""
    summary = poster.summary or ""
    text = f"{title} {summary}"
    topic_keywords = [
        ("科技", "科技活动"),
        ("文化节", "校园文化"),
        ("讲座", "讲座"),
        ("论坛", "论坛"),
        ("竞赛", "竞赛"),
        ("比赛", "竞赛"),
        ("招聘", "招聘"),
        ("志愿", "志愿服务"),
        ("开幕式", "开幕式"),
    ]
    for keyword, topic in topic_keywords:
        if keyword in text:
            return topic
    return None


def _poster_tags(poster: Poster) -> set[str]:
    """Read legacy comma-separated and newer JSON tag values alike."""
    if not poster.tags:
        return set()
    try:
        value = json.loads(poster.tags)
        if isinstance(value, list):
            return {str(item).strip() for item in value if str(item).strip()}
    except (TypeError, json.JSONDecodeError):
        pass
    return {item.strip() for item in poster.tags.split(",") if item.strip()}


def _title_terms(poster: Poster) -> set[str]:
    """Small dependency-free lexical signal for Chinese and English titles."""
    text = f"{poster.title or ''} {poster.summary or ''}".lower()
    cjk = "".join(re.findall(r"[\u4e00-\u9fff]", text))
    terms = {cjk[index:index + 2] for index in range(max(0, len(cjk) - 1))}
    terms.update(re.findall(r"[a-z][a-z0-9_-]{2,}", text))
    return terms


def related_recommendations(poster: Poster, limit: int = 6) -> list[dict]:
    """Return explainable, multi-factor related-activity recommendations.

    This intentionally combines structured graph signals and lightweight text
    similarity, so recommendations remain deterministic and transparent even
    when embeddings or an external AI service are unavailable.
    """
    candidates = Poster.query.filter(
        Poster.id != poster.id,
        Poster.status == "published",
    ).all()
    source_tags = _poster_tags(poster)
    source_topic = _topic_from_poster(poster)
    source_terms = _title_terms(poster)
    ranked: list[tuple[int, Poster, list[str]]] = []

    for candidate in candidates:
        score = 0
        reasons: list[str] = []
        if poster.activity_type and poster.activity_type == candidate.activity_type:
            score += 3; reasons.append("同类活动")
        shared_tags = sorted(source_tags & _poster_tags(candidate))
        if shared_tags:
            score += min(4, len(shared_tags) * 2)
            reasons.append(f"共同标签：{'、'.join(shared_tags[:2])}")
        if poster.organizer and poster.organizer == candidate.organizer:
            score += 3; reasons.append("同一主办方")
        if poster.location and poster.location == candidate.location:
            score += 2; reasons.append("同一地点")
        if source_topic and source_topic == _topic_from_poster(candidate):
            score += 3; reasons.append(f"共同主题：{source_topic}")
        if poster.event_time and candidate.event_time:
            days = abs((poster.event_time.date() - candidate.event_time.date()).days)
            if days <= 7:
                score += 2; reasons.append("时间相近")
            elif days <= 30:
                score += 1
        shared_terms = source_terms & _title_terms(candidate)
        if len(shared_terms) >= 2:
            score += min(3, len(shared_terms))
            reasons.append("内容主题相近")
        if score >= 3:
            ranked.append((score, candidate, reasons))

    ranked.sort(key=lambda item: (-item[0], item[1].event_time or datetime.max, -item[1].id))
    return [
        {
            "poster": candidate.to_dict(),
            "score": score,
            "reason": " · ".join(reasons[:3]) or "相关活动推荐",
        }
        for score, candidate, reasons in ranked[:limit]
    ]


def personalized_recommendations(user_id: int, limit: int = 6) -> list[dict]:
    """Rank future activities from non-sensitive user behaviour.

    Registration form fields are intentionally never read.  Only the user's
    explicit favourites, registrations, subscriptions and calendar entries
    contribute to this profile, and every result carries an explanation.
    """
    favorites = ActivityFavorite.query.filter_by(user_id=user_id).all()
    registrations = ActivityRegistration.query.filter_by(user_id=user_id).all()
    seed_weights: dict[int, int] = {}
    for row in favorites:
        seed_weights[row.poster_id] = max(seed_weights.get(row.poster_id, 0), 3)
    for row in registrations:
        seed_weights[row.poster_id] = max(seed_weights.get(row.poster_id, 0), 4)
    subscribed_keywords = {
        (row.keyword or "").strip().lower()
        for row in Subscription.query.filter_by(user_id=user_id).all()
        if row.keyword and row.keyword.strip()
    }
    subscribed_node_ids = {
        row.node_id for row in Subscription.query.filter_by(user_id=user_id).all() if row.node_id
    }
    seeds = Poster.query.filter(Poster.id.in_(seed_weights)).all() if seed_weights else []
    registered_ids = {row.poster_id for row in registrations}
    favorite_ids = {row.poster_id for row in favorites}
    calendar_posters = [row.poster for row in UserCalendarEvent.query.filter_by(user_id=user_id).all() if row.poster]
    now = datetime.utcnow()
    candidates = Poster.query.filter(
        Poster.status == "published",
        or_(Poster.event_time.is_(None), Poster.event_time >= now),
    ).all()

    ranked: list[tuple[int, Poster, list[str]]] = []
    for candidate in candidates:
        if candidate.id in registered_ids or candidate.id in favorite_ids:
            continue
        score = 0
        reasons: list[str] = []
        candidate_terms = _title_terms(candidate)
        candidate_tags = _poster_tags(candidate)
        candidate_text = " ".join([
            candidate.title or "", candidate.summary or "", candidate.activity_type or "", candidate.tags or "",
        ]).lower()
        for seed in seeds:
            weight = seed_weights.get(seed.id, 1)
            matched = False
            if seed.activity_type and seed.activity_type == candidate.activity_type:
                score += 2 * weight; matched = True
            if _poster_tags(seed) & candidate_tags:
                score += 2 * weight; matched = True
            if _title_terms(seed) & candidate_terms:
                score += weight; matched = True
            if matched:
                reasons.append("与你收藏或报名的活动兴趣相近")
        keyword_matches = [keyword for keyword in subscribed_keywords if keyword in candidate_text]
        if keyword_matches:
            score += min(6, len(keyword_matches) * 3)
            reasons.append(f"匹配订阅：{keyword_matches[0]}")
        if subscribed_node_ids:
            node_match = PosterNode.query.filter(
                PosterNode.poster_id == candidate.id,
                PosterNode.node_id.in_(subscribed_node_ids),
            ).first()
            if node_match:
                score += 4; reasons.append("匹配订阅的知识主题")
        for scheduled in calendar_posters:
            if not candidate.event_time or not scheduled.event_time:
                continue
            if candidate.event_time == scheduled.event_time:
                score -= 6; reasons.append("与已有日程时间冲突")
            elif candidate.event_time.date() == scheduled.event_time.date():
                score -= 1; reasons.append("当日日程较密集")
        if not reasons:
            score += 1
            reasons.append("近期校园热门活动")
        ranked.append((score, candidate, reasons))

    ranked.sort(key=lambda item: (-item[0], item[1].event_time or datetime.max, -item[1].id))
    results: list[dict] = []
    type_counts: dict[str, int] = {}
    for score, candidate, reasons in ranked:
        activity_type = candidate.activity_type or "其他"
        if type_counts.get(activity_type, 0) >= 2:
            continue
        type_counts[activity_type] = type_counts.get(activity_type, 0) + 1
        results.append({
            "activity": candidate.to_dict(),
            "score": score,
            "reason": " · ".join(dict.fromkeys(reasons[:2])),
        })
        if len(results) >= limit:
            break
    return results


def _node_specs_for_poster(poster: Poster) -> list[dict]:
    specs = []
    event_date = _date_name(poster.event_time)
    location = _normalize(poster.location)
    organizer = _normalize(poster.organizer)
    topic = _topic_from_poster(poster)
    source = _normalize(poster.source_url)

    # Normalize location and organizer through the controlled vocabulary
    if location:
        try:
            location = _dict_normalize(location, category="place")
        except Exception:
            pass
    if organizer:
        try:
            organizer = _dict_normalize(organizer, category="org")
        except Exception:
            pass

    if event_date:
        specs.append(
            {
                "name": event_date,
                "node_type": "time",
                "relation_type": NODE_RELATION_TYPES["time"],
                "description": "活动日期",
            }
        )
    if location:
        specs.append(
            {
                "name": location,
                "node_type": "place",
                "relation_type": NODE_RELATION_TYPES["place"],
                "description": "活动地点",
            }
        )
    if organizer:
        specs.append(
            {
                "name": organizer,
                "node_type": "organization",
                "relation_type": NODE_RELATION_TYPES["organization"],
                "description": "活动主办方",
            }
        )
    if topic:
        specs.append(
            {
                "name": topic,
                "node_type": "topic",
                "relation_type": NODE_RELATION_TYPES["topic"],
                "description": "活动主题",
            }
        )
    if source:
        specs.append(
            {
                "name": source,
                "node_type": "source",
                "relation_type": NODE_RELATION_TYPES["source"],
                "description": "活动来源",
                "source_url": poster.source_url,
            }
        )
    return specs


def get_or_create_node(spec: dict) -> KnowledgeNode:
    node = KnowledgeNode.query.filter_by(
        name=spec["name"],
        node_type=spec["node_type"],
    ).first()
    if node is not None:
        return node

    node = KnowledgeNode(
        name=spec["name"],
        node_type=spec["node_type"],
        description=spec.get("description"),
        source_url=spec.get("source_url"),
    )
    db.session.add(node)
    db.session.flush()
    return node


def rebuild_poster_nodes(poster: Poster) -> list[PosterNode]:
    PosterNode.query.filter_by(poster_id=poster.id).delete()
    poster_nodes = []
    for spec in _node_specs_for_poster(poster):
        node = get_or_create_node(spec)
        poster_node = PosterNode(
            poster_id=poster.id,
            node_id=node.id,
            relation_type=spec["relation_type"],
            matched_by="rule",
        )
        db.session.add(poster_node)
        poster_nodes.append(poster_node)
    db.session.flush()
    return poster_nodes


def _same_day_filter(poster: Poster):
    if poster.event_time is None:
        return None
    start = datetime.combine(poster.event_time.date(), datetime.min.time())
    end = datetime.combine(poster.event_time.date(), datetime.max.time())
    return Poster.event_time.between(start, end)


def _related_candidates(poster: Poster, link_type: str):
    if link_type == "same_day":
        condition = _same_day_filter(poster)
    elif link_type == "same_place" and poster.location:
        condition = Poster.location == poster.location
    elif link_type == "same_org" and poster.organizer:
        condition = Poster.organizer == poster.organizer
    elif link_type == "same_topic":
        topic = _topic_from_poster(poster)
        if topic is None:
            return []
        return [
            candidate
            for candidate in Poster.query.filter(Poster.id != poster.id)
            .filter(Poster.status == "published")
            .all()
            if _topic_from_poster(candidate) == topic
        ]
    else:
        return []

    if condition is None:
        return []

    return (
        Poster.query.filter(Poster.id != poster.id)
        .filter(Poster.status == "published")
        .filter(condition)
        .all()
    )


def rebuild_poster_links(poster: Poster) -> list[PosterLink]:
    PosterLink.query.filter_by(from_poster_id=poster.id).delete()
    links = []
    for link_type, rule_name in LINK_RULES.items():
        for candidate in _related_candidates(poster, link_type):
            existing = PosterLink.query.filter_by(
                from_poster_id=poster.id,
                to_poster_id=candidate.id,
                link_type=link_type,
            ).first()
            if existing is not None:
                continue
            link = PosterLink(
                from_poster_id=poster.id,
                to_poster_id=candidate.id,
                link_type=link_type,
                created_by_rule=rule_name,
            )
            db.session.add(link)
            links.append(link)
    db.session.flush()
    return links


def rebuild_poster_knowledge(poster: Poster) -> dict:
    nodes = rebuild_poster_nodes(poster)
    links = rebuild_poster_links(poster)
    return {"nodes": nodes, "links": links}


def related_payload(poster: Poster) -> dict:
    direct_nodes = PosterNode.query.filter_by(poster_id=poster.id).all()
    direct_links = [
        *PosterLink.query.filter_by(from_poster_id=poster.id).all(),
        *PosterLink.query.filter_by(to_poster_id=poster.id).all(),
    ]
    node_ids = [poster_node.node_id for poster_node in direct_nodes]
    related_posters = related_recommendations(poster)

    return {
        "poster": poster.to_dict(),
        "knowledge_nodes": [poster_node.to_dict() for poster_node in direct_nodes],
        "nodes": [poster_node.node.to_dict() for poster_node in direct_nodes if poster_node.node],
        "related": related_posters,
        "related_posters": related_posters,
        "poster_links": [_link_payload(link, poster.id) for link in direct_links],
    }


def _link_payload(link: PosterLink, current_poster_id: int) -> dict:
    is_outgoing = link.from_poster_id == current_poster_id
    related = link.to_poster if is_outgoing else link.from_poster
    return {
        "id": link.id,
        "direction": "outgoing" if is_outgoing else "incoming",
        "link_type": link.link_type,
        "created_by_rule": link.created_by_rule,
        "created_at": link.created_at.isoformat(),
        "related_poster": related.to_dict() if related else None,
    }
