#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -d ".venv-backend" ]]; then
  python3 -m venv .venv-backend
fi

. .venv-backend/bin/activate
pip install --upgrade pip
pip install -r requirements-backend.txt

echo "Public backend environment is ready."
echo "Start command: bash deploy/public/run_backend_wsl.sh"
