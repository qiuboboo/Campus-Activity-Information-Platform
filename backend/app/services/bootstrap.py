from datetime import datetime, timedelta

from flask import current_app
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import (
    CrawlLog,
    DataSource,
    DictEntry,
    Notification,
    Poster,
    Subscription,
    User,
    UserCalendarEvent,
)
from .audit_service import create_audit_log
from .knowledge_service import rebuild_poster_knowledge
from .poster_service import generate_poster_html


def ensure_default_admin() -> None:
    username = current_app.config["DEFAULT_ADMIN_USERNAME"]
    password = current_app.config["DEFAULT_ADMIN_PASSWORD"]

    existing_user = User.query.filter_by(username=username).first()
    if existing_user is not None:
        return

    admin = User(username=username, role="admin", email="admin@example.edu")
    admin.set_password(password)
    db.session.add(admin)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()


def _ensure_user(username: str, password: str, role: str, email: str) -> User:
    user = User.query.filter_by(username=username).first()
    if user is None:
      user = User(username=username, role=role, email=email)
      db.session.add(user)
    user.role = role
    user.email = email
    user.set_password(password)
    db.session.flush()
    return user


def _upsert_poster(created_by: int, payload: dict) -> Poster:
    poster = Poster.query.filter_by(source_url=payload["source_url"]).first()
    if poster is None:
        poster = Poster(created_by=created_by, source_url=payload["source_url"])
        db.session.add(poster)

    for key, value in payload.items():
        setattr(poster, key, value)

    poster.created_by = created_by
    poster.content_html = generate_poster_html(
        title=poster.title,
        summary=poster.summary,
        event_time=poster.event_time,
        location=poster.location,
        organizer=poster.organizer,
        activity_type=poster.activity_type,
    )
    db.session.flush()
    return poster


def _ensure_data_source() -> DataSource:
    source = DataSource.query.filter_by(name="中山大学官网").first()
    if source is None:
        source = DataSource(name="中山大学官网", base_url="https://www.sysu.edu.cn/")
        db.session.add(source)

    source.base_url = "https://www.sysu.edu.cn/"
    source.enabled = True
    source.crawl_mode = "basic"
    source.source_level = "official"
    source.allowed_domains = "www.sysu.edu.cn"
    source.list_selector = None
    source.content_selector = None
    source.owner = "SYSU"
    source.notes = "官方首页演示数据源；实际活动抓取建议配置更精确的栏目地址和 CSS 选择器。"
    source.request_interval = 1
    db.session.flush()

    if not CrawlLog.query.filter_by(data_source_id=source.id).first():
        now = datetime.utcnow()
        log = CrawlLog(
            data_source_id=source.id,
            status="completed",
            message="演示日志：已抓取官网首页并生成草稿。",
            started_at=now - timedelta(minutes=3),
            finished_at=now - timedelta(minutes=2),
            pages_found=1,
            pages_succeeded=1,
            pages_failed=0,
            duplicates_skipped=0,
            drafts_created=1,
            average_quality_score=75,
        )
        db.session.add(log)
    return source


def _ensure_dict_entries() -> None:
    entries = [
        ("place", "大学生活动中心大礼堂", "大活,大活礼堂", "大型讲座、晚会和开幕式常用场地"),
        ("place", "图书馆报告厅", "图书馆,报告厅", "报告会与学术沙龙常用场地"),
        ("org", "共青团中山大学委员会", "校团委,团委", "校园文化与志愿服务活动组织方"),
        ("org", "计算机学院", "计院,计算机学院", "技术讲座、竞赛与创新活动组织方"),
        ("topic", "人工智能", "AI,大模型,机器学习", "技术与创新主题"),
        ("topic", "志愿服务", "志愿者,公益", "公益实践与校园服务主题"),
    ]
    for category, standard_name, aliases, description in entries:
        entry = DictEntry.query.filter_by(category=category, standard_name=standard_name).first()
        if entry is None:
            entry = DictEntry(category=category, standard_name=standard_name)
            db.session.add(entry)
        entry.aliases = aliases
        entry.description = description


def _ensure_unique(model, defaults: dict, **filters):
    item = model.query.filter_by(**filters).first()
    if item is None:
        item = model(**filters, **defaults)
        db.session.add(item)
    else:
        for key, value in defaults.items():
            setattr(item, key, value)
    db.session.flush()
    return item


def seed_demo_posters() -> None:
    ensure_default_admin()

    admin = _ensure_user(
        current_app.config["DEFAULT_ADMIN_USERNAME"],
        current_app.config["DEFAULT_ADMIN_PASSWORD"],
        "admin",
        "admin@example.edu",
    )
    test = _ensure_user("test", "test123456", "publisher", "test@example.edu")

    now = datetime.utcnow()
    posters = [
        _upsert_poster(admin.id, {
            "title": "2026 校园科技文化节开幕式",
            "raw_text": "校园科技文化节将在大学生活动中心大礼堂举行，现场包含创新项目展示、社团互动和开幕演出。",
            "summary": "面向全校师生的科技文化节开幕活动，适合演示热门推荐、日历和知识关联。",
            "event_time": now + timedelta(days=5, hours=2),
            "location": "大学生活动中心大礼堂",
            "organizer": "共青团中山大学委员会",
            "status": "published",
            "source_type": "manual",
            "source_url": "https://demo.sysu/activity/tech-culture-opening",
            "activity_type": "展览",
            "tags": "科技,文化节,开幕式",
            "cover_image_url": "https://www.sysu.edu.cn/sites/default/files/logo_0.png",
            "quality_score": 92,
        }),
        _upsert_poster(admin.id, {
            "title": "人工智能创新应用讲座",
            "raw_text": "计算机学院邀请企业工程师分享大模型应用开发经验，包含案例拆解、问答和学习路径建议。",
            "summary": "从大模型产品到校园创新实践的技术讲座。",
            "event_time": now + timedelta(days=7, hours=4),
            "location": "图书馆报告厅",
            "organizer": "计算机学院",
            "status": "published",
            "source_type": "manual",
            "source_url": "https://demo.sysu/activity/ai-lecture",
            "activity_type": "讲座",
            "tags": "AI,大模型,创新",
            "cover_image_url": None,
            "quality_score": 88,
        }),
        _upsert_poster(admin.id, {
            "title": "校园志愿服务文化论坛",
            "raw_text": "论坛围绕志愿服务项目设计、社区协作和校园公益传播展开交流。",
            "summary": "志愿服务主题论坛，展示订阅和通知功能。",
            "event_time": now + timedelta(days=9, hours=3),
            "location": "图书馆报告厅",
            "organizer": "共青团中山大学委员会",
            "status": "published",
            "source_type": "manual",
            "source_url": "https://demo.sysu/activity/volunteer-forum",
            "activity_type": "论坛",
            "tags": "志愿服务,公益,论坛",
            "cover_image_url": None,
            "quality_score": 84,
        }),
        _upsert_poster(test.id, {
            "title": "测试用户发布的摄影工作坊",
            "raw_text": "摄影工作坊正在等待管理员审核，内容包含校园取景、构图练习和作品互评。",
            "summary": "用于演示发布者提交审核与管理员审核流程。",
            "event_time": now + timedelta(days=12, hours=5),
            "location": "逸夫艺术楼",
            "organizer": "学生摄影社",
            "status": "pending_review",
            "source_type": "manual",
            "source_url": "https://demo.sysu/activity/photo-workshop",
            "activity_type": "其他",
            "tags": "摄影,工作坊",
            "cover_image_url": None,
            "quality_score": 76,
        }),
        _upsert_poster(test.id, {
            "title": "被驳回的社团招新夜",
            "raw_text": "该活动缺少准确时间和地点，保留为驳回状态以演示重新编辑提交。",
            "summary": "用于演示驳回原因和再次提交。",
            "event_time": None,
            "location": None,
            "organizer": "测试社团",
            "status": "rejected",
            "review_comment": "请补充准确活动时间和地点后再提交。",
            "source_type": "manual",
            "source_url": "https://demo.sysu/activity/rejected-club-night",
            "activity_type": "晚会",
            "tags": "社团,招新",
            "cover_image_url": None,
            "quality_score": 52,
        }),
    ]

    for poster in posters:
        if poster.status == "published":
            rebuild_poster_knowledge(poster)

    source = _ensure_data_source()
    _ensure_dict_entries()

    db.session.flush()
    _ensure_unique(Subscription, {"notify_method": "platform"}, user_id=test.id, keyword="人工智能")
    _ensure_unique(UserCalendarEvent, {}, user_id=test.id, poster_id=posters[0].id)
    _ensure_unique(Notification, {
        "title": "你订阅的活动有更新",
        "body": "人工智能创新应用讲座已发布，可以前往活动详情查看。",
        "is_read": False,
    }, user_id=test.id, poster_id=posters[1].id)

    redis = getattr(current_app, "redis", None)
    if redis is not None:
        redis.sadd(f"user:{test.id}:favorite_activities", posters[0].id, posters[1].id)
        redis.sadd(f"activity:{posters[0].id}:registrations", test.id)
        redis.sadd(f"activity:{posters[1].id}:registrations", test.id)

    if not getattr(seed_demo_posters, "_audit_logged", False):
        create_audit_log(
            actor_id=admin.id,
            action="seed_demo",
            target_type="demo",
            target_id=source.id,
            summary="Seeded demo accounts, activities, subscriptions, notifications, calendar and data source examples.",
        )
        seed_demo_posters._audit_logged = True

    db.session.commit()
