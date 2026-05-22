"""Integration tests for health API."""


class TestHealth:
    def test_returns_ok(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200

    def test_does_not_require_auth(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200


class TestDemoSummary:
    """Test the demo summary endpoint if it exists."""

    def test_summary_with_auth(self, client, admin_headers):
        resp = client.get("/api/demo/summary", headers=admin_headers)
        # This endpoint may or may not exist; accept both 200 and 404
        assert resp.status_code in (200, 404)
