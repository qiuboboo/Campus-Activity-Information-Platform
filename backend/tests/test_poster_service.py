"""Unit tests for poster_service."""

from datetime import datetime

from app.services.poster_service import build_poster_fields, generate_poster_html


class TestGeneratePosterHtml:
    def test_generates_full_html(self):
        html = generate_poster_html(
            title="测试活动",
            summary="这是摘要",
            event_time=datetime.fromisoformat("2026-05-10T19:00:00"),
            location="大礼堂",
            organizer="校团委",
            activity_type="讲座",
        )
        assert "<!DOCTYPE html>" in html
        assert "测试活动" in html
        assert "大礼堂" in html
        assert "校团委" in html
        assert "讲座" in html
        assert "大礼堂" in html
        assert "校团委" in html
        assert "讲座" in html
        assert "2026-05-10 19:00" in html

    def test_handles_none_fields(self):
        html = generate_poster_html(title="仅标题", summary="仅摘要")
        assert "仅标题" in html
        assert "仅摘要" in html
        assert "时间" not in html
        assert "地点" not in html

    def test_escapes_html(self):
        html = generate_poster_html(
            title='<script>alert("xss")</script>',
            summary="safe",
        )
        assert "<script>" not in html
        assert "&lt;script&gt;" in html


class TestBuildPosterFields:
    def test_builds_from_full_payload(self):
        payload = {
            "raw_text": "活动内容正文",
            "title": "校园科技节",
            "summary": "科技节摘要",
            "event_time": "2026-05-10T19:00:00",
            "location": "大礼堂",
            "organizer": "校团委",
            "source_url": "https://example.edu.cn/event",
            "status": "draft",
        }
        result = build_poster_fields(payload)
        assert result["title"] == "校园科技节"
        assert result["raw_text"] == "活动内容正文"
        assert result["summary"] == "科技节摘要"
        assert result["location"] == "大礼堂"
        assert result["organizer"] == "校团委"
        assert result["source_url"] == "https://example.edu.cn/event"
        assert isinstance(result["event_time"], datetime)

    def test_auto_title_from_first_line(self):
        result = build_poster_fields({"raw_text": "这是第一行标题\n这是第二行内容"})
        assert result["title"] == "这是第一行标题"
        assert result["raw_text"] == "这是第一行标题\n这是第二行内容"

    def test_auto_title_truncated_at_80_chars(self):
        long_text = "x" * 100
        result = build_poster_fields({"raw_text": long_text})
        assert len(result["title"]) == 80

    def test_auto_summary(self):
        result = build_poster_fields({"raw_text": "活动内容" * 30})
        assert result["summary"] is not None
        assert len(result["summary"]) <= 120

    def test_fallback_to_existing_poster(self, app, admin_user):
        from app.extensions import db
        from app.models import Poster

        fallback = Poster(
            title="existing title",
            raw_text="existing raw text content",
            summary="existing summary",
            location="existing place",
            organizer="existing org",
            status="draft",
            source_type="manual",
            created_by=admin_user.id,
        )
        db.session.add(fallback)
        db.session.flush()

        result = build_poster_fields({}, fallback=fallback)
        assert result["title"] == "existing title"
        assert result["location"] == "existing place"
        assert result["organizer"] == "existing org"

    def test_payload_overrides_fallback(self, app, admin_user):
        from app.extensions import db
        from app.models import Poster

        fallback = Poster(
            title="existing title",
            raw_text="existing raw text content",
            summary="existing summary",
            location="existing place",
            organizer="existing org",
            status="draft",
            source_type="manual",
            created_by=admin_user.id,
        )
        db.session.add(fallback)
        db.session.flush()

        result = build_poster_fields({"title": "new title"}, fallback=fallback)
        assert result["title"] == "new title"
        assert result["location"] == "existing place"  # from fallback
