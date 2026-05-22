"""Unit tests for knowledge_service."""

from datetime import datetime

from app.models import KnowledgeNode, Poster, PosterLink, PosterNode
from app.services.knowledge_service import (
    _date_name,
    _node_specs_for_poster,
    _normalize,
    _topic_from_poster,
    get_or_create_node,
    rebuild_poster_knowledge,
    rebuild_poster_nodes,
)


class TestNormalize:
    def test_normalizes_text(self):
        assert _normalize("  多个   空格  ") == "多个 空格"

    def test_returns_none_for_none(self):
        assert _normalize(None) is None

    def test_returns_none_for_whitespace(self):
        assert _normalize("   ") is None


class TestDateName:
    def test_formats_date(self):
        dt = datetime.fromisoformat("2026-05-10T19:00:00")
        assert _date_name(dt) == "2026-05-10"

    def test_returns_none_for_none(self):
        assert _date_name(None) is None


class TestTopicFromPoster:
    def test_detects_technology_topic(self):
        poster = Poster(title="科技创新论坛", raw_text="科技活动")
        assert _topic_from_poster(poster) == "科技活动"

    def test_detects_lecture_topic(self):
        poster = Poster(title="AI 前沿讲座", raw_text="关于人工智能的讲座")
        assert _topic_from_poster(poster) == "讲座"

    def test_detects_competition_topic(self):
        poster = Poster(title="编程竞赛通知", raw_text="")
        assert _topic_from_poster(poster) == "竞赛"

    def test_detects_recruitment_topic(self):
        poster = Poster(title="校园招聘会", raw_text="")
        assert _topic_from_poster(poster) == "招聘"

    def test_returns_none_for_unknown_topic(self):
        poster = Poster(title="随便什么活动", raw_text="没有关键词")
        assert _topic_from_poster(poster) is None


class TestNodeSpecsForPoster:
    def test_generates_specs_for_full_poster(self):
        poster = Poster(
            title="校园科技文化节",
            event_time=datetime.fromisoformat("2026-05-10T19:00:00"),
            location="大礼堂",
            organizer="校团委",
            source_url="https://example.edu.cn/event",
        )
        specs = _node_specs_for_poster(poster)
        assert len(specs) == 5  # time, place, org, topic, source
        types = {s["node_type"] for s in specs}
        assert types == {"time", "place", "organization", "topic", "source"}

    def test_generates_specs_for_minimal_poster(self):
        poster = Poster(title="简单活动", raw_text="内容")
        specs = _node_specs_for_poster(poster)
        # No time, place, org, or source
        assert all(s["node_type"] != "time" for s in specs)
        assert all(s["node_type"] != "place" for s in specs)


class TestGetOrCreateNode:
    def test_creates_new_node(self, app):
        with app.app_context():
            spec = {"name": "大礼堂", "node_type": "place", "description": "地点"}
            node = get_or_create_node(spec)
            assert node.id is not None
            assert node.name == "大礼堂"
            assert node.node_type == "place"

    def test_returns_existing_node(self, app):
        with app.app_context():
            spec = {"name": "校团委", "node_type": "organization"}
            node1 = get_or_create_node(spec)
            node2 = get_or_create_node(spec)
            assert node1.id == node2.id


class TestRebuildPosterNodes:
    def test_creates_nodes_for_poster(self, app):
        with app.app_context():
            poster = Poster(
                title="测试活动",
                raw_text="活动详细摘要内容",
                summary="活动摘要",
                event_time=datetime.fromisoformat("2026-05-10T19:00:00"),
                location="大礼堂",
                organizer="测试协会",
                source_url="https://example.edu.cn/test",
                status="published",
                source_type="manual",
                created_by=1,
            )
            from app.extensions import db

            db.session.add(poster)
            db.session.flush()

            nodes = rebuild_poster_nodes(poster)
            assert len(nodes) > 0
            assert all(n.poster_id == poster.id for n in nodes)


class TestRebuildPosterKnowledge:
    def test_full_rebuild_creates_nodes_and_links(self, app):
        with app.app_context():
            from app.extensions import db

            # Create two posters with the same day/location for links
            p1 = Poster(
                title="活动A",
                raw_text="活动A内容",
                summary="活动A摘要",
                event_time=datetime.fromisoformat("2026-05-10T10:00:00"),
                location="大礼堂",
                organizer="校团委",
                source_url="https://example.edu.cn/a",
                status="published",
                source_type="manual",
                created_by=1,
            )
            p2 = Poster(
                title="活动B",
                raw_text="活动B内容",
                summary="活动B摘要",
                event_time=datetime.fromisoformat("2026-05-10T15:00:00"),
                location="大礼堂",
                organizer="校团委",
                source_url="https://example.edu.cn/b",
                status="published",
                source_type="manual",
                created_by=1,
            )
            db.session.add_all([p1, p2])
            db.session.flush()

            result = rebuild_poster_knowledge(p1)
            assert "nodes" in result
            assert "links" in result
            assert len(result["nodes"]) > 0
