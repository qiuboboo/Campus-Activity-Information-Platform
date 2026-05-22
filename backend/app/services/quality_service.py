from ..models import Poster


def score_poster(
    poster: Poster,
    is_suspected_duplicate: bool = False,
    is_official_source: bool = False,
) -> tuple[int, list[str]]:
    """Score a poster's quality. Returns (score, notes)."""
    score = 100
    notes = []

    # Title empty or too short
    title = (poster.title or "").strip()
    if not title:
        score -= 30
        notes.append("标题为空")
    elif len(title) < 5:
        score -= 15
        notes.append("标题过短")

    # Summary check
    summary = (poster.summary or "").strip()
    if not summary:
        score -= 15
        notes.append("摘要为空")

    # Event time
    if poster.event_time is None:
        score -= 15
        notes.append("缺少活动时间")

    # Location
    if not poster.location:
        score -= 10
        notes.append("缺少活动地点")

    # Source URL
    if not poster.source_url:
        score -= 10
        notes.append("缺少来源链接")

    # Raw text too short
    raw = (poster.raw_text or "").strip()
    if len(raw) < 50:
        score -= 10
        notes.append("正文过短")
    elif len(raw) < 200:
        score -= 5
        notes.append("正文偏短")

    # Suspected duplicate
    if is_suspected_duplicate:
        score -= 20
        notes.append("疑似重复")

    # Official source bonus
    if is_official_source:
        score += 10
        notes.append("官方来源加分")

    score = max(0, min(100, score))
    return score, notes
