"""Integration tests for posters API."""


class TestListPosters:
    def test_returns_empty_list(self, client, admin_headers):
        resp = client.get("/api/posters", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_pagination(self, client, admin_headers):
        resp = client.get("/api/posters?page=1&per_page=5", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["page"] == 1
        assert data["per_page"] == 5

    def test_keyword_search(self, client, admin_headers, sample_published_poster):
        resp = client.get("/api/posters?q=AI", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["items"]) >= 1

    def test_status_filter(self, client, admin_headers, sample_published_poster):
        resp = client.get("/api/posters?status=published", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        for item in data["items"]:
            assert item["status"] == "published"

    def test_requires_auth(self, client):
        resp = client.get("/api/posters")
        assert resp.status_code == 401


class TestCreatePoster:
    def test_creates_draft_poster(self, client, admin_headers):
        resp = client.post(
            "/api/posters",
            json={"raw_text": "校园科技文化节将于5月10日举行"},
            headers=admin_headers,
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["item"]["status"] == "draft"
        assert data["item"]["title"] is not None

    def test_rejects_empty_raw_text(self, client, admin_headers):
        resp = client.post("/api/posters", json={"raw_text": ""}, headers=admin_headers)
        assert resp.status_code == 400

    def test_viewer_cannot_create(self, client, viewer_headers):
        resp = client.post(
            "/api/posters",
            json={"raw_text": "test"},
            headers=viewer_headers,
        )
        assert resp.status_code == 403


class TestGetPoster:
    def test_returns_poster_by_id(self, client, admin_headers, sample_poster):
        resp = client.get(f"/api/posters/{sample_poster.id}", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["item"]["title"] == "2026 校园科技文化节开幕式"

    def test_returns_404_for_missing(self, client, admin_headers):
        resp = client.get("/api/posters/99999", headers=admin_headers)
        assert resp.status_code == 404


class TestUpdatePoster:
    def test_updates_poster_fields(self, client, admin_headers, sample_poster):
        resp = client.put(
            f"/api/posters/{sample_poster.id}",
            json={"title": "更新后的标题"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.get_json()["item"]["title"] == "更新后的标题"

    def test_rejects_empty_raw_text(self, client, admin_headers, sample_poster):
        resp = client.put(
            f"/api/posters/{sample_poster.id}",
            json={"raw_text": ""},
            headers=admin_headers,
        )
        assert resp.status_code == 400


class TestSubmitPoster:
    def test_submits_draft_for_review(self, client, admin_headers, sample_poster):
        resp = client.post(
            f"/api/posters/{sample_poster.id}/submit",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.get_json()["item"]["status"] == "pending_review"

    def test_cannot_submit_non_draft(self, client, admin_headers, sample_poster):
        # First submit
        client.post(f"/api/posters/{sample_poster.id}/submit", headers=admin_headers)
        # Second submit should fail
        resp = client.post(
            f"/api/posters/{sample_poster.id}/submit",
            headers=admin_headers,
        )
        assert resp.status_code == 400


class TestReviewPoster:
    def test_approves_poster(self, client, admin_headers, sample_poster):
        # Submit first
        client.post(f"/api/posters/{sample_poster.id}/submit", headers=admin_headers)
        # Then approve
        resp = client.post(
            f"/api/posters/{sample_poster.id}/review",
            json={"action": "approve", "comment": "looks good"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.get_json()["item"]["status"] == "published"

    def test_rejects_poster(self, client, admin_headers, sample_poster):
        client.post(f"/api/posters/{sample_poster.id}/submit", headers=admin_headers)
        resp = client.post(
            f"/api/posters/{sample_poster.id}/review",
            json={"action": "reject", "comment": "inappropriate"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.get_json()["item"]["status"] == "rejected"

    def test_invalid_action(self, client, admin_headers, sample_poster):
        resp = client.post(
            f"/api/posters/{sample_poster.id}/review",
            json={"action": "delete"},
            headers=admin_headers,
        )
        assert resp.status_code == 400


class TestReviewQueue:
    def test_returns_filtered_queue(self, client, admin_headers, sample_poster):
        resp = client.get("/api/posters/review-queue", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "items" in data

    def test_requires_admin(self, client, publisher_headers):
        resp = client.get("/api/posters/review-queue", headers=publisher_headers)
        assert resp.status_code == 403

    def test_data_source_id_param_ignored(self, client, admin_headers, sample_poster):
        """Regression: data_source_id was removed from review_queue."""
        resp = client.get(
            "/api/posters/review-queue?data_source_id=1",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        # Should work without error, data_source_id param is simply ignored


class TestBulkReview:
    def test_bulk_approve(self, client, admin_headers, sample_poster):
        client.post(f"/api/posters/{sample_poster.id}/submit", headers=admin_headers)
        resp = client.post(
            "/api/posters/bulk-review",
            json={"poster_ids": [sample_poster.id], "action": "approve"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["succeeded"]) == 1

    def test_bulk_reject(self, client, admin_headers, sample_poster):
        client.post(f"/api/posters/{sample_poster.id}/submit", headers=admin_headers)
        resp = client.post(
            "/api/posters/bulk-review",
            json={"poster_ids": [sample_poster.id], "action": "reject"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert len(data := resp.get_json()["succeeded"]) == 1


class TestRelatedPosters:
    def test_returns_related(self, client, admin_headers, sample_published_poster):
        resp = client.get(
            f"/api/posters/{sample_published_poster.id}/related",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "poster" in data
        assert "knowledge_nodes" in data
        assert "related_posters" in data
        assert "poster_links" in data


class TestMergeSource:
    def test_merges_duplicate_source(self, client, admin_headers, app):
        """Create two similar posters and merge one into the other."""
        from app.extensions import db
        from app.models import Poster

        with app.app_context():
            p1 = Poster(
                title="合并测试主海报",
                raw_text="主海报内容",
                summary="摘要",
                status="draft",
                source_type="manual",
                source_url="https://example.edu.cn/main",
                created_by=1,
            )
            p2 = Poster(
                title="重复来源",
                raw_text="重复内容",
                summary="摘要2",
                status="draft",
                source_type="crawl",
                source_url="https://example.edu.cn/dup",
                created_by=1,
            )
            db.session.add_all([p1, p2])
            db.session.commit()
            p1_id = p1.id
            p2_id = p2.id

        resp = client.post(
            f"/api/posters/{p1_id}/merge-source",
            json={"source_poster_id": p2_id},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["merged"]["id"] == p2_id

        # Source poster should be deleted
        resp2 = client.get(f"/api/posters/{p2_id}", headers=admin_headers)
        assert resp2.status_code == 404
