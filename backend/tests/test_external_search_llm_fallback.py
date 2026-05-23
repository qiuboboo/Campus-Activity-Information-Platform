"""Tests for external search LLM fallback path.

These mock both SearXNG and _llm_chat to verify the fallback logic
in ai_service.search_external().
"""

from unittest.mock import patch


class TestExternalSearchLlmFallback:
    """Test the LLM fallback path when multi-search returns no results."""

    @patch("app.services.ai_service._llm_chat")
    @patch("app.services.multi_search_service.search")
    def test_falls_back_to_llm_when_multi_search_empty(
        self, mock_multi, mock_llm, app
    ):
        """When multi-search returns empty and LLM source requested, must call LLM."""
        app.config["LLM_API_KEY"] = "test-key"
        mock_multi.return_value = {"results": [], "error": None}
        mock_llm.return_value = [
            {"title": "LLM Result", "summary": "From LLM", "source": "test", "url": None},
        ]

        from app.services.ai_service import search_external

        result = search_external("test", sources=["web", "llm"])
        assert len(result["results"]) == 1
        assert result["results"][0]["title"] == "LLM Result"
        assert result["error"] is None
        mock_llm.assert_called_once()

    @patch("app.services.ai_service._llm_chat")
    @patch("app.services.multi_search_service.search")
    def test_llm_returns_none(self, mock_multi, mock_llm, app):
        """When LLM returns None, must report error."""
        app.config["LLM_API_KEY"] = "test-key"
        mock_multi.return_value = {"results": [], "error": None}
        mock_llm.return_value = None

        from app.services.ai_service import search_external

        result = search_external("test", sources=["web", "llm"])
        assert result["results"] == []
        assert result["error"] is not None
        assert "unavailable" in result["error"].lower()

    @patch("app.services.ai_service._llm_chat")
    @patch("app.services.multi_search_service.search")
    def test_llm_returns_invalid_format(self, mock_multi, mock_llm, app):
        """When LLM returns a non-list, must report format error."""
        app.config["LLM_API_KEY"] = "test-key"
        mock_multi.return_value = {"results": [], "error": None}
        mock_llm.return_value = "not a list"

        from app.services.ai_service import search_external

        result = search_external("test", sources=["web", "llm"])
        assert result["results"] == []
        assert "format" in result["error"].lower()

    @patch("app.services.ai_service._llm_chat")
    @patch("app.services.multi_search_service.search")
    def test_llm_returns_empty_list(self, mock_multi, mock_llm, app):
        """When LLM returns empty list, must return empty results with no error."""
        app.config["LLM_API_KEY"] = "test-key"
        mock_multi.return_value = {"results": [], "error": None}
        mock_llm.return_value = []

        from app.services.ai_service import search_external

        result = search_external("test", sources=["web", "llm"])
        assert result["results"] == []
        assert result["error"] is None

    @patch("app.services.multi_search_service.search")
    def test_skips_llm_when_not_requested(self, mock_multi, app):
        """When sources doesn't include 'llm', must skip LLM fallback."""
        mock_multi.return_value = {"results": [], "error": "All engines returned no results"}

        from app.services.ai_service import search_external

        result = search_external("test", sources=["web"])
        assert result["results"] == []
        assert result["error"] is not None

    @patch("app.services.ai_service._llm_chat")
    @patch("app.services.multi_search_service.search")
    def test_skips_llm_when_multi_search_succeeds(self, mock_multi, mock_llm, app):
        """When multi-search returns results, must NOT call LLM."""
        mock_multi.return_value = {
            "results": [{"title": "Real", "summary": "", "source": "baidu", "url": "https://a.com"}],
            "error": None,
        }

        from app.services.ai_service import search_external

        result = search_external("test", sources=["web", "llm"])
        assert len(result["results"]) == 1
        assert result["results"][0]["source"] == "baidu"
        mock_llm.assert_not_called()
