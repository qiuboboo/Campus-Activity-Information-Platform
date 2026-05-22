import click
from flask import Flask

from .extensions import db
from .services.bootstrap import ensure_default_admin, seed_demo_posters


def register_commands(app: Flask) -> None:
    @app.cli.command("init-db")
    def init_db() -> None:
        db.create_all()
        ensure_default_admin()
        click.echo("database initialized")

    @app.cli.command("seed-demo")
    def seed_demo() -> None:
        seed_demo_posters()
        click.echo("demo data seeded")
