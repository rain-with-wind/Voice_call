from pathlib import Path
import sqlite3

from flask import current_app, g


def get_db():
    if "db" not in g:
        db_path = Path(current_app.config["DATABASE_PATH"])
        db_path.parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    schema_path = Path(current_app.root_path) / "schema.sql"
    with schema_path.open("r", encoding="utf-8") as file:
        db.executescript(file.read())
    db.commit()


def ensure_database(app):
    with app.app_context():
        init_db()


def init_app(app):
    app.teardown_appcontext(close_db)
