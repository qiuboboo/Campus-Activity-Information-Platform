"""Tests for data models — creation, relationships, constraints, to_dict()."""

from datetime import datetime, timedelta

import pytest
from werkzeug.security import check_password_hash

from app.extensions import db
from app.models import (
    AuditLog,
    CrawlLog,
    DataSource,
    DictEntry,
    KnowledgeNode,
    Notification,
    Poster,
    PosterLink,
    PosterNode,
    Subscription,
    User,
    UserCalendarEvent,
)


class TestUserModel:
    def test_create_user(self, app):
        user = User(username="test1", role="viewer")
        user.set_password("secret123")
        db.session.add(user)
        db.session.commit()

        assert user.id is not None
        assert user.username == "test1"
        assert user.role == "viewer"
        assert user.email is None
        assert check_password_hash(user.password_hash, "secret123")

    def test_to_dict(self, app, admin_user):
        d = admin_user.to_dict()
        assert d["id"] == admin_user.id
        assert d["username"] == "admin"
        assert d["role"] == "admin"
        assert "password_hash" not in d

    def test_unique_username(self, app, admin_user):
        dup = User(username="admin", role="viewer")
        db.session.add(dup)
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()


class TestPosterModel:
    def test_create_poster(self, app, admin_user):
        poster = Poster(
            title="测试活动",
            raw_text="这是一场测试活动",
            summary="测试摘要",
            created_by=admin_user.id,
        )
        db.session.add(poster)
        db.session.commit()

        assert poster.id is not None
        assert poster.status == "draft"
        assert poster.source_type == "manual"
        assert poster.created_at is not None
        assert poster.updated_at is not None

    def test_to_dict(self, app, sample_published_poster):
        d = sample_published_poster.to_dict()
        assert d["id"] == sample_published_poster.id
        assert d["title"] == "AI 创新应用讲座"
        assert d["status"] == "published"
        assert d["event_time"] is not None


class TestKnowledgeNodeModel:
    def test_create_node(self, app):
        node = KnowledgeNode(
            name="大学生活动中心大礼堂",
            node_type="location",
            description="主要活动场所",
        )
        db.session.add(node)
        db.session.commit()

        assert node.id is not None
        assert node.node_type == "location"

    def test_unique_name_type(self, app):
        n1 = KnowledgeNode(name="大礼堂", node_type="location")
        db.session.add(n1)
        db.session.commit()

        n2 = KnowledgeNode(name="大礼堂", node_type="location")
        db.session.add(n2)
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()

    def test_different_types_same_name_allowed(self, app):
        n1 = KnowledgeNode(name="计算机学院", node_type="organization")
        n2 = KnowledgeNode(name="计算机学院", node_type="location")
        db.session.add_all([n1, n2])
        db.session.commit()  # should not raise

    def test_to_dict(self, app):
        node = KnowledgeNode(name="校团委", node_type="organization")
        db.session.add(node)
        db.session.commit()
        d = node.to_dict()
        assert d["name"] == "校团委"
        assert d["node_type"] == "organization"


class TestPosterNodeRelation:
    def test_link_poster_to_node(self, app, sample_published_poster):
        node = KnowledgeNode(name="大礼堂", node_type="location")
        db.session.add(node)
        db.session.flush()

        pn = PosterNode(
            poster_id=sample_published_poster.id,
            node_id=node.id,
            relation_type="location",
            matched_by="rule",
        )
        db.session.add(pn)
        db.session.commit()

        assert pn.id is not None
        assert pn.poster.id == sample_published_poster.id
        assert pn.node.name == "大礼堂"


class TestDataSourceModel:
    def test_create_data_source(self, app):
        ds = DataSource(
            name="测试数据源",
            base_url="https://example.com/news",
            list_selector="a.title",
            content_selector="div.content",
        )
        db.session.add(ds)
        db.session.commit()

        assert ds.id is not None
        assert ds.enabled is True
        assert ds.crawl_mode == "basic"
        assert ds.request_interval == 2

    def test_allowed_domains(self, app):
        ds = DataSource(
            name="test",
            base_url="https://a.com",
            allowed_domains="a.com,b.com",
        )
        db.session.add(ds)
        db.session.commit()

        assert ds.get_allowed_domains() == ["a.com", "b.com"]

    def test_to_dict(self, app):
        ds = DataSource(name="test", base_url="https://a.com")
        db.session.add(ds)
        db.session.commit()
        d = ds.to_dict()
        assert d["name"] == "test"
        assert d["crawl_mode"] == "basic"


class TestCrawlLogModel:
    def test_create_log(self, app, sample_data_source):
        log = CrawlLog(data_source_id=sample_data_source.id, status="success")
        db.session.add(log)
        db.session.commit()

        assert log.id is not None
        assert log.data_source.id == sample_data_source.id


class TestAuditLogModel:
    def test_create_audit_log(self, app, admin_user):
        log = AuditLog(
            actor_id=admin_user.id,
            action="test_action",
            target_type="poster",
            target_id=1,
            summary="Test audit entry",
        )
        db.session.add(log)
        db.session.commit()

        assert log.id is not None
        assert log.actor_id == admin_user.id
        assert log.created_at is not None


class TestSubscriptionModel:
    def test_create_subscription_by_node(self, app, admin_user):
        node = KnowledgeNode(name="test_node", node_type="topic")
        db.session.add(node)
        db.session.flush()

        sub = Subscription(user_id=admin_user.id, node_id=node.id, notify_method="platform")
        db.session.add(sub)
        db.session.commit()

        assert sub.id is not None
        assert sub.user_id == admin_user.id
        assert sub.node_id == node.id

    def test_create_subscription_by_keyword(self, app, admin_user):
        sub = Subscription(user_id=admin_user.id, keyword="讲座", notify_method="platform")
        db.session.add(sub)
        db.session.commit()

        assert sub.id is not None
        assert sub.keyword == "讲座"

    def test_requires_node_or_keyword(self, app, admin_user):
        sub = Subscription(user_id=admin_user.id, notify_method="platform")
        db.session.add(sub)
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()


class TestNotificationModel:
    def test_create_notification(self, app, admin_user, sample_published_poster):
        notif = Notification(
            user_id=admin_user.id,
            poster_id=sample_published_poster.id,
            title="新活动",
            body="有新活动发布",
        )
        db.session.add(notif)
        db.session.commit()

        assert notif.id is not None
        assert notif.is_read is False

    def test_to_dict(self, app, admin_user, sample_published_poster):
        notif = Notification(
            user_id=admin_user.id,
            poster_id=sample_published_poster.id,
            title="新活动",
            body="详情",
        )
        db.session.add(notif)
        db.session.commit()

        d = notif.to_dict()
        assert d["is_read"] is False
        assert d["poster"]["id"] == sample_published_poster.id
        assert d["poster"]["title"] == sample_published_poster.title


class TestUserCalendarEventModel:
    def test_create_event(self, app, admin_user, sample_published_poster):
        event = UserCalendarEvent(
            user_id=admin_user.id,
            poster_id=sample_published_poster.id,
        )
        db.session.add(event)
        db.session.commit()

        assert event.id is not None

    def test_unique_user_poster(self, app, admin_user, sample_published_poster):
        e1 = UserCalendarEvent(user_id=admin_user.id, poster_id=sample_published_poster.id)
        db.session.add(e1)
        db.session.commit()

        e2 = UserCalendarEvent(user_id=admin_user.id, poster_id=sample_published_poster.id)
        db.session.add(e2)
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()


class TestDictEntryModel:
    def test_create_entry(self, app):
        entry = DictEntry(
            category="place",
            standard_name="大学生活动中心大礼堂",
            aliases="大活礼堂,大礼堂",
            description="校园主要活动场所",
        )
        db.session.add(entry)
        db.session.commit()

        assert entry.id is not None
        assert entry.alias_list() == ["大活礼堂", "大礼堂"]

    def test_empty_aliases(self, app):
        entry = DictEntry(category="place", standard_name="测试")
        db.session.add(entry)
        db.session.commit()

        assert entry.alias_list() == []

    def test_unique_category_name(self, app):
        e1 = DictEntry(category="place", standard_name="大礼堂")
        db.session.add(e1)
        db.session.commit()

        e2 = DictEntry(category="place", standard_name="大礼堂")
        db.session.add(e2)
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()


class TestTimestampMixin:
    def test_created_at_set(self, app, admin_user):
        assert admin_user.created_at is not None
        assert isinstance(admin_user.created_at, datetime)

    def test_updated_at_tracks_changes(self, app, admin_user):
        old_updated = admin_user.updated_at
        admin_user.username = "admin_renamed"
        db.session.commit()
        assert admin_user.updated_at >= old_updated
