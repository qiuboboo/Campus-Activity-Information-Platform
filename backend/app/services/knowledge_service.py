from datetime import datetime

from sqlalchemy import or_

from ..extensions import db
from ..models import KnowledgeNode, Poster, PosterLink, PosterNode


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
            from .dict_manager import normalize
            location = normalize(location, category="place")
        except Exception:
            pass
    if organizer:
        try:
            from .dict_manager import normalize
            organizer = normalize(organizer, category="org")
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
    related_posters = []

    if node_ids:
        related_rows = (
            PosterNode.query.filter(PosterNode.node_id.in_(node_ids))
            .filter(PosterNode.poster_id != poster.id)
            .all()
        )
        seen = set()
        for row in related_rows:
            if row.poster_id in seen:
                continue
            seen.add(row.poster_id)
            related_posters.append(
                {
                    "poster": row.poster.to_dict(),
                    "shared_node": row.node.to_dict(),
                    "relation_type": row.relation_type,
                }
            )

    return {
        "poster": poster.to_dict(),
        "knowledge_nodes": [poster_node.to_dict() for poster_node in direct_nodes],
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
