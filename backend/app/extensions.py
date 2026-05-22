import os

import redis as _redis
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()


def create_redis_client(redis_url: str | None = None) -> _redis.Redis | None:
    if redis_url is not None and redis_url.strip() == "":
        return None
    url = redis_url or os.getenv("REDIS_URL") or None
    if url is None:
        return None
    return _redis.from_url(url)
