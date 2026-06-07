#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

. .venv-backend/bin/activate

BACKEND_LOG="/tmp/public_voice_backend.log"
rm -f "$BACKEND_LOG"

PUBLIC_VOICE_BACKEND_PORT="${PUBLIC_VOICE_BACKEND_PORT:-8101}"
PUBLIC_VOICE_BACKEND_HOST="127.0.0.1" \
PUBLIC_VOICE_BACKEND_PORT="$PUBLIC_VOICE_BACKEND_PORT" \
gunicorn --bind "127.0.0.1:${PUBLIC_VOICE_BACKEND_PORT}" public_backend.wsgi:app >"$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!
sleep 4

PUBLIC_VOICE_BACKEND_PORT="$PUBLIC_VOICE_BACKEND_PORT" python3 - <<'PY'
import json
import os
import urllib.request

base = f"http://127.0.0.1:{os.environ['PUBLIC_VOICE_BACKEND_PORT']}"

def request(path, method="GET", data=None, headers=None):
    import json as _json
    body = None if data is None else _json.dumps(data).encode("utf-8")
    req = urllib.request.Request(base + path, data=body, method=method, headers=headers or {"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

health = request("/api/health")
registered = request("/api/rooms/register", "POST", {
    "name": "Smoke Test Room",
    "public_host": "call.example.com",
    "public_port": 5000,
    "owner_name": "tester",
    "notes": "backend smoke test"
})
room_code = registered["room"]["room_code"]
rooms = request("/api/rooms")
detail = request(f"/api/rooms/{room_code}")
print(json.dumps({
    "health_status": health["status"],
    "registered_room_code": room_code,
    "rooms_count": len(rooms["rooms"]),
    "detail_host": detail["room"]["public_host"],
}, ensure_ascii=False))
PY

kill "$BACKEND_PID" 2>/dev/null || true
wait "$BACKEND_PID" 2>/dev/null || true

echo "--- BACKEND LOG ---"
cat "$BACKEND_LOG" || true
