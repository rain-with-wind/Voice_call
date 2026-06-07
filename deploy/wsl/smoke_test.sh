#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

. .venv/bin/activate

PORT="${VOICE_CALL_TEST_PORT:-5060}"
SERVER_LOG="/tmp/voice_call_cli_server.log"
CLIENT_LOG="/tmp/voice_call_cli_client.log"

rm -f "$SERVER_LOG" "$CLIENT_LOG"

PYTHONUNBUFFERED=1 python3 - <<PY
import json
import os
import subprocess
import time
from pathlib import Path

root = Path("${ROOT_DIR}")
server_log = Path("${SERVER_LOG}")
client_log = Path("${CLIENT_LOG}")
port = "${PORT}"

env = os.environ.copy()
env["PYTHONUNBUFFERED"] = "1"

with server_log.open("w") as server_output, client_log.open("w") as client_output:
    server = subprocess.Popen(
        ["python3", "voice_call.py", "--mode", "server", "--port", port],
        cwd=root,
        stdout=server_output,
        stderr=subprocess.STDOUT,
        env=env,
    )
    time.sleep(3)
    client = subprocess.Popen(
        ["python3", "voice_call.py", "--mode", "client", "--host", "127.0.0.1", "--port", port],
        cwd=root,
        stdout=client_output,
        stderr=subprocess.STDOUT,
        env=env,
    )
    time.sleep(8)

    result = {
        "SERVER_ALIVE": server.poll() is None,
        "CLIENT_ALIVE": client.poll() is None,
        "SERVER_RETURNCODE": server.poll(),
        "CLIENT_RETURNCODE": client.poll(),
    }
    print(json.dumps(result))

    for proc in (server, client):
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=3)
PY

echo "--- SERVER LOG ---"
cat "$SERVER_LOG" || true
echo "--- CLIENT LOG ---"
cat "$CLIENT_LOG" || true
