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

    # Named model profiles: LLM_{NAME}_KEY / LLM_{NAME}_BASE_URL / LLM_{NAME}_MODEL
    # e.g. LLM_CLAUDE_KEY=sk-xxx / LLM_CLAUDE_BASE_URL=https://api.anthropic.com / LLM_CLAUDE_MODEL=claude-sonnet-4-20250514
    @staticmethod
    def list_llm_profiles() -> dict[str, dict]:
        """Discover all configured LLM profiles from environment variables.

        Returns a dict keyed by profile name, each containing key/base_url/model.
        The "default" profile is always present if LLM_API_KEY is set.
        """
        profiles: dict[str, dict] = {}

        key = os.getenv("LLM_API_KEY", "")
        if key:
            profiles["default"] = {
                "key": key,
                "base_url": os.getenv("LLM_API_BASE_URL", "https://api.deepseek.com"),
                "model": os.getenv("LLM_MODEL", "deepseek-chat"),
            }

        # Discover named profiles: scan env for LLM_*_KEY pattern
        for env_key, env_val in sorted(os.environ.items()):
            if not env_val:
                continue
            if env_key.startswith("LLM_") and env_key.endswith("_KEY"):
                name = env_key[4:-4].lower()  # LLM_DEEPSEEK_KEY -> deepseek
                if name == "api":
                    continue  # skip LLM_API_KEY
                prefix = f"LLM_{name.upper()}"
                profiles[name] = {
                    "key": env_val,
                    "base_url": os.getenv(f"{prefix}_BASE_URL", "https://api.deepseek.com"),
                    "model": os.getenv(f"{prefix}_MODEL", ""),
                }

        return profiles

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

    # --- Multi-Engine Search (SearXNG) ---
    SEARXNG_BASE_URL = os.getenv("SEARXNG_BASE_URL", "http://campus-activity-searxng:8080")

    # --- Sogou WeChat Search ---
    SOGOU_COOKIES = os.getenv("SOGOU_COOKIES", "")

    # --- Crawler Security ---
    CRAWL_REQUEST_INTERVAL = int(os.getenv("CRAWL_REQUEST_INTERVAL", "2"))
    CRAWL_MAX_PAGES = int(os.getenv("CRAWL_MAX_PAGES", "50"))
    CRAWL_SOFT_TIMEOUT = int(os.getenv("CRAWL_SOFT_TIMEOUT", "1800"))
    CRAWL_BLOCK_INTERNAL = _as_bool(os.getenv("CRAWL_BLOCK_INTERNAL"), True)
