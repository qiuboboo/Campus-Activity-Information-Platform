import os

from dotenv import load_dotenv


load_dotenv()


def _as_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-in-production")
    AUTO_CREATE_TABLES = _as_bool(os.getenv("AUTO_CREATE_TABLES"), True)
    POSTERS_PER_PAGE = int(os.getenv("POSTERS_PER_PAGE", "10"))
    DEFAULT_ADMIN_USERNAME = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
    DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123456")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    OPENCLAW_BASE_URL = os.getenv("OPENCLAW_BASE_URL", "")
    EMBEDDING_ENABLED = _as_bool(os.getenv("EMBEDDING_ENABLED"), False)
    JSON_AS_ASCII = False
