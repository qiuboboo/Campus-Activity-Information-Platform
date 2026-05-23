"""Tests for search_logger.py — structured JSON search observability."""

import json
import logging
from unittest.mock import ANY, patch

import pytest

from app.utils.search_logger import _get_request_id, _get_user_id, log_search, mask_query


class TestMaskQuery:
    """Query masking (privacy-safe logging)."""

    def test_empty_string(self):
        assert mask_query("") == ""

    def test_ascii_short(self):
        """≤ 3 chars: returned as-is."""
        assert mask_query("ab") == "ab"
        assert mask_query("abc") == "abc"

    def test_ascii_long(self):
        """> 3 chars: first + *** + last."""
        assert mask_query("hello") == "h***o"

    def test_chinese_short(self):
        """≤ 2 CJK chars: returned as-is."""
        assert mask_query("讲座") == "讲座"

    def test_chinese_long(self):
        """> 2 CJK chars: first char + *** + last char."""
        result = mask_query("校园科技文化节")
        # First CJK char is "校", last string char is "节"
        assert result == "校***节"

    def test_mixed_short_cjk_passes_through(self):
        """≤ 2 CJK chars with surrounding ASCII → passed through."""
        assert mask_query("AI讲座2026") == "AI讲座2026"

    def test_mixed_long_cjk_masked(self):
        """> 2 CJK chars with surrounding ASCII → masked at string level."""
        result = mask_query("AI创新应用讲座2026")
        assert result == "A***6"


class TestLogSearch:
    """Structured JSON log emission."""

    @pytest.fixture
    def capture_log(self, caplog):
        caplog.set_level(logging.INFO, logger="search")
        return caplog

    def test_emits_valid_json_line(self, capture_log):
        log_search(
            endpoint="internal",
            query="讲座",
            latency_ms=12.34,
            hit_count=3,
            result_types={"poster": 2, "knowledge_node": 1},
            search_mode="fulltext",
            sort="relevance",
            order="desc",
        )
        assert len(capture_log.records) == 1
        record = capture_log.records[0]
        # Parse the message as JSON
        parsed = json.loads(record.message)
        assert isinstance(parsed, dict)

    def test_contains_all_required_fields(self, capture_log):
        log_search(
            endpoint="external",
            query="科技节",
            latency_ms=45.6,
            hit_count=0,
            result_types={},
            search_mode="multi",
            error="All search engines returned no results",
        )
        parsed = json.loads(capture_log.records[0].message)
        for field in [
            "endpoint", "query_masked", "latency_ms", "hit_count",
            "result_types", "search_mode", "sort", "order",
            "error", "request_id", "user_id", "timestamp",
        ]:
            assert field in parsed, f"missing field: {field}"

    def test_query_is_masked(self, capture_log):
        log_search(
            endpoint="internal",
            query="校园科技文化节开幕式",
            latency_ms=10.0,
            hit_count=5,
            result_types={"poster": 5},
            search_mode="fulltext",
        )
        parsed = json.loads(capture_log.records[0].message)
        # Must NOT contain full query
        assert "校园科技文化节开幕式" not in parsed["query_masked"]
        # Masked form should be shorter
        assert len(parsed["query_masked"]) < len("校园科技文化节开幕式")

    def test_latency_rounded_to_2_decimal(self, capture_log):
        log_search(
            endpoint="internal",
            query="test",
            latency_ms=123.456789,
            hit_count=0,
            result_types={},
            search_mode="fulltext",
        )
        parsed = json.loads(capture_log.records[0].message)
        assert parsed["latency_ms"] == 123.46

    def test_empty_query_logs_search_mode_none(self, capture_log):
        log_search(
            endpoint="internal",
            query="",
            latency_ms=0,
            hit_count=0,
            result_types={},
            search_mode="none",
        )
        parsed = json.loads(capture_log.records[0].message)
        assert parsed["query_masked"] == ""
        assert parsed["search_mode"] == "none"

    def test_external_error_preserved(self, capture_log):
        log_search(
            endpoint="external",
            query="讲座",
            latency_ms=5000,
            hit_count=0,
            result_types={},
            search_mode="multi",
            error="Search engines unavailable and LLM fallback failed",
        )
        parsed = json.loads(capture_log.records[0].message)
        assert "unavailable" in parsed["error"]


class TestRequestContext:
    """request_id and user_id extraction."""

    def test_get_request_id_outside_flask(self):
        assert _get_request_id() == "unknown"

    def test_get_user_id_outside_flask(self):
        assert _get_user_id() is None
