"""Shared fixtures for all tests.

IMPORTANT: The *app* fixture pushes the Flask app context and keeps it alive
for the entire test.  This prevents SQLAlchemy ``DetachedInstanceError`` when
fixture-created objects are accessed in test functions.
"""

import pytest
from flask_jwt_extended import create_access_token

from app import create_app
from app.config import Config
from app.extensions import db
from app.models import DataSource, Poster, User


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_SECRET_KEY = "test-secret"
    AUTO_CREATE_TABLES = True
    EMBEDDING_ENABLED = False
    ENABLE_SCHEDULED_CRAWL = False
    LLM_API_KEY = ""
    REDIS_URL = ""  # disable Redis for tests


@pytest.fixture
def app():
    """Create a Flask app with the application context pushed for the test."""
    application = create_app(TestConfig)
    ctx = application.app_context()
    ctx.push()
    db.create_all()
    admin = User(username="admin", role="admin")
    admin.set_password("admin123456")
    db.session.add(admin)
    db.session.commit()
    yield application
    db.session.remove()
    db.drop_all()
    ctx.pop()


@pytest.fixture
def client(app):
    return app.test_client()


# ── User fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def admin_user():
    return User.query.filter_by(username="admin").first()


@pytest.fixture
def admin_token(app, admin_user):
    return create_access_token(
        identity=str(admin_user.id),
        additional_claims={"role": admin_user.role, "username": admin_user.username},
    )


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def publisher_user():
    user = User(username="publisher", role="publisher")
    user.set_password("pass123456")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def publisher_token(app, publisher_user):
    return create_access_token(
        identity=str(publisher_user.id),
        additional_claims={"role": publisher_user.role, "username": publisher_user.username},
    )


@pytest.fixture
def publisher_headers(publisher_token):
    return {"Authorization": f"Bearer {publisher_token}"}


@pytest.fixture
def viewer_user():
    user = User(username="viewer", role="viewer")
    user.set_password("pass123456")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def viewer_token(app, viewer_user):
    return create_access_token(
        identity=str(viewer_user.id),
        additional_claims={"role": viewer_user.role, "username": viewer_user.username},
    )


@pytest.fixture
def viewer_headers(viewer_token):
    return {"Authorization": f"Bearer {viewer_token}"}


# ── Data fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def sample_poster(app, admin_user):
    poster = Poster(
        title="2026 校园科技文化节开幕式",
        raw_text="2026 校园科技文化节将于 2026-05-10 19:00 在大学生活动中心大礼堂举行。",
        summary="校园科技文化节开幕式，面向全校师生开放。",
        location="大学生活动中心大礼堂",
        organizer="校团委",
        status="draft",
        source_type="manual",
        source_url="https://example.edu.cn/tech-culture",
        created_by=admin_user.id,
    )
    db.session.add(poster)
    db.session.commit()
    return poster


@pytest.fixture
def sample_published_poster(app, admin_user):
    from datetime import datetime

    from app.services.knowledge_service import rebuild_poster_knowledge

    poster = Poster(
        title="AI 创新应用讲座",
        raw_text="AI 创新应用讲座将于 2026-05-10 15:00 举行，由计算机学院主办。",
        summary="面向全校学生的人工智能应用讲座。",
        event_time=datetime.fromisoformat("2026-05-10T15:00:00"),
        location="大学生活动中心大礼堂",
        organizer="计算机学院",
        status="published",
        source_type="manual",
        source_url="https://example.edu.cn/ai-lecture",
        created_by=admin_user.id,
    )
    db.session.add(poster)
    db.session.flush()
    rebuild_poster_knowledge(poster)
    db.session.commit()
    return poster


@pytest.fixture
def sample_data_source():
    ds = DataSource(
        name="校园网通知公告",
        base_url="https://example.edu.cn/notices",
        list_selector="a.news-title",
        content_selector="div.article-content",
        crawl_mode="basic",
        enabled=True,
        source_level="official",
        allowed_domains="example.edu.cn",
    )
    db.session.add(ds)
    db.session.commit()
    return ds
