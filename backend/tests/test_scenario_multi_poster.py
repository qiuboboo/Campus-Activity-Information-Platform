"""Comprehensive scenario: multi-poster lifecycle with knowledge graph, search,
subscriptions, notifications, and calendar.

Design: nearly 100% white-box — exercises service layer AND API layer.
Uses the standard conftest (SQLite in-memory, no external deps).
"""

import pytest
from datetime import datetime

from app.extensions import db
from app.models import (
    KnowledgeNode, Notification, Poster, PosterLink, PosterNode,
    Subscription, User, UserCalendarEvent,
)
from app.services.knowledge_service import (
    rebuild_poster_knowledge, related_payload, _topic_from_poster,
    _node_specs_for_poster, get_or_create_node,
)
from app.services.notification_service import dispatch_notifications
from app.services.calendar_service import generate_ics


# ---------------------------------------------------------------------------
# Fixture: 5 related posters
# ---------------------------------------------------------------------------
@pytest.fixture
def five_posters(app, admin_user):
    """Create 5 interconnected posters sharing time/place/org/topic."""
    base_time = datetime.fromisoformat("2026-06-15T19:00:00")
    posters = []

    specs = [
        {
            "title": "AI创新应用讲座",
            "raw_text": "计算机学院主办AI创新应用讲座，6月15日晚7点在大学生活动中心大礼堂举行",
            "summary": "面向全校学生的人工智能应用讲座",
            "event_time": base_time,
            "location": "大学生活动中心大礼堂",
            "organizer": "计算机学院",
        },
        {
            "title": "校园科技文化节",
            "raw_text": "校团委主办校园科技文化节，6月15日晚7点在大学生活动中心大礼堂开幕",
            "summary": "年度校园科技文化盛会",
            "event_time": base_time,  # SAME DAY & SAME PLACE
            "location": "大学生活动中心大礼堂",
            "organizer": "校团委",
        },
        {
            "title": "机器学习竞赛",
            "raw_text": "计算机学院主办机器学习竞赛，6月16日下午2点在图书馆报告厅",
            "summary": "面向全校的机器学习算法竞赛",
            "event_time": datetime.fromisoformat("2026-06-16T14:00:00"),
            "location": "图书馆报告厅",
            "organizer": "计算机学院",  # SAME ORG as #1
        },
        {
            "title": "职业规划讲座",
            "raw_text": "就业指导中心主办职业规划讲座，6月17日上午10点在大学生活动中心大礼堂",
            "summary": "帮助学生做好职业规划",
            "event_time": datetime.fromisoformat("2026-06-17T10:00:00"),
            "location": "大学生活动中心大礼堂",  # SAME PLACE as #1, #2
            "organizer": "就业指导中心",
        },
        {
            "title": "志愿服务招募",
            "raw_text": "校团委招募志愿者，报名截止6月20日",
            "summary": "暑期志愿服务项目招募志愿者",
            "event_time": None,  # NO TIME
            "location": None,    # NO PLACE
            "organizer": "校团委",  # SAME ORG as #2
        },
    ]

    for s in specs:
        p = Poster(
            title=s["title"],
            raw_text=s["raw_text"],
            summary=s["summary"],
            event_time=s.get("event_time"),
            location=s.get("location"),
            organizer=s.get("organizer"),
            status="published",
            source_type="manual",
            created_by=admin_user.id,
        )
        db.session.add(p)
        db.session.flush()
        rebuild_poster_knowledge(p)
        posters.append(p)
    db.session.commit()
    return posters


class TestKnowledgeGraphIntegrity:
    """White-box: verify knowledge nodes and links after bulk creation."""

    def test_nodes_created_for_all_posters(self, five_posters):
        for p in five_posters:
            node_count = PosterNode.query.filter_by(poster_id=p.id).count()
            assert node_count > 0, f"Poster '{p.title}' has no nodes"

    def test_place_nodes_shared_across_posters(self, five_posters):
        """Posters #1, #2, #4 share '大学生活动中心大礼堂' — same node_id."""
        place_node = KnowledgeNode.query.filter_by(
            name="大学生活动中心大礼堂", node_type="place",
        ).first()
        assert place_node is not None
        linked = set()
        for pn in place_node.posters:
            linked.add(pn.poster_id)
        # At least posters 1, 2, 4 should be linked
        assert len(linked) >= 3

    def test_org_nodes_shared_correctly(self, five_posters):
        """Posters #1, #3 share '计算机学院'; #2, #5 share '校团委'."""
        cs = KnowledgeNode.query.filter_by(
            name="计算机学院", node_type="organization",
        ).first()
        tw = KnowledgeNode.query.filter_by(
            name="校团委", node_type="organization",
        ).first()
        assert cs is not None
        assert tw is not None
        assert len([pn for pn in cs.posters]) >= 2  # posters 1, 3
        assert len([pn for pn in tw.posters]) >= 2  # posters 2, 5

    def test_poster_links_generated(self, five_posters):
        """Same-day / same-place / same-org links should exist."""
        p1, p2, p3, p4, p5 = five_posters
        links = (
            PosterLink.query.filter_by(from_poster_id=p1.id).all()
            + PosterLink.query.filter_by(to_poster_id=p1.id).all()
        )
        assert len(links) >= 1, "Poster #1 should have links to others"

    def test_poster_without_time_has_no_time_node(self, five_posters):
        """Poster #5 has no event_time → no time knowledge node."""
        p5 = five_posters[4]
        time_node = PosterNode.query.filter_by(
            poster_id=p5.id,
        ).join(KnowledgeNode).filter(KnowledgeNode.node_type == "time").first()
        assert time_node is None

    def test_all_posters_have_unique_ids(self, five_posters):
        ids = [p.id for p in five_posters]
        assert len(set(ids)) == 5


class TestRelatedPayload:
    def test_related_payload_has_all_sections(self, five_posters):
        p1 = five_posters[0]
        payload = related_payload(p1)
        assert "poster" in payload
        assert "knowledge_nodes" in payload
        assert "related_posters" in payload
        assert "poster_links" in payload
        assert len(payload["knowledge_nodes"]) >= 1

    def test_no_self_reference_in_related(self, five_posters):
        p1 = five_posters[0]
        payload = related_payload(p1)
        related_ids = [r["poster"]["id"] for r in payload["related_posters"]]
        assert p1.id not in related_ids

    def test_endpoint_returns_related(self, client, admin_headers, five_posters):
        p1 = five_posters[0]
        r = client.get(f"/api/posters/{p1.id}/related", headers=admin_headers)
        assert r.status_code == 200
        assert len(r.get_json()["knowledge_nodes"]) >= 1


class TestSubscriptionAndNotification:
    def test_subscription_matches_published_poster(self, app, admin_user, five_posters):
        """Subscribe to keyword 'AI' → should match poster #1 'AI创新应用讲座'."""
        Subscription.query.delete()
        Notification.query.delete()
        sub = Subscription(user_id=admin_user.id, keyword="AI", notify_method="platform")
        db.session.add(sub)
        db.session.commit()

        p1 = five_posters[0]
        notifications = dispatch_notifications(p1)
        assert len(notifications) >= 1
        assert notifications[0].poster_id == p1.id
        assert p1.title in notifications[0].title

    def test_no_duplicate_notification_for_node_and_keyword(self, app, admin_user,
                                                              five_posters):
        """A single user should not get 2 notifications for the same poster."""
        Subscription.query.delete()
        Notification.query.delete()
        node_ids = [pn.node_id for pn in five_posters[0].nodes]
        if not node_ids:
            pytest.skip("no nodes")
        sub1 = Subscription(user_id=admin_user.id, node_id=node_ids[0])
        sub2 = Subscription(user_id=admin_user.id, keyword="AI")
        db.session.add_all([sub1, sub2])
        db.session.commit()

        notifications = dispatch_notifications(five_posters[0])
        user_ids = [n.user_id for n in notifications]
        assert len(user_ids) == len(set(user_ids))


class TestSearchAcrossPosters:
    def test_keyword_finds_multiple(self, client, admin_headers, five_posters):
        """'计算机学院' should match at least posters #1 and #3."""
        r = client.get("/api/posters?q=计算机学院", headers=admin_headers)
        assert r.status_code == 200
        items = r.get_json()["items"]
        assert len(items) >= 2

    def test_keyword_no_hit(self, client, admin_headers, five_posters):
        r = client.get("/api/posters?q=zzz_nonexistent_xyz", headers=admin_headers)
        assert r.status_code == 200
        assert len(r.get_json()["items"]) == 0

    def test_internal_search_finds_nodes(self, client, admin_headers, five_posters):
        """Internal search for '大礼堂' should return knowledge nodes."""
        r = client.get("/api/search/internal?q=大礼堂", headers=admin_headers)
        assert r.status_code == 200
        items = r.get_json()["items"]
        types = {i["hit_type"] for i in items if "hit_type" in i}
        assert "knowledge_node" in types


class TestCalendarFlow:
    def test_generate_ics_for_published(self, five_posters):
        p1 = five_posters[0]
        ics = generate_ics(p1)
        assert "BEGIN:VCALENDAR" in ics
        assert "BEGIN:VEVENT" in ics
        assert p1.title in ics
        assert "SUMMARY" in ics

    def test_calendar_event_crud(self, client, admin_headers, five_posters):
        """Full calendar lifecycle: add → list → remove."""
        p1 = five_posters[0]
        # Add
        r = client.post("/api/calendar/events",
                        json={"poster_id": p1.id}, headers=admin_headers)
        assert r.status_code == 201
        # List
        r = client.get("/api/calendar/events", headers=admin_headers)
        assert r.get_json()["total"] >= 1
        # Remove
        r = client.delete(f"/api/calendar/events/{p1.id}", headers=admin_headers)
        assert r.status_code == 200


class TestReviewQueue:
    def test_published_do_not_appear_in_review_queue(self, client, admin_headers,
                                                       five_posters):
        """Published posters should not appear in review queue."""
        r = client.get("/api/posters/review-queue", headers=admin_headers)
        assert r.status_code == 200
        published_ids = {p.id for p in five_posters}
        queue_ids = {i["id"] for i in r.get_json()["items"]}
        assert queue_ids.isdisjoint(published_ids)

    def test_draft_appears_in_queue(self, client, admin_headers, sample_poster):
        """Draft poster should appear in review queue."""
        r = client.get("/api/posters/review-queue", headers=admin_headers)
        items = r.get_json()["items"]
        draft_ids = {i["id"] for i in items}
        assert sample_poster.id in draft_ids


