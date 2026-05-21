import os

import redis as _redis
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()


def create_redis_client() -> _redis.Redis:
    return _redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
