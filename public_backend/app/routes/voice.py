"""WebSocket voice relay for room-based audio streaming."""
import json
import threading

from flask import Blueprint
from flask_sock import Sock

bp = Blueprint("voice", __name__, url_prefix="/api/voice")

# Room relay: {room_code: {role: ws, ...}}
_rooms = {}
_lock = threading.Lock()


def init_sock(app):
    sock = Sock(app)

    @sock.route("/api/voice/ws/<room_code>/<role>")
    def voice_ws(ws, room_code, role):
        if role not in ("host", "client"):
            ws.close(4000, "Invalid role")
            return

        other_role = "client" if role == "host" else "host"

        with _lock:
            room = _rooms.setdefault(room_code, {})
            room[role] = ws

        try:
            peer = room.get(other_role)
            if peer:
                # Both sides connected, relay bidirectionally
                _relay(ws, peer)
            else:
                # Wait for peer to connect
                _wait_peer(ws)
        finally:
            with _lock:
                room.pop(role, None)
                if not room:
                    _rooms.pop(room_code, None)

    return sock


def _wait_peer(ws):
    """Keep connection alive while waiting for peer."""
    try:
        while True:
            data = ws.receive(timeout=5)
            if data is None:
                continue
    except Exception:
        pass


def _relay(ws_a, ws_b):
    """Bidirectional relay between two WebSocket peers."""

    def forward(src, dst):
        try:
            while True:
                data = src.receive(timeout=1)
                if data is None:
                    continue
                if isinstance(data, str):
                    continue
                dst.send(data)
        except Exception:
            pass

    t1 = threading.Thread(target=forward, args=(ws_a, ws_b), daemon=True)
    t2 = threading.Thread(target=forward, args=(ws_b, ws_a), daemon=True)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
