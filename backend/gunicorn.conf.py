bind = "0.0.0.0:5000"
workers = 1
threads = 2
timeout = 60
preload_app = True


def on_starting(server):
    """Initialize database tables once before workers are forked."""
    from wsgi import app
    from app.extensions import db

    with app.app_context():
        from app.config import Config
        if getattr(Config, "AUTO_CREATE_TABLES", True):
            db.create_all()
            from app.services.bootstrap import ensure_default_admin
            ensure_default_admin()
