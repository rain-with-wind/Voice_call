"""@file rooms.py
@brief Room-management HTTP routes for the public backend.
"""

from flask import Blueprint, current_app, jsonify, request

from ..room_registry import close_room, create_room, get_active_room, get_active_rooms, heartbeat_room


bp = Blueprint("rooms", __name__, url_prefix="/api/rooms")


@bp.get("")
def list_rooms():
    """@brief Return the current list of active rooms as JSON."""
    rooms = get_active_rooms(current_app.config["ROOM_TTL_SECONDS"])
    return jsonify({"rooms": rooms})


@bp.post("/register")
def register_room():
    """@brief Validate input and register a new room.

    @return Response JSON response containing room metadata and manage token.
    """
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    public_host = (payload.get("public_host") or "").strip()
    owner_name = (payload.get("owner_name") or "").strip()
    notes = (payload.get("notes") or "").strip()

    try:
        public_port = int(payload.get("public_port", 5000))
    except (TypeError, ValueError):
        return jsonify({"error": "public_port must be an integer"}), 400

    if not name:
        return jsonify({"error": "Room name is required"}), 400
    if not public_host:
        return jsonify({"error": "public_host is required"}), 400
    if public_port < 1 or public_port > 65535:
        return jsonify({"error": "public_port must be between 1 and 65535"}), 400

    room, manage_token = create_room(name, public_host, public_port, owner_name, notes)
    return (
        jsonify(
            {
                "room": room,
                "manage_token": manage_token,
                "heartbeat_interval_seconds": current_app.config["HEARTBEAT_INTERVAL_SECONDS"],
            }
        ),
        201,
    )


@bp.get("/<room_code>")
def room_detail(room_code):
    """@brief Return a single active room by room code.

    @param room_code User-facing room code.
    @return Response JSON room details or a 404 payload.
    """
    room = get_active_room(room_code, current_app.config["ROOM_TTL_SECONDS"])
    if room is None:
        return jsonify({"error": "Room not found or expired"}), 404
    return jsonify({"room": room})


@bp.post("/<room_code>/heartbeat")
def room_heartbeat(room_code):
    """@brief Refresh a room so it stays active in the registry.

    @param room_code User-facing room code.
    @return Response JSON room details or an error payload.
    """
    manage_token = request.headers.get("X-Manage-Token", "")
    if not manage_token:
        return jsonify({"error": "X-Manage-Token is required"}), 401

    if not heartbeat_room(room_code, manage_token):
        return jsonify({"error": "Room not found or token invalid"}), 404

    room = get_active_room(room_code, current_app.config["ROOM_TTL_SECONDS"])
    return jsonify({"room": room})


@bp.post("/<room_code>/close")
def room_close(room_code):
    """@brief Mark a room as closed.

    @param room_code User-facing room code.
    @return Response JSON confirmation or an error payload.
    """
    manage_token = request.headers.get("X-Manage-Token", "")
    if not manage_token:
        return jsonify({"error": "X-Manage-Token is required"}), 401

    if not close_room(room_code, manage_token):
        return jsonify({"error": "Room not found or token invalid"}), 404

    return jsonify({"message": "Room closed"})
