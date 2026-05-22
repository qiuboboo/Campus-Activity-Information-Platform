"""Integration tests for audit logs API."""


class TestListAuditLogs:
    def test_returns_logs(self, client, admin_headers):
        resp = client.get("/api/audit-logs", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_logs_appear_after_poster_action(self, client, admin_headers, sample_poster):
        """After submitting a poster, audit logs should appear."""
        client.post(
            f"/api/posters/{sample_poster.id}/submit",
            headers=admin_headers,
        )
        resp = client.get("/api/audit-logs", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        # At least one log should exist (the submit action)
        assert len(data["items"]) >= 1

    def test_requires_auth(self, client):
        resp = client.get("/api/audit-logs")
        assert resp.status_code == 401
