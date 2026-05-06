from datetime import datetime

from flask import current_app

from ..extensions import db
from ..models import Poster, User


def ensure_default_admin() -> None:
    username = current_app.config["DEFAULT_ADMIN_USERNAME"]
    password = current_app.config["DEFAULT_ADMIN_PASSWORD"]

    existing_user = User.query.filter_by(username=username).first()
    if existing_user is not None:
        return

    admin = User(username=username, role="admin")
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()


def seed_demo_posters() -> None:
    ensure_default_admin()
    admin = User.query.filter_by(username=current_app.config["DEFAULT_ADMIN_USERNAME"]).first()
    if admin is None:
        return

    if Poster.query.count() > 0:
        return

    poster = Poster(
        title="2026 校园科技文化节开幕式",
        raw_text="2026 校园科技文化节将于 2026-05-10 19:00 在大学生活动中心大礼堂举行，由校团委主办。",
        summary="校园科技文化节开幕式，面向全校师生开放。",
        event_time=datetime.fromisoformat("2026-05-10T19:00:00"),
        location="大学生活动中心大礼堂",
        organizer="校团委",
        status="draft",
        source_type="manual",
        created_by=admin.id,
    )
    db.session.add(poster)
    db.session.commit()
