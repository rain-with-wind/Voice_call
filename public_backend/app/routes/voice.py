"""WebSocket voice relay for room-based audio streaming."""
import threading

from flask import Blueprint
from flask_sock import Sock

bp = Blueprint("voice", __name__, url_prefix="/api/voice")

_rooms = {}
_lock = threading.Lock()


def init_sock(app):
    sock = Sock(app)

    @sock.route("/api/voice/ws/<room_code>/<role>")
    def voice_ws(ws, room_code, role):
        if role not in ("host", "client"):
            ws.close(4000, "Invalid role")
            return

        other = "client" if role == "host" else "host"

        with _lock:
            room = _rooms.setdefault(room_code, {})
            room[role] = ws
            peer = room.get(other)
            if not peer:
                room["_ready"] = threading.Event()

        if peer:
            # Second peer — wake up the first peer that's waiting
            ready = room.get("_ready")
            if ready:
                ready.set()
        else:
            # First peer — wait for second peer to arrive
            room["_ready"].wait(timeout=120)

        peer = room.get(other)
        if peer:
            _relay(ws, peer)

        with _lock:
            room.pop(role, None)
            room.pop("_ready", None)
            if not room:
                _rooms.pop(room_code, None)

    return sock


def _relay(ws_a, ws_b):
    """Bidirectional relay between two WebSocket peers."""

    def forward(src, dst, stop):
        try:
            while not stop.is_set():
                data = src.receive(timeout=1)
                if data is None:
                    continue
                if isinstance(data, str):
                    continue
                dst.send(data)
        except Exception:
            pass
        finally:
            stop.set()

    stop = threading.Event()
    t1 = threading.Thread(target=forward, args=(ws_a, ws_b, stop), daemon=True)
    t2 = threading.Thread(target=forward, args=(ws_b, ws_a, stop), daemon=True)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
