#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

. .venv-backend/bin/activate

export PUBLIC_VOICE_BACKEND_HOST="${PUBLIC_VOICE_BACKEND_HOST:-0.0.0.0}"
export PUBLIC_VOICE_BACKEND_PORT="${PUBLIC_VOICE_BACKEND_PORT:-8100}"

exec gunicorn --bind "${PUBLIC_VOICE_BACKEND_HOST}:${PUBLIC_VOICE_BACKEND_PORT}" public_backend.wsgi:app
