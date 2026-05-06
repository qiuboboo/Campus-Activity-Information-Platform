from datetime import datetime

from flask import current_app
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import Poster, User
from .knowledge_service import rebuild_poster_knowledge


def ensure_default_admin() -> None:
    username = current_app.config["DEFAULT_ADMIN_USERNAME"]
    password = current_app.config["DEFAULT_ADMIN_PASSWORD"]

    existing_user = User.query.filter_by(username=username).first()
    if existing_user is not None:
        return

    admin = User(username=username, role="admin")
    admin.set_password(password)
    db.session.add(admin)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()


def seed_demo_posters() -> None:
    ensure_default_admin()
    admin = User.query.filter_by(username=current_app.config["DEFAULT_ADMIN_USERNAME"]).first()
    if admin is None:
        return

    if Poster.query.count() > 0:
        return

    demo_posters = [
        Poster(
            title="2026 校园科技文化节开幕式",
            raw_text="2026 校园科技文化节将于 2026-05-10 19:00 在大学生活动中心大礼堂举行，由校团委主办。",
            summary="校园科技文化节开幕式，面向全校师生开放。",
            event_time=datetime.fromisoformat("2026-05-10T19:00:00"),
            location="大学生活动中心大礼堂",
            organizer="校团委",
            status="published",
            source_type="manual",
            source_url="https://example.edu.cn/events/tech-culture-opening",
            created_by=admin.id,
        ),
        Poster(
            title="AI 创新应用讲座",
            raw_text="AI 创新应用讲座将于 2026-05-10 15:00 在大学生活动中心大礼堂举行，由计算机学院主办。",
            summary="面向全校学生的人工智能应用讲座。",
            event_time=datetime.fromisoformat("2026-05-10T15:00:00"),
            location="大学生活动中心大礼堂",
            organizer="计算机学院",
            status="published",
            source_type="manual",
            source_url="https://example.edu.cn/events/ai-lecture",
            created_by=admin.id,
        ),
        Poster(
            title="校园志愿服务文化论坛",
            raw_text="校园志愿服务文化论坛将于 2026-05-12 14:00 在图书馆报告厅举行，由校团委主办。",
            summary="围绕校园志愿服务与文化建设开展交流。",
            event_time=datetime.fromisoformat("2026-05-12T14:00:00"),
            location="图书馆报告厅",
            organizer="校团委",
            status="published",
            source_type="manual",
            source_url="https://example.edu.cn/events/volunteer-forum",
            created_by=admin.id,
        ),
    ]
    db.session.add_all(demo_posters)
    db.session.flush()
    for poster in demo_posters:
        rebuild_poster_knowledge(poster)
    db.session.commit()
