"""Integration tests for knowledge API."""


class TestListNodes:
    def test_returns_nodes(self, client, admin_headers, sample_published_poster):
        resp = client.get("/api/knowledge/nodes", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_filter_by_type(self, client, admin_headers):
        resp = client.get("/api/knowledge/nodes?node_type=place", headers=admin_headers)
        assert resp.status_code == 200

    def test_keyword_search(self, client, admin_headers):
        resp = client.get("/api/knowledge/nodes?q=大礼堂", headers=admin_headers)
        assert resp.status_code == 200

    def test_requires_auth(self, client):
        resp = client.get("/api/knowledge/nodes")
        assert resp.status_code == 401


class TestGetNode:
    def test_returns_node_with_posters(self, client, admin_headers, sample_published_poster):
        # First find a node ID from the poster's knowledge
        nodes_resp = client.get("/api/knowledge/nodes", headers=admin_headers)
        nodes = nodes_resp.get_json()["items"]
        if nodes:
            node_id = nodes[0]["id"]
            resp = client.get(f"/api/knowledge/nodes/{node_id}", headers=admin_headers)
            assert resp.status_code == 200
            data = resp.get_json()
            assert "item" in data
            assert "posters" in data["item"]

    def test_returns_404_for_missing(self, client, admin_headers):
        resp = client.get("/api/knowledge/nodes/99999", headers=admin_headers)
        assert resp.status_code == 404


class TestRebuildAllKnowledge:
    def test_rebuilds_knowledge_for_published(self, client, admin_headers, sample_published_poster):
        resp = client.post(
            "/api/knowledge/rebuild",
            json={"status": "published"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "total" in data
        assert "succeeded" in data
        assert "failed" in data

    def test_requires_admin(self, client, publisher_headers):
        resp = client.post("/api/knowledge/rebuild", headers=publisher_headers)
        assert resp.status_code == 403


# =============================================================================
# Corner-case tests
# =============================================================================


class TestRebuildEdgeCases:
    def test_rebuild_with_source_type_filter(self, client, admin_headers, sample_published_poster):
        """Rebuilding with source_type=manual should only process manual posters."""
        r = client.post("/api/knowledge/rebuild",
                        json={"status": "published", "source_type": "manual"},
                        headers=admin_headers)
        assert r.status_code == 200
        assert r.get_json()["total"] >= 1

    def test_rebuild_with_no_matching_posters(self, client, admin_headers):
        """Rebuilding with a status that has no posters returns zero."""
        r = client.post("/api/knowledge/rebuild",
                        json={"status": "nonexistent_status_xyz"},
                        headers=admin_headers)
        assert r.status_code == 200
        assert r.get_json()["total"] == 0

    def test_rebuild_returns_zero_failed_for_clean_data(self, client, admin_headers,
                                                         sample_published_poster):
        r = client.post("/api/knowledge/rebuild", headers=admin_headers)
        assert r.status_code == 200
        assert r.get_json()["failed"] == 0


class TestListNodesEdgeCases:
    def test_filter_nonexistent_type_returns_empty(self, client, admin_headers):
        r = client.get("/api/knowledge/nodes?node_type=nonexistent", headers=admin_headers)
        assert r.status_code == 200
        assert r.get_json()["items"] == []

    def test_keyword_no_match_returns_empty(self, client, admin_headers):
        r = client.get("/api/knowledge/nodes?q=zzzz_no_match_xyz", headers=admin_headers)
        assert r.status_code == 200
        assert r.get_json()["items"] == []

    def test_pagination_is_not_supported(self, client, admin_headers):
        """Nodes endpoint returns all — pagination params should be ignored or OK."""
        r = client.get("/api/knowledge/nodes?page=1&per_page=5", headers=admin_headers)
        assert r.status_code == 200
