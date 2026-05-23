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

    def test_default_sort_is_relevance(self, client, admin_headers):
        """Default sort must be relevance when not specified."""
        resp = client.get("/api/search/internal?q=AI", headers=admin_headers)
        data = resp.get_json()
        assert data["sort"] == "relevance"
        assert data["order"] == "desc"

    def test_sort_by_title(self, client, admin_headers, sample_published_poster):
        """sort=title must return results ordered by title."""
        resp = client.get(
            "/api/search/internal?q=AI&sort=title&order=asc",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["sort"] == "title"
        assert data["order"] == "asc"

    def test_sort_by_event_time(self, client, admin_headers):
        """sort=event_time must be accepted."""
        resp = client.get(
            "/api/search/internal?q=test&sort=event_time&order=desc",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["sort"] == "event_time"
        assert data["order"] == "desc"

    def test_invalid_sort_falls_back_to_relevance(self, client, admin_headers):
        """Invalid sort value must fall back to relevance."""
        resp = client.get(
            "/api/search/internal?q=test&sort=invalid_sort_xyz&order=invalid",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["sort"] == "relevance"
        assert data["order"] == "desc"


class TestExternalSearch:
    def test_requires_query(self, client, admin_headers):
        resp = client.get("/api/search/external?q=", headers=admin_headers)
        assert resp.status_code == 400

    def test_requires_auth(self, client):
        resp = client.get("/api/search/external?q=test")
        assert resp.status_code == 401

    def test_contract_fields_present(self, client, admin_headers):
        """All contract fields must be present regardless of search outcome."""
        resp = client.get("/api/search/external?q=讲座", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "error" in data
        assert "query" in data
        assert "results" in data
        assert "count" in data
        assert "source" in data
        assert data["source"] == "multi"
        assert data["query"] == "讲座"
        assert isinstance(data["results"], list)
        assert isinstance(data["count"], int)

    def test_error_when_all_engines_unreachable(self, client, admin_headers):
        """Without SearXNG reachable, external search may fall through but
        must return valid contract structure."""
        resp = client.get("/api/search/external?q=讲座", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        # Contract fields must always exist
        assert "error" in data
        assert "results" in data
        assert "count" in data
        assert data["source"] == "multi"
        assert isinstance(data["results"], list)
        assert isinstance(data["count"], int)

    def test_sources_param_is_accepted(self, client, admin_headers):
        """sources query param must not break the endpoint."""
        resp = client.get("/api/search/external?q=讲座&sources=web", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.get_json()["source"] == "multi"
