from flask import Flask

from .api.auth import auth_bp
from .api.health import health_bp
from .api.posters import posters_bp
from .commands import register_commands
from .config import Config
from .extensions import cors, db, jwt
from .services.bootstrap import ensure_default_admin


def create_app(config_object: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app)

    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(posters_bp, url_prefix="/api/posters")

    register_commands(app)

    with app.app_context():
        if app.config["AUTO_CREATE_TABLES"]:
            db.create_all()
            ensure_default_admin()

    return app
