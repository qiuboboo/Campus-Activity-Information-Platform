from app.services.crawler_service import _looks_like_listing_title, _parse_content, _summarize_activity


def test_generic_content_extractor_removes_page_chrome():
    html = """<html><body><header>中山大学 首页 新闻 联系我们</header><nav>导航 活动中心</nav><main><article><h1>人工智能讲座</h1><p>计算机学院将于2026年8月1日举办人工智能讲座。</p><p>地点：东校园报告厅，欢迎报名参加。</p></article></main><footer>版权所有 网站地图</footer></body></html>"""
    text = _parse_content(html, None)
    assert "人工智能讲座" in text
    assert "版权所有" not in text
    assert "导航" not in text


def test_summary_is_concise_and_event_oriented():
    raw = "学院新闻\n欢迎访问\n人工智能讲座将于2026年8月1日14:00在东校园报告厅举行。\n活动包含技术分享和交流环节，欢迎全校学生报名参加。\n版权所有"
    summary = _summarize_activity(raw)
    assert "人工智能讲座" in summary
    assert len(summary) <= 180


def test_short_activity_section_title_is_recognised_as_a_listing():
    assert _looks_like_listing_title("学术活动 | 中山大学计算机学院")
    assert _looks_like_listing_title("精品活动｜青年时空")
    assert not _looks_like_listing_title("人工智能讲座：大模型技术分享")
