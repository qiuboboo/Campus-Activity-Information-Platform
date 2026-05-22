"""Integration tests for dicts API."""


class TestListDicts:
    def test_returns_entries(self, client, admin_headers):
        resp = client.get("/api/dict/place", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "items" in data
        assert isinstance(data["items"], list)
        assert data["category"] == "place"

    def test_filter_by_query(self, client, admin_headers):
        resp = client.get("/api/dict/place?q=中心", headers=admin_headers)
        assert resp.status_code == 200

    def test_pagination(self, client, admin_headers):
        resp = client.get("/api/dict/place?page=1&per_page=10", headers=admin_headers)
        assert resp.status_code == 200

    def test_requires_auth(self, client):
        resp = client.get("/api/dict/place")
        assert resp.status_code == 401


class TestCreateDict:
    def test_creates_entry(self, client, admin_headers):
        resp = client.post(
            "/api/dict/place",
            json={
                "standard_name": "大学生活动中心",
                "aliases": "大活,活动中心",
            },
            headers=admin_headers,
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["item"]["standard_name"] == "大学生活动中心"

    def test_rejects_missing_standard_name(self, client, admin_headers):
        resp = client.post(
            "/api/dict/place",
            json={"aliases": "test"},
            headers=admin_headers,
        )
        assert resp.status_code == 400

    def test_viewer_cannot_create(self, client, viewer_headers):
        resp = client.post(
            "/api/dict/place",
            json={"standard_name": "test"},
            headers=viewer_headers,
        )
        assert resp.status_code == 403


class TestUpdateDict:
    def test_updates_entry(self, client, admin_headers, app):
        from app.extensions import db
        from app.models import DictEntry

        with app.app_context():
            entry = DictEntry(category="place", standard_name="旧名称")
            db.session.add(entry)
            db.session.commit()
            entry_id = entry.id

        resp = client.put(
            f"/api/dict/place/{entry_id}",
            json={"standard_name": "新名称"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.get_json()["item"]["standard_name"] == "新名称"

    def test_returns_404_for_missing(self, client, admin_headers):
        resp = client.put(
            "/api/dict/place/99999",
            json={"standard_name": "x"},
            headers=admin_headers,
        )
        assert resp.status_code == 404


class TestDeleteDict:
    def test_deletes_entry(self, client, admin_headers, app):
        from app.extensions import db
        from app.models import DictEntry

        with app.app_context():
            entry = DictEntry(category="place", standard_name="待删除")
            db.session.add(entry)
            db.session.commit()
            entry_id = entry.id

        resp = client.delete(f"/api/dict/place/{entry_id}", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.get_json()["deleted"] is True

    def test_returns_404_for_missing(self, client, admin_headers):
        resp = client.delete("/api/dict/place/99999", headers=admin_headers)
        assert resp.status_code == 404


class TestSeedDict:
    def test_seeds_builtin_entries(self, client, admin_headers):
        resp = client.post("/api/dict/seed", headers=admin_headers)
        assert resp.status_code in (200, 201)
