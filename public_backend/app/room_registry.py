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


def join_room(room_code, room_ttl_seconds, participant_ttl_seconds, client_ip, device_token="", display_name=""):
    """@brief Register a participant in an active room.

    @param room_code Room code to join.
    @param room_ttl_seconds Active-room TTL threshold.
    @param participant_ttl_seconds Active-participant TTL threshold.
    @param client_ip Source IP address used for identity reuse.
    @param device_token Stable frontend-generated device token.
    @param display_name Optional participant display name.
    @return tuple[dict|None, dict|None, bool] Active room, participant metadata, and whether an existing session was reused.
    """
    room = get_active_room(room_code, room_ttl_seconds)
    if room is None:
        return None, None, False

    db = get_db()
    normalized_device_token = (device_token or "").strip()
    identity = get_or_create_identity(client_ip, normalized_device_token)
    existing_participant = get_existing_active_participant(
        room_code,
        client_ip,
        normalized_device_token,
        participant_ttl_seconds,
    )
    if existing_participant is not None:
        heartbeat_participant(room_code, existing_participant["participant_token"])
        participant = get_participant(room_code, existing_participant["participant_token"])
        return room, participant, True

    participant_token = secrets.token_urlsafe(24)
    now = _utc_now()
    normalized_name = _normalize_display_name(display_name, identity["display_name"])

    db.execute(
        """
        INSERT INTO room_participants (
            room_code, participant_token, uid, client_ip, device_token, display_name, role, status, created_at, updated_at, last_seen_at
        )
        VALUES (?, ?, ?, ?, ?, ?, 'guest', 'active', ?, ?, ?)
        """,
        (room_code, participant_token, identity["uid"], client_ip, normalized_device_token, normalized_name, now, now, now),
    )
    db.commit()

    participant = get_participant(room_code, participant_token)
    return room, participant, False


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


def get_room_state(room_code, room_ttl_seconds, participant_ttl_seconds, message_limit):
    """@brief Return an active room together with participants and messages.

    @param room_code User-facing room code.
    @param room_ttl_seconds Active-room TTL threshold.
    @param participant_ttl_seconds Active-participant TTL threshold.
    @param message_limit Maximum number of recent messages to return.
    @return dict|None Room state payload or `None` when the room is unavailable.
    """
    room = get_active_room(room_code, room_ttl_seconds)
    if room is None:
        return None

    return {
        "room": room,
        "participants": get_active_participants(room_code, participant_ttl_seconds),
        "messages": get_recent_messages(room_code, message_limit),
    }


def get_active_participants(room_code, participant_ttl_seconds):
    """@brief Fetch currently active participants for a room.

    @param room_code User-facing room code.
    @param participant_ttl_seconds Maximum participant idle age.
    @return list[dict] Serialized participant records.
    """
    db = get_db()
    cutoff = _utc_dt() - timedelta(seconds=participant_ttl_seconds)
    rows = db.execute(
        """
        SELECT participant_token, uid, display_name, role, status, created_at, updated_at, last_seen_at
        FROM room_participants
        WHERE room_code = ? AND status = 'active' AND last_seen_at >= ?
        ORDER BY created_at ASC
        """,
        (room_code, cutoff.isoformat()),
    ).fetchall()
    return [serialize_participant(row) for row in rows]


def get_recent_messages(room_code, message_limit):
    """@brief Fetch recent room messages in chronological order.

    @param room_code User-facing room code.
    @param message_limit Maximum number of messages to return.
    @return list[dict] Serialized message records.
    """
    db = get_db()
    rows = db.execute(
        """
        SELECT id, display_name, body, created_at
        FROM (
            SELECT id, display_name, body, created_at
            FROM room_messages
            WHERE room_code = ?
            ORDER BY id DESC
            LIMIT ?
        )
        ORDER BY id ASC
        """,
        (room_code, message_limit),
    ).fetchall()
    return [serialize_message(row) for row in rows]


def get_participant(room_code, participant_token):
    """@brief Fetch a single participant by token.

    @param room_code User-facing room code.
    @param participant_token Secret participant token.
    @return dict|None Serialized participant record.
    """
    db = get_db()
    row = db.execute(
        """
        SELECT participant_token, uid, display_name, role, status, created_at, updated_at, last_seen_at
        FROM room_participants
        WHERE room_code = ? AND participant_token = ?
        """,
        (room_code, participant_token),
    ).fetchone()
    if row is None:
        return None
    return serialize_participant(row)


def get_existing_active_participant(room_code, client_ip, device_token, participant_ttl_seconds):
    """@brief Fetch an active participant in a room for the same device or IP.

    @param room_code User-facing room code.
    @param client_ip Source IP address.
    @param device_token Stable frontend-generated device token.
    @param participant_ttl_seconds Maximum participant idle age.
    @return dict|None Serialized participant record when available.
    """
    db = get_db()
    cutoff = _utc_dt() - timedelta(seconds=participant_ttl_seconds)
    row = None
    if device_token:
        row = db.execute(
            """
            SELECT participant_token, uid, display_name, role, status, created_at, updated_at, last_seen_at
            FROM room_participants
            WHERE room_code = ? AND device_token = ? AND status = 'active' AND last_seen_at >= ?
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (room_code, device_token, cutoff.isoformat()),
        ).fetchone()
    if row is None and not device_token:
        row = db.execute(
            """
            SELECT participant_token, uid, display_name, role, status, created_at, updated_at, last_seen_at
            FROM room_participants
            WHERE room_code = ? AND client_ip = ? AND status = 'active' AND last_seen_at >= ?
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (room_code, client_ip, cutoff.isoformat()),
        ).fetchone()
    if row is None:
        return None
    return serialize_participant(row)


def heartbeat_participant(room_code, participant_token):
    """@brief Refresh a participant's presence timestamp.

    @param room_code User-facing room code.
    @param participant_token Secret participant token.
    @return bool `True` when a participant was updated.
    """
    db = get_db()
    now = _utc_now()
    result = db.execute(
        """
        UPDATE room_participants
        SET last_seen_at = ?, updated_at = ?, status = 'active'
        WHERE room_code = ? AND participant_token = ?
        """,
        (now, now, room_code, participant_token),
    )
    db.commit()
    return result.rowcount > 0


def leave_participant(room_code, participant_token):
    """@brief Mark a participant as having left the room.

    @param room_code User-facing room code.
    @param participant_token Secret participant token.
    @return bool `True` when a participant was updated.
    """
    db = get_db()
    now = _utc_now()
    result = db.execute(
        """
        UPDATE room_participants
        SET status = 'left', updated_at = ?, last_seen_at = ?
        WHERE room_code = ? AND participant_token = ?
        """,
        (now, now, room_code, participant_token),
    )
    db.commit()
    return result.rowcount > 0


def post_room_message(room_code, participant_token, body):
    """@brief Persist a text message for a room participant.

    @param room_code User-facing room code.
    @param participant_token Secret participant token.
    @param body Message body.
    @return dict|None Serialized message record or `None` when unauthorized.
    """
    participant = get_participant(room_code, participant_token)
    if participant is None or participant["status"] != "active":
        return None

    normalized_body = (body or "").strip()
    if not normalized_body:
        return None

    db = get_db()
    now = _utc_now()
    cursor = db.execute(
        """
        INSERT INTO room_messages (room_code, participant_token, display_name, body, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (room_code, participant_token, participant["display_name"], normalized_body[:500], now),
    )
    db.execute(
        """
        UPDATE room_participants
        SET last_seen_at = ?, updated_at = ?, status = 'active'
        WHERE room_code = ? AND participant_token = ?
        """,
        (now, now, room_code, participant_token),
    )
    db.commit()

    row = db.execute(
        """
        SELECT id, display_name, body, created_at
        FROM room_messages
        WHERE id = ?
        """,
        (cursor.lastrowid,),
    ).fetchone()
    return serialize_message(row)


def get_or_create_identity(client_ip, device_token=""):
    """@brief Resolve a stable UID and display name for a device or IP.

    @param client_ip Source IP address.
    @param device_token Stable frontend-generated device token.
    @return dict Identity payload containing `uid` and `display_name`.
    """
    normalized_ip = (client_ip or "").strip() or "unknown"
    normalized_device_token = (device_token or "").strip()
    db = get_db()
    row = None
    if normalized_device_token:
        row = db.execute(
            """
            SELECT uid, display_name
            FROM client_identities
            WHERE device_token = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (normalized_device_token,),
        ).fetchone()
    if row is None and not normalized_device_token:
        row = db.execute(
            """
            SELECT uid, display_name
            FROM client_identities
            WHERE ip_address = ?
            """,
            (normalized_ip,),
        ).fetchone()
    if row is not None:
        db.execute(
            """
            UPDATE client_identities
            SET device_token = CASE
                WHEN ? != '' THEN ?
                ELSE device_token
            END,
                updated_at = ?
            WHERE uid = ?
            """,
            (normalized_device_token, normalized_device_token, _utc_now(), row["uid"]),
        )
        db.commit()
        return {"uid": row["uid"], "display_name": row["display_name"]}

    now = _utc_now()
    uid = _generate_uid()
    display_name = f"UID-{uid}"
    db.execute(
        """
        INSERT INTO client_identities (ip_address, device_token, uid, display_name, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (normalized_ip, normalized_device_token, uid, display_name, now, now),
    )
    db.commit()
    return {"uid": uid, "display_name": display_name}


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


def serialize_participant(row):
    """@brief Convert a participant row into an API response shape.

    @param row SQLite row returned from the database layer.
    @return dict JSON-serializable participant representation.
    """
    return {
        "participant_token": row["participant_token"],
        "uid": row["uid"],
        "display_name": row["display_name"],
        "role": row["role"],
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "last_seen_at": row["last_seen_at"],
    }


def serialize_message(row):
    """@brief Convert a message row into an API response shape.

    @param row SQLite row returned from the database layer.
    @return dict JSON-serializable message representation.
    """
    return {
        "id": row["id"],
        "display_name": row["display_name"],
        "body": row["body"],
        "created_at": row["created_at"],
    }


def _generate_room_code():
    """@brief Generate a short human-friendly room code.

    @return str Six-character code that avoids ambiguous characters.
    """
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(6))


def _normalize_display_name(display_name, fallback_name):
    """@brief Normalize a user-facing display name or generate one.

    @param display_name Optional raw display name.
    @param fallback_name Stable generated name used when no custom name is provided.
    @return str Safe display name for room presence and chat.
    """
    normalized = (display_name or "").strip()
    if normalized:
        return normalized[:40]
    return fallback_name[:40]


def _generate_uid():
    """@brief Generate a stable-looking short UID token.

    @return str Six-character code.
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
