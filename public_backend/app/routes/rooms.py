"""@file rooms.py
@brief Room-management HTTP routes for the public backend.
"""

from flask import Blueprint, current_app, jsonify, request

from ..room_registry import (
    close_room,
    create_room,
    get_active_room,
    get_active_rooms,
    get_room_state,
    heartbeat_participant,
    heartbeat_room,
    join_room,
    leave_participant,
    post_room_message,
)


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
    public_host = (payload.get("public_host") or "relay").strip()
    owner_name = (payload.get("owner_name") or "").strip()
    notes = (payload.get("notes") or "").strip()

    try:
        public_port = int(payload.get("public_port", 0))
    except (TypeError, ValueError):
        public_port = 0

    if not name:
        return jsonify({"error": "Room name is required"}), 400

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


@bp.get("/<room_code>/state")
def room_state(room_code):
    """@brief Return the room, active participants, and recent messages.

    @param room_code User-facing room code.
    @return Response JSON state payload or 404 when unavailable.
    """
    state = get_room_state(
        room_code,
        current_app.config["ROOM_TTL_SECONDS"],
        current_app.config["PARTICIPANT_TTL_SECONDS"],
        current_app.config["MESSAGE_LIMIT"],
    )
    if state is None:
        return jsonify({"error": "Room not found or expired"}), 404
    return jsonify(state)


@bp.post("/<room_code>/join")
def room_join(room_code):
    """@brief Create an anonymous participant session for a room.

    @param room_code User-facing room code.
    @return Response JSON containing participant session information.
    """
    payload = request.get_json(silent=True) or {}
    room, participant, reused_session = join_room(
        room_code,
        current_app.config["ROOM_TTL_SECONDS"],
        current_app.config["PARTICIPANT_TTL_SECONDS"],
        _get_client_ip(),
        request.headers.get("X-Device-Token", ""),
        payload.get("display_name", ""),
    )
    if room is None or participant is None:
        return jsonify({"error": "Room not found or expired"}), 404

    state = get_room_state(
        room_code,
        current_app.config["ROOM_TTL_SECONDS"],
        current_app.config["PARTICIPANT_TTL_SECONDS"],
        current_app.config["MESSAGE_LIMIT"],
    )
    return jsonify(
        {
            "room": room,
            "participant": participant,
            "participant_token": participant["participant_token"],
            "reused_session": reused_session,
            "participants": state["participants"],
            "messages": state["messages"],
        }
    )


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


@bp.post("/<room_code>/participants/heartbeat")
def participant_heartbeat(room_code):
    """@brief Refresh a participant's presence in a room.

    @param room_code User-facing room code.
    @return Response JSON confirmation or an error payload.
    """
    participant_token = request.headers.get("X-Participant-Token", "")
    if not participant_token:
        return jsonify({"error": "X-Participant-Token is required"}), 401

    if not heartbeat_participant(room_code, participant_token):
        return jsonify({"error": "Participant not found"}), 404

    return jsonify({"message": "Participant refreshed"})


@bp.post("/<room_code>/participants/leave")
def participant_leave(room_code):
    """@brief Mark a participant as having left the room.

    @param room_code User-facing room code.
    @return Response JSON confirmation or an error payload.
    """
    participant_token = request.headers.get("X-Participant-Token", "")
    if not participant_token:
        return jsonify({"error": "X-Participant-Token is required"}), 401

    if not leave_participant(room_code, participant_token):
        return jsonify({"error": "Participant not found"}), 404

    return jsonify({"message": "Participant left"})


@bp.post("/<room_code>/messages")
def room_message(room_code):
    """@brief Persist a participant text message for a room.

    @param room_code User-facing room code.
    @return Response JSON message payload or an error payload.
    """
    participant_token = request.headers.get("X-Participant-Token", "")
    if not participant_token:
        return jsonify({"error": "X-Participant-Token is required"}), 401

    payload = request.get_json(silent=True) or {}
    body = (payload.get("body") or "").strip()
    if not body:
        return jsonify({"error": "Message body is required"}), 400

    state = get_room_state(
        room_code,
        current_app.config["ROOM_TTL_SECONDS"],
        current_app.config["PARTICIPANT_TTL_SECONDS"],
        current_app.config["MESSAGE_LIMIT"],
    )
    if state is None:
        return jsonify({"error": "Room not found or expired"}), 404

    message = post_room_message(room_code, participant_token, body)
    if message is None:
        return jsonify({"error": "Participant not found or message invalid"}), 404

    updated_state = get_room_state(
        room_code,
        current_app.config["ROOM_TTL_SECONDS"],
        current_app.config["PARTICIPANT_TTL_SECONDS"],
        current_app.config["MESSAGE_LIMIT"],
    )
    return jsonify({"message": message, "participants": updated_state["participants"], "messages": updated_state["messages"]})


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


def _get_client_ip():
    """@brief Resolve the best-effort client IP from the current request."""
    forwarded_for = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP", "").strip()
    return forwarded_for or real_ip or request.remote_addr or "unknown"
