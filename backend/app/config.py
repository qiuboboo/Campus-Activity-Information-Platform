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
    EMBEDDING_ENABLED = _as_bool(os.getenv("EMBEDDING_ENABLED"), False)
    EMBEDDING_API_URL = os.getenv("EMBEDDING_API_URL", "http://copilot-proxy:4141/v1/embeddings")
    EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", "copilot")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    JSON_AS_ASCII = False

    # --- Celery / Scheduled Crawl ---
    ENABLE_SCHEDULED_CRAWL = _as_bool(os.getenv("ENABLE_SCHEDULED_CRAWL"), False)
    CRAWL_SCHEDULE_HOURS = int(os.getenv("CRAWL_SCHEDULE_HOURS", "12"))

    # --- AI Service (Multi-Model) ---
    # Default model (always required as fallback)
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    LLM_API_BASE_URL = os.getenv("LLM_API_BASE_URL", "https://api.deepseek.com")
    LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

    # --- MCP Service ---
    MCP_SERVERS = os.getenv("MCP_SERVERS", "")

    # --- CORS ---
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

    # --- Email / SMTP ---
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.qq.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = _as_bool(os.getenv("MAIL_USE_TLS"), True)
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "")

    # --- Local attachment storage ---
    UPLOAD_DIR = os.path.abspath(os.getenv("UPLOAD_DIR", "uploads"))
    MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", str(10 * 1024 * 1024)))
    RECOMMENDATION_ENABLED = _as_bool(os.getenv("RECOMMENDATION_ENABLED"), True)

    # --- Multi-Engine Search (SearXNG) ---
    SEARXNG_BASE_URL = os.getenv("SEARXNG_BASE_URL", "http://campus-activity-searxng:8080")

    # --- Sogou WeChat Search ---
    SOGOU_COOKIES = os.getenv("SOGOU_COOKIES", "")

    # --- Crawler Security ---
    CRAWL_REQUEST_INTERVAL = int(os.getenv("CRAWL_REQUEST_INTERVAL", "2"))
    CRAWL_CONNECT_TIMEOUT = int(os.getenv("CRAWL_CONNECT_TIMEOUT", "5"))
    CRAWL_READ_TIMEOUT = int(os.getenv("CRAWL_READ_TIMEOUT", "30"))
    CRAWL_REQUEST_RETRIES = int(os.getenv("CRAWL_REQUEST_RETRIES", "2"))
    CRAWL_RETRY_BACKOFF_SECONDS = float(os.getenv("CRAWL_RETRY_BACKOFF_SECONDS", "1"))
    CRAWL_MAX_PAGES = int(os.getenv("CRAWL_MAX_PAGES", "50"))
    CRAWL_SOFT_TIMEOUT = int(os.getenv("CRAWL_SOFT_TIMEOUT", "1800"))
    CRAWL_BLOCK_INTERNAL = _as_bool(os.getenv("CRAWL_BLOCK_INTERNAL"), True)
