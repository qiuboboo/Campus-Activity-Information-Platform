"""Integration tests for data sources API."""


class TestListDataSources:
    def test_returns_sources(self, client, admin_headers, sample_data_source):
        resp = client.get("/api/data-sources", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_requires_auth(self, client):
        resp = client.get("/api/data-sources")
        assert resp.status_code == 401


class TestCreateDataSource:
    def test_creates_source(self, client, admin_headers):
        resp = client.post(
            "/api/data-sources",
            json={
                "name": "新数据源",
                "base_url": "https://news.example.edu.cn",
                "allowed_domains": "news.example.edu.cn",
            },
            headers=admin_headers,
        )
        assert resp.status_code == 201
        assert resp.get_json()["name"] == "新数据源"

    def test_rejects_missing_name(self, client, admin_headers):
        resp = client.post(
            "/api/data-sources",
            json={"base_url": "https://example.edu.cn"},
            headers=admin_headers,
        )
        assert resp.status_code == 400

    def test_rejects_missing_base_url(self, client, admin_headers):
        resp = client.post(
            "/api/data-sources",
            json={"name": "test"},
            headers=admin_headers,
        )
        assert resp.status_code == 400

    def test_viewer_cannot_create(self, client, viewer_headers):
        resp = client.post(
            "/api/data-sources",
            json={"name": "x", "base_url": "https://example.com"},
            headers=viewer_headers,
        )
        assert resp.status_code == 403


class TestGetDataSource:
    def test_returns_source(self, client, admin_headers, sample_data_source):
        resp = client.get(
            f"/api/data-sources/{sample_data_source.id}",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.get_json()["name"] == "校园网通知公告"

    def test_returns_404(self, client, admin_headers):
        resp = client.get("/api/data-sources/99999", headers=admin_headers)
        assert resp.status_code == 404


class TestUpdateDataSource:
    def test_updates_source(self, client, admin_headers, sample_data_source):
        resp = client.put(
            f"/api/data-sources/{sample_data_source.id}",
            json={"name": "更新的数据源名"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.get_json()["name"] == "更新的数据源名"


class TestDataSourceLogs:
    def test_returns_logs(self, client, admin_headers, sample_data_source):
        resp = client.get(
            f"/api/data-sources/{sample_data_source.id}/logs",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert "items" in resp.get_json()


class TestDeleteDataSource:
    def test_deletes_source(self, client, admin_headers, sample_data_source):
        resp = client.delete(
            f"/api/data-sources/{sample_data_source.id}",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

        # Verify it's gone
        resp2 = client.get(
            f"/api/data-sources/{sample_data_source.id}",
            headers=admin_headers,
        )
        assert resp2.status_code == 404

    def test_returns_404(self, client, admin_headers):
        resp = client.delete("/api/data-sources/99999", headers=admin_headers)
        assert resp.status_code == 404

    def test_requires_admin(self, client, viewer_headers, sample_data_source):
        resp = client.delete(
            f"/api/data-sources/{sample_data_source.id}",
            headers=viewer_headers,
        )
        assert resp.status_code == 403

    def test_requires_auth(self, client, sample_data_source):
        resp = client.delete(f"/api/data-sources/{sample_data_source.id}")
        assert resp.status_code == 401
