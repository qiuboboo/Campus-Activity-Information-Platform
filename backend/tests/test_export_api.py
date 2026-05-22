"""Integration tests for export API."""


class TestExportPosters:
    def test_exports_posters_json(self, client, admin_headers, sample_published_poster):
        resp = client.get("/api/export/posters.json", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "items" in data

    def test_requires_auth(self, client):
        resp = client.get("/api/export/posters.json")
        assert resp.status_code == 401


class TestExportKnowledge:
    def test_exports_knowledge_json(self, client, admin_headers, sample_published_poster):
        resp = client.get("/api/export/knowledge.json", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "items" in data


class TestExportCrawlReport:
    def test_exports_crawl_report(self, client, admin_headers):
        resp = client.get("/api/export/crawl-report.json", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "items" in data
