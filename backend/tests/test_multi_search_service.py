"""Unit tests for multi_search_service."""

from unittest.mock import ANY, MagicMock, patch


class TestSearch:
    """Test multi_search_service.search() with mocked SearXNG and Sogou."""

    @patch("app.services.weixin_search_service.sogou_search")
    @patch("app.services.multi_search_service.requests")
    def test_returns_results_from_searxng(self, mock_requests, mock_sogou, app):
        """SearXNG results are normalised and returned."""
        mock_requests.get.return_value.status_code = 200
        mock_requests.get.return_value.json.return_value = {
            "results": [
                {
                    "title": "校园科技节",
                    "content": "2026年科技节活动",
                    "engine": "baidu",
                    "url": "https://www.sysu.edu.cn/techfest",
                },
                {
                    "title": "AI 创新讲座",
                    "content": "AI前沿技术讲座",
                    "engine": "google",
                    "url": "https://example.com/ai-talk",
                },
            ]
        }

        from app.services.multi_search_service import search

        result = search("科技节", engines=["baidu", "google"])

        assert result["error"] is None
        assert len(result["results"]) == 2
        assert result["results"][0]["title"] == "校园科技节"
        assert result["results"][0]["source"] == "baidu"
        assert result["results"][1]["source"] == "google"
        mock_requests.get.assert_called_once()
        assert mock_sogou.call_count == 0  # Sogou not in engines

    @patch("app.services.weixin_search_service.sogou_search")
    @patch("app.services.multi_search_service.requests")
    def test_includes_sogou_results(self, mock_requests, mock_sogou, app):
        """When sogou is in engines, sogou results are included."""
        mock_requests.get.return_value.status_code = 200
        mock_requests.get.return_value.json.return_value = {
            "results": [
                {
                    "title": "Google Result",
                    "content": "Desc",
                    "engine": "google",
                    "url": "https://example.com/1",
                }
            ]
        }
        mock_sogou.return_value = [
            {"title": "微信文章", "sogou_url": "https://weixin.sogou.com/article"},
        ]

        from app.services.multi_search_service import search

        result = search("讲座", engines=["google", "sogou"])

        assert len(result["results"]) == 2
        titles = {r["title"] for r in result["results"]}
        assert "微信文章" in titles
        assert "Google Result" in titles
        mock_sogou.assert_called_once_with("讲座", page=1)

    @patch("app.services.weixin_search_service.sogou_search")
    @patch("app.services.multi_search_service.requests")
    def test_deduplicates_by_url(self, mock_requests, mock_sogou, app):
        """Duplicate URLs are removed, first occurrence kept."""
        mock_requests.get.return_value.status_code = 200
        mock_requests.get.return_value.json.return_value = {
            "results": [
                {
                    "title": "Same URL",
                    "content": "First",
                    "engine": "google",
                    "url": "https://example.com/dup",
                },
                {
                    "title": "Same URL Again",
                    "content": "Second",
                    "engine": "bing",
                    "url": "https://example.com/dup",
                },
            ]
        }

        from app.services.multi_search_service import search

        result = search("test", engines=["google", "bing"])

        assert len(result["results"]) == 1
        assert result["results"][0]["title"] == "Same URL"

    @patch("app.services.weixin_search_service.sogou_search")
    @patch("app.services.multi_search_service.requests")
    def test_empty_query_returns_empty(self, mock_requests, mock_sogou, app):
        """Empty or whitespace-only query returns immediately with no error."""
        from app.services.multi_search_service import search

        result = search("  ", engines=["google"])
        assert result["results"] == []
        assert result["error"] is None
        mock_requests.get.assert_not_called()

    @patch("app.services.weixin_search_service.sogou_search")
    @patch("app.services.multi_search_service.requests")
    def test_searxng_unavailable(self, mock_requests, mock_sogou, app):
        """When SearXNG is unreachable, returns empty with error."""
        # Mock a connection failure — non-200 response
        bad_resp = MagicMock()
        bad_resp.status_code = 503
        mock_requests.get.return_value = bad_resp

        from app.services.multi_search_service import search

        result = search("test", engines=["google"])
        assert result["results"] == []
        assert result["error"] is not None

    @patch("app.services.weixin_search_service.sogou_search")
    @patch("app.services.multi_search_service.requests")
    def test_passes_engines_to_searxng(self, mock_requests, mock_sogou, app):
        """Engine names are passed as comma-separated to SearXNG."""
        mock_requests.get.return_value.status_code = 200
        mock_requests.get.return_value.json.return_value = {"results": []}

        from app.services.multi_search_service import search

        search("test", engines=["baidu", "duckduckgo"])

        call_args = mock_requests.get.call_args
        params = call_args[1]["params"]
        assert params["engines"] == "baidu,duckduckgo"


class TestNormaliseResult:
    def test_standard_fields(self):
        from app.services.multi_search_service import _normalise_result

        raw = {
            "title": " Test Title ",
            "content": " Some summary ",
            "engine": "google",
            "url": "https://example.com",
        }
        norm = _normalise_result(raw)
        assert norm["title"] == "Test Title"
        assert norm["summary"] == "Some summary"
        assert norm["source"] == "google"
        assert norm["url"] == "https://example.com"

    def test_missing_url_becomes_none(self):
        from app.services.multi_search_service import _normalise_result

        norm = _normalise_result({"title": "No URL", "content": ""}, engine="bing")
        assert norm["url"] is None


class TestDeduplicate:
    def test_removes_duplicates(self):
        from app.services.multi_search_service import _deduplicate

        items = [
            {"url": "https://a.com/1", "title": "First"},
            {"url": "https://a.com/1", "title": "Duplicate"},
            {"url": "https://b.com/2", "title": "Unique"},
        ]
        deduped = _deduplicate(items)
        assert len(deduped) == 2
        assert deduped[0]["title"] == "First"
        assert deduped[1]["title"] == "Unique"

    def test_handles_empty_urls(self):
        from app.services.multi_search_service import _deduplicate

        items = [
            {"url": None, "title": "No URL"},
            {"url": "", "title": "Empty URL"},
        ]
        deduped = _deduplicate(items)
        assert len(deduped) == 2
