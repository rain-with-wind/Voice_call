#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

. .venv/bin/activate
HOST="${1:-127.0.0.1}"
PORT="${VOICE_CALL_PORT:-5000}"

exec python3 -u voice_call.py --mode client --host "$HOST" --port "$PORT"
