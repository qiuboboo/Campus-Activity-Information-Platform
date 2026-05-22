"""Unit tests for quality_service."""

from datetime import datetime

from app.models import Poster
from app.services.quality_service import score_poster


def _make_poster(**kwargs):
    defaults = {
        "title": "测试活动标题",
        "raw_text": "这是一个测试活动的详细描述内容，包含足够长的正文，" * 8,
        "summary": "测试活动摘要",
        "event_time": datetime.fromisoformat("2026-05-10T19:00:00"),
        "location": "大礼堂",
        "organizer": "校团委",
        "source_url": "https://example.edu.cn/test",
        "status": "draft",
        "source_type": "manual",
        "created_by": 1,
    }
    defaults.update(kwargs)
    return Poster(**defaults)


class TestScorePoster:
    def test_full_poster_scores_100(self):
        poster = _make_poster()
        score, notes = score_poster(poster)
        assert score == 100
        assert not notes

    def test_official_source_bonus(self):
        poster = _make_poster()
        score, notes = score_poster(poster, is_official_source=True)
        assert score == 100  # capped at 100
        assert "官方来源加分" in notes

    def test_empty_title_penalty(self):
        poster = _make_poster(title="")
        score, notes = score_poster(poster)
        assert score <= 70
        assert "标题为空" in notes

    def test_short_title_penalty(self):
        poster = _make_poster(title="短")
        score, notes = score_poster(poster)
        assert "标题过短" in notes
        assert score < 100

    def test_missing_summary_penalty(self):
        poster = _make_poster(summary="")
        score, notes = score_poster(poster)
        assert "摘要为空" in notes

    def test_missing_event_time_penalty(self):
        poster = _make_poster(event_time=None)
        score, notes = score_poster(poster)
        assert "缺少活动时间" in notes

    def test_missing_location_penalty(self):
        poster = _make_poster(location=None)
        score, notes = score_poster(poster)
        assert "缺少活动地点" in notes

    def test_missing_source_url_penalty(self):
        poster = _make_poster(source_url=None)
        score, notes = score_poster(poster)
        assert "缺少来源链接" in notes

    def test_short_raw_text_penalty(self):
        poster = _make_poster(raw_text="太短")
        score, notes = score_poster(poster)
        assert "正文过短" in notes

    def test_moderately_short_raw_text_penalty(self):
        poster = _make_poster(raw_text="a" * 100)
        score, notes = score_poster(poster)
        assert "正文偏短" in notes

    def test_duplicate_penalty(self):
        poster = _make_poster()
        score, notes = score_poster(poster, is_suspected_duplicate=True)
        assert "疑似重复" in notes
        assert score < 100

    def test_score_clamped_to_range(self):
        poster = _make_poster(title="", summary="", event_time=None, location=None, source_url=None, raw_text="")
        score, notes = score_poster(poster, is_suspected_duplicate=True)
        assert 0 <= score <= 100
