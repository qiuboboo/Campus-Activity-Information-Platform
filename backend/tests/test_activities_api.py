"""
Activities API (蓝图前缀 /api/activities)
用例覆盖: 列表/创建/详情/更新/提交/报名/收藏 的 happy path + 关键 error case
"""
import pytest

from app.models import Poster


class TestListActivities:
    def test_returns_published_only(self, client, sample_published_poster, sample_poster):
        resp = client.get("/api/activities")
        assert resp.status_code == 200
        assert resp.json["total"] == 1

    def test_keyword_filter(self, client, sample_published_poster):
        resp = client.get("/api/activities?q=AI")
        assert resp.status_code == 200
        assert resp.json["total"] >= 1
        resp = client.get("/api/activities?q=NO_MATCH_ZZZ")
        assert resp.status_code == 200
        assert resp.json["total"] == 0

    def test_custom_page_size(self, client, sample_published_poster):
        resp = client.get("/api/activities?per_page=1&page=1")
        assert resp.status_code == 200
        assert resp.json["per_page"] == 1


class TestCreateActivity:
    def test_requires_raw_text(self, client, publisher_headers):
        resp = client.post("/api/activities", headers=publisher_headers, json={"title": "无正文"})
        assert resp.status_code == 400

    def test_publisher_creates_draft(self, client, publisher_headers):
        resp = client.post("/api/activities", headers=publisher_headers, json={
            "title": "新活动", "raw_text": "测试正文", "summary": "测试摘要",
            "activity_type": "讲座", "location": "南校园", "organizer": "校团委",
            "cover_image_url": "https://example.edu/poster.jpg",
        })
        assert resp.status_code == 201
        data = resp.json
        assert data["title"] == "新活动"
        assert data["status"] == "draft"
        assert data["cover_image_url"] == "https://example.edu/poster.jpg"

    def test_viewer_cannot_create(self, client, viewer_headers):
        resp = client.post("/api/activities", headers=viewer_headers, json={"title": "x", "raw_text": "y"})
        assert resp.status_code == 403


class TestGetDetail:
    def test_published_detail_includes_tags(self, client, sample_published_poster):
        resp = client.get(f"/api/activities/{sample_published_poster.id}")
        assert resp.status_code == 200
        assert resp.json["title"] == sample_published_poster.title
        assert "tags" in resp.json

    def test_hides_non_published_from_guest(self, client, sample_poster):
        resp = client.get(f"/api/activities/{sample_poster.id}")
        assert resp.status_code == 404


class TestUpdateActivity:
    def test_publisher_updates_own(self, client, publisher_headers, publisher_user):
        from app.extensions import db
        post = Poster(title="旧标题", raw_text="旧正文", summary="旧摘要", created_by=publisher_user.id, status="draft", source_type="manual")
        db.session.add(post); db.session.commit()
        resp = client.put(f"/api/activities/{post.id}", headers=publisher_headers, json={"title": "新标题"})
        assert resp.status_code == 200


class TestSubmitReview:
    def test_draft_can_submit(self, client, publisher_headers, publisher_user):
        from app.extensions import db
        post = Poster(title="待提交", raw_text="内容", summary="摘要", created_by=publisher_user.id, status="draft", source_type="manual")
        db.session.add(post); db.session.commit()
        resp = client.post(f"/api/activities/{post.id}/submit-review", headers=publisher_headers)
        assert resp.status_code == 200
        assert resp.json["status"] == "pending_review"


class TestRegister:
    def test_register_without_redis_returns_503(self, app, client, publisher_headers, sample_published_poster):
        resp = client.post(f"/api/activities/{sample_published_poster.id}/register", headers=publisher_headers)
        assert resp.status_code == 503


class TestFavorite:
    def test_favorite_without_redis_returns_503(self, app, client, viewer_headers, sample_published_poster):
        resp = client.post(f"/api/activities/{sample_published_poster.id}/favorite", headers=viewer_headers)
        assert resp.status_code == 503
