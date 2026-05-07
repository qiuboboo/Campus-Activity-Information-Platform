import os

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
