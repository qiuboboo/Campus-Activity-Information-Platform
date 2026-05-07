import os
from datetime import timedelta

from celery import Celery

from .config import Config

celery = Celery(
    "campus_activity",
    broker=os.getenv("REDIS_URL", Config.REDIS_URL),
    backend=os.getenv("REDIS_URL", Config.REDIS_URL),
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    worker_concurrency=1,
)

# Beat schedule (activated when beat service runs)
celery.conf.beat_schedule = {
    "crawl-all-enabled-sources": {
        "task": "app.tasks.crawl_tasks.crawl_all_enabled_sources",
        "schedule": timedelta(hours=Config.CRAWL_SCHEDULE_HOURS),
        "options": {"queue": "default"},
    },
}
