"""@file room_registry.py
@brief Persistence helpers for public room registration and lifecycle updates.
"""

from datetime import datetime, timedelta, timezone
import secrets

from .database import get_db


def create_room(name, public_host, public_port, owner_name="", notes=""):
    """@brief Create and persist a new public room record.

    @param name Room display name.
    @param public_host Hostname or domain clients should use.
    @param public_port TCP port exposed to clients.
    @param owner_name Optional room owner display name.
    @param notes Optional room description or notes.
    @return tuple[dict, str] Serialized room data and its management token.
    """
    db = get_db()
    room_code = _generate_room_code()
    manage_token = secrets.token_urlsafe(24)
    now = _utc_now()

    db.execute(
        """
        INSERT INTO rooms (room_code, name, public_host, public_port, owner_name, notes, manage_token, status, updated_at, last_heartbeat_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
        """,
        (room_code, name, public_host, public_port, owner_name, notes, manage_token, now, now),
    )
    db.commit()

    room = get_room_by_code(room_code)
    return room, manage_token


def get_active_rooms(ttl_seconds):
    """@brief Fetch rooms that are still considered active.

    @param ttl_seconds Maximum allowed age of the latest status refresh.
    @return list[dict] Serialized room records.
    """
    db = get_db()
    cutoff = _utc_dt() - timedelta(seconds=ttl_seconds)
    rows = db.execute(
        """
        SELECT room_code, name, public_host, public_port, owner_name, notes, status, created_at, updated_at, last_heartbeat_at
        FROM rooms
        WHERE status = 'active' AND last_heartbeat_at >= ?
        ORDER BY created_at DESC
        """,
        (cutoff.isoformat(),),
    ).fetchall()
    return [serialize_room(row) for row in rows]


def get_active_room(room_code, ttl_seconds):
    """@brief Fetch a single active room by code.

    @param room_code Room code to query.
    @param ttl_seconds Maximum allowed age of the latest status refresh.
    @return dict|None Serialized room record or `None` if expired/missing.
    """
    db = get_db()
    cutoff = _utc_dt() - timedelta(seconds=ttl_seconds)
    row = db.execute(
        """
        SELECT room_code, name, public_host, public_port, owner_name, notes, status, created_at, updated_at, last_heartbeat_at
        FROM rooms
        WHERE room_code = ? AND status = 'active' AND last_heartbeat_at >= ?
        """,
        (room_code, cutoff.isoformat()),
    ).fetchone()
    if row is None:
        return None
    return serialize_room(row)


def heartbeat_room(room_code, manage_token):
    """@brief Refresh the status timestamp for a managed room.

    @param room_code Room code to update.
    @param manage_token Secret token that authorizes the update.
    @return bool `True` when a room was updated, otherwise `False`.
    """
    db = get_db()
    now = _utc_now()
    result = db.execute(
        """
        UPDATE rooms
        SET last_heartbeat_at = ?, updated_at = ?, status = 'active'
        WHERE room_code = ? AND manage_token = ?
        """,
        (now, now, room_code, manage_token),
    )
    db.commit()
    return result.rowcount > 0


def close_room(room_code, manage_token):
    """@brief Mark a room as closed.

    @param room_code Room code to close.
    @param manage_token Secret token that authorizes the close request.
    @return bool `True` when a room was updated, otherwise `False`.
    """
    db = get_db()
    now = _utc_now()
    result = db.execute(
        """
        UPDATE rooms
        SET status = 'closed', updated_at = ?
        WHERE room_code = ? AND manage_token = ?
        """,
        (now, room_code, manage_token),
    )
    db.commit()
    return result.rowcount > 0


def get_room_by_code(room_code):
    """@brief Fetch a room regardless of whether it is active.

    @param room_code Room code to query.
    @return dict|None Serialized room record or `None` when not found.
    """
    db = get_db()
    row = db.execute(
        """
        SELECT room_code, name, public_host, public_port, owner_name, notes, status, created_at, updated_at, last_heartbeat_at
        FROM rooms
        WHERE room_code = ?
        """,
        (room_code,),
    ).fetchone()
    if row is None:
        return None
    return serialize_room(row)


def serialize_room(row):
    """@brief Convert a database row into the API response shape.

    @param row SQLite row returned from the database layer.
    @return dict JSON-serializable room representation.
    """
    return {
        "room_code": row["room_code"],
        "name": row["name"],
        "public_host": row["public_host"],
        "public_port": row["public_port"],
        "owner_name": row["owner_name"],
        "notes": row["notes"],
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "last_heartbeat_at": row["last_heartbeat_at"],
    }


def _generate_room_code():
    """@brief Generate a short human-friendly room code.

    @return str Six-character code that avoids ambiguous characters.
    """
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(6))


def _utc_dt():
    """@brief Return the current UTC datetime object.

    @return datetime Current UTC timestamp.
    """
    return datetime.now(timezone.utc)


def _utc_now():
    """@brief Return the current UTC timestamp in ISO 8601 format.

    @return str ISO 8601 UTC timestamp string.
    """
    return _utc_dt().isoformat()
