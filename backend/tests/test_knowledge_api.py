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
