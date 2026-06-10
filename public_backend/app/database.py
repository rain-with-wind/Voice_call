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
    _ensure_runtime_migrations(db)
    db.commit()


def ensure_database(app):
    with app.app_context():
        init_db()


def init_app(app):
    app.teardown_appcontext(close_db)


def _ensure_runtime_migrations(db):
    """Ensure newer columns exist when reusing an older SQLite database."""
    participant_columns = {
        row["name"] for row in db.execute("PRAGMA table_info(room_participants)").fetchall()
    }
    if "uid" not in participant_columns:
        db.execute("ALTER TABLE room_participants ADD COLUMN uid TEXT NOT NULL DEFAULT ''")
    if "client_ip" not in participant_columns:
        db.execute("ALTER TABLE room_participants ADD COLUMN client_ip TEXT NOT NULL DEFAULT ''")
    if "device_token" not in participant_columns:
        db.execute("ALTER TABLE room_participants ADD COLUMN device_token TEXT NOT NULL DEFAULT ''")

    identity_columns = {
        row["name"] for row in db.execute("PRAGMA table_info(client_identities)").fetchall()
    }
    if identity_columns:
        _ensure_client_identity_v2(db, identity_columns)

    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_room_participants_room_device ON room_participants(room_code, device_token, status)"
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_room_participants_room_ip ON room_participants(room_code, client_ip, status)"
    )
    db.execute("CREATE INDEX IF NOT EXISTS idx_client_identities_device_token ON client_identities(device_token)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_client_identities_ip_address ON client_identities(ip_address)")


def _ensure_client_identity_v2(db, identity_columns):
    """Upgrade the client identity table to token-first semantics if needed."""
    if "device_token" not in identity_columns or _client_identities_ip_is_unique(db):
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS client_identities_v2 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT NOT NULL,
                device_token TEXT NOT NULL DEFAULT '',
                uid TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        if "device_token" not in identity_columns:
            db.execute(
                """
                INSERT INTO client_identities_v2 (id, ip_address, device_token, uid, display_name, created_at, updated_at)
                SELECT id, ip_address, '', uid, display_name, created_at, updated_at
                FROM client_identities
                """
            )
        else:
            db.execute(
                """
                INSERT INTO client_identities_v2 (id, ip_address, device_token, uid, display_name, created_at, updated_at)
                SELECT id, ip_address, device_token, uid, display_name, created_at, updated_at
                FROM client_identities
                """
            )
        db.execute("DROP TABLE client_identities")
        db.execute("ALTER TABLE client_identities_v2 RENAME TO client_identities")


def _client_identities_ip_is_unique(db):
    """Return whether the legacy client identity table still enforces unique IPs."""
    rows = db.execute("PRAGMA index_list(client_identities)").fetchall()
    for row in rows:
        if not row["unique"]:
            continue
        columns = db.execute(f"PRAGMA index_info({row['name']})").fetchall()
        column_names = [column["name"] for column in columns]
        if column_names == ["ip_address"]:
            return True
    return False
