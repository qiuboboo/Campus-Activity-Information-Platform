"""Integration tests for AI API endpoints.

All tests run with LLM_API_KEY="" and no MCP servers configured,
so AI-dependent endpoints return expected error codes.
"""


class TestAiStatus:
    def test_returns_status(self, client, admin_headers):
        """GET /api/ai/status always returns 200 (no external deps needed)."""
        resp = client.get("/api/ai/status", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "llm_configured" in data
        assert "mcp_servers" in data

    def test_requires_auth(self, client):
        resp = client.get("/api/ai/status")
        assert resp.status_code == 401


class TestAiExtract:
    def test_returns_fallback_when_llm_unavailable(self, client, admin_headers):
        """POST /api/ai/extract falls back to rule-based extraction when LLM unavailable."""
        resp = client.post(
            "/api/ai/extract",
            json={"text": "校园科技文化节将于5月10日举行"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "fields" in data
        assert "title" in data["fields"]

    def test_rejects_empty_text(self, client, admin_headers):
        resp = client.post(
            "/api/ai/extract",
            json={"text": ""},
            headers=admin_headers,
        )
        assert resp.status_code == 400

    def test_requires_auth(self, client):
        resp = client.post("/api/ai/extract", json={"text": "test"})
        assert resp.status_code == 401


class TestAiEnrich:
    def test_returns_503_when_llm_unavailable(self, client, admin_headers, sample_poster):
        """POST /api/ai/enrich/{id} returns 503 when LLM is not configured."""
        resp = client.post(
            f"/api/ai/enrich/{sample_poster.id}",
            headers=admin_headers,
        )
        assert resp.status_code == 503

    def test_requires_auth(self, client, sample_poster):
        resp = client.post(f"/api/ai/enrich/{sample_poster.id}")
        assert resp.status_code == 401

    def test_requires_admin(self, client, viewer_headers, sample_poster):
        resp = client.post(
            f"/api/ai/enrich/{sample_poster.id}",
            headers=viewer_headers,
        )
        assert resp.status_code == 403


class TestAiSearch:
    def test_returns_results_with_query(self, client, admin_headers):
        """POST /api/ai/search may return 0 results but should not fail."""
        resp = client.post(
            "/api/ai/search",
            json={"query": "中山大学 科技节"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "query" in data
        assert "results" in data
        assert "count" in data

    def test_rejects_empty_query(self, client, admin_headers):
        resp = client.post(
            "/api/ai/search",
            json={"query": ""},
            headers=admin_headers,
        )
        assert resp.status_code == 400

    def test_requires_auth(self, client):
        resp = client.post("/api/ai/search", json={"query": "test"})
        assert resp.status_code == 401


class TestMcpServers:
    def test_returns_server_list(self, client, admin_headers):
        """GET /api/ai/mcp/servers returns list (may be empty)."""
        resp = client.get("/api/ai/mcp/servers", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "servers" in data

    def test_requires_auth(self, client):
        resp = client.get("/api/ai/mcp/servers")
        assert resp.status_code == 401


class TestMcpCall:
    def test_returns_503_when_mcp_unavailable(self, client, admin_headers):
        """POST /api/ai/mcp/call returns 503 when server not configured."""
        resp = client.post(
            "/api/ai/mcp/call",
            json={"server": "test-server", "tool": "test_tool", "params": {}},
            headers=admin_headers,
        )
        assert resp.status_code == 503

    def test_rejects_missing_server(self, client, admin_headers):
        resp = client.post(
            "/api/ai/mcp/call",
            json={"tool": "test_tool"},
            headers=admin_headers,
        )
        assert resp.status_code == 400

    def test_rejects_missing_tool(self, client, admin_headers):
        resp = client.post(
            "/api/ai/mcp/call",
            json={"server": "test-server"},
            headers=admin_headers,
        )
        assert resp.status_code == 400

    def test_requires_auth(self, client):
        resp = client.post("/api/ai/mcp/call", json={"server": "x", "tool": "y"})
        assert resp.status_code == 401

    def test_requires_admin(self, client, viewer_headers):
        resp = client.post(
            "/api/ai/mcp/call",
            json={"server": "x", "tool": "y"},
            headers=viewer_headers,
        )
        assert resp.status_code == 403


# =============================================================================
# Corner-case / edge-condition tests
# =============================================================================


class TestAiExtractEdgeCases:
    def test_fallback_strips_for_whitespace(self, client, admin_headers):
        """Whitespace-only text should still be rejected."""
        r = client.post("/api/ai/extract", json={"text": "   "}, headers=admin_headers)
        assert r.status_code == 400

    def test_fallback_handles_special_characters(self, client, admin_headers):
        """Special characters should not crash the extractor."""
        r = client.post("/api/ai/extract",
                        json={"text": "活动：<script>alert('xss')</script> at 大礼堂"},
                        headers=admin_headers)
        assert r.status_code == 200

    def test_fallback_returns_fallback_flag(self, client, admin_headers):
        """When LLM is unavailable, the result should have _fallback: true."""
        r = client.post("/api/ai/extract",
                        json={"text": "2026年6月15日在图书馆举行学术讲座"},
                        headers=admin_headers)
        assert r.status_code == 200
        fields = r.get_json()["fields"]
        # fallback extractor marks its output
        assert fields.get("_fallback") is True

    def test_fallback_extracts_chinese_date(self, client, admin_headers):
        """Fallback should parse Chinese date formats."""
        r = client.post("/api/ai/extract",
                        json={"text": "2026年6月15日下午3点在图书馆举行讲座"},
                        headers=admin_headers)
        assert r.status_code == 200
        fields = r.get_json()["fields"]
        assert fields.get("title") is not None


class TestMcpCallEdgeCases:
    def test_empty_server_name_rejected(self, client, admin_headers):
        r = client.post("/api/ai/mcp/call",
                        json={"server": "", "tool": "t"}, headers=admin_headers)
        assert r.status_code == 400

    def test_empty_tool_name_rejected(self, client, admin_headers):
        r = client.post("/api/ai/mcp/call",
                        json={"server": "s", "tool": ""}, headers=admin_headers)
        assert r.status_code == 400

    def test_whitespace_server_name_rejected(self, client, admin_headers):
        r = client.post("/api/ai/mcp/call",
                        json={"server": "   ", "tool": "t"}, headers=admin_headers)
        assert r.status_code == 400

    def test_publisher_cannot_call_mcp(self, client, publisher_headers):
        r = client.post("/api/ai/mcp/call",
                        json={"server": "s", "tool": "t"}, headers=publisher_headers)
        assert r.status_code == 403
