"""Integration tests for home/featured API."""


class TestHomeFeatured:
    def test_returns_empty_when_no_published(self, client):
        resp = client.get("/api/home/featured")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "items" in data
        assert data["items"] == []

    def test_returns_top_3_published(self, client, sample_published_poster):
        resp = client.get("/api/home/featured")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["items"]) >= 1
        item = data["items"][0]
        assert item["id"] == sample_published_poster.id
        assert item["title"] == "AI 创新应用讲座"
        assert item["location"] == "大学生活动中心大礼堂"
        assert item["organizer"] == "计算机学院"
        assert item["activity_type"] is None  # not set in fixture

    def test_ignores_drafts(self, client, sample_poster):
        """Draft posters should not appear in featured."""
        resp = client.get("/api/home/featured")
        data = resp.get_json()
        ids = [item["id"] for item in data["items"]]
        assert sample_poster.id not in ids

    def test_public_no_auth_required(self, client):
        resp = client.get("/api/home/featured")
        assert resp.status_code == 200
