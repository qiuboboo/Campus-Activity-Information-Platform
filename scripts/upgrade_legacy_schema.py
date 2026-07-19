"""Safely transition an existing pre-Alembic database to the current schema.

Back up first.  Run `python scripts/upgrade_legacy_schema.py --legacy-bootstrap`
only for an existing database that has no alembic_version table.
"""
import argparse
import sys
from pathlib import Path

from sqlalchemy import inspect

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app import create_app, init_database  # noqa: E402
from app.extensions import db  # noqa: E402
from flask_migrate import stamp, upgrade  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--legacy-bootstrap", action="store_true")
    args = parser.parse_args()
    app = create_app()
    with app.app_context():
        tables = set(inspect(db.engine).get_table_names())
        directory = str(ROOT / "backend" / "migrations")
        if not tables or tables == {"alembic_version"}:
            upgrade(directory=directory)
            print("Empty database upgraded.")
            return
        if "alembic_version" in tables:
            upgrade(directory=directory)
            print("Versioned database upgraded.")
            return
        if not args.legacy_bootstrap:
            raise SystemExit("Legacy database detected. Back up, then rerun with --legacy-bootstrap.")
        app.config["AUTO_CREATE_TABLES"] = True
        init_database(app)
        stamp(directory=directory, revision="head")
        print("Legacy database safely baselined.")


if __name__ == "__main__":
    main()
