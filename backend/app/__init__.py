import logging
import time
import uuid

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

from .api.ai import ai_bp
from .api.audit_logs import audit_logs_bp
from .api.auth import auth_bp
from .api.calendar import calendar_bp
from .api.data_sources import data_sources_bp
from .api.dicts import dicts_bp
from .api.export import export_bp
from .api.health import health_bp
from .api.knowledge import knowledge_bp
from .api.posters import posters_bp
from .api.search import search_bp
from .api.subscriptions import subscriptions_bp
from .api.tasks import tasks_bp
from .commands import register_commands
from .config import Config
from .extensions import cors, create_redis_client, db, jwt
from .services.bootstrap import ensure_default_admin
from .utils.ratelimit import limiter

logger = logging.getLogger(__name__)


def init_database(app: Flask) -> None:
    """Create tables and seed default admin. Safe for single-process call."""
    with app.app_context():
        if app.config["AUTO_CREATE_TABLES"]:
            db.create_all()
            ensure_default_admin()


def _register_error_handlers(app: Flask) -> None:
    """Convert HTTP exceptions and unhandled errors to JSON responses."""

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException):
        return jsonify({
            "error": exc.name,
            "message": exc.description,
            "code": exc.code,
        }), exc.code or 500

    @app.errorhandler(Exception)
    def handle_unhandled(exc: Exception):
        logger.exception("Unhandled exception: %s", exc)
        return jsonify({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "code": 500,
        }), 500


def _register_request_logging(app: Flask) -> None:
    """Log every request with method, path, status, and duration."""

    @app.after_request
    def log_request(response):
        duration = time.time() - request.start_time
        logger.info(
            "%s %s -> %s [%.0fms]",
            request.method,
            request.path,
            response.status_code,
            duration * 1000,
        )
        return response


def _register_request_id(app: Flask) -> None:
    """Attach a unique request ID and start time to each request."""

    @app.before_request
    def attach_request_id():
        request.request_id = request.headers.get("X-Request-Id", str(uuid.uuid4())[:8])
        request.start_time = time.time()


def create_app(config_object: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app)

    # Initialize Redis client
    app.redis = create_redis_client()
    limiter.init_app(app.redis)

    _register_error_handlers(app)
    _register_request_id(app)
    _register_request_logging(app)

    app.register_blueprint(ai_bp, url_prefix="/api")
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(posters_bp, url_prefix="/api/posters")
    app.register_blueprint(knowledge_bp, url_prefix="/api/knowledge")
    app.register_blueprint(search_bp, url_prefix="/api/search")
    app.register_blueprint(data_sources_bp, url_prefix="/api")
    app.register_blueprint(dicts_bp, url_prefix="/api")
    app.register_blueprint(tasks_bp, url_prefix="/api")
    app.register_blueprint(audit_logs_bp, url_prefix="/api/audit-logs")
    app.register_blueprint(export_bp, url_prefix="/api")
    app.register_blueprint(subscriptions_bp, url_prefix="/api/subscriptions")
    app.register_blueprint(calendar_bp, url_prefix="/api")

    register_commands(app)

    return app
