"""Integration tests for search API."""


class TestInternalSearch:
    def test_searches_posters(self, client, admin_headers, sample_published_poster):
        resp = client.get("/api/search/internal?q=AI", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "items" in data
        assert "query" in data
        assert data["query"] == "AI"

    def test_searches_with_no_results(self, client, admin_headers):
        resp = client.get("/api/search/internal?q=zzz_no_match_xyz", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["items"] == []

    def test_empty_query_returns_empty(self, client, admin_headers):
        resp = client.get("/api/search/internal?q=", headers=admin_headers)
        assert resp.status_code == 200

    def test_requires_auth(self, client):
        resp = client.get("/api/search/internal?q=test")
        assert resp.status_code == 401

    def test_search_mode_is_fulltext(self, client, admin_headers):
        resp = client.get("/api/search/internal?q=test", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["search_mode"] == "fulltext"


class TestExternalSearch:
    def test_requires_query(self, client, admin_headers):
        resp = client.get("/api/search/external?q=", headers=admin_headers)
        assert resp.status_code == 400

    def test_requires_auth(self, client):
        resp = client.get("/api/search/external?q=test")
        assert resp.status_code == 401
