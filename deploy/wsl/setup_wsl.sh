#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -d ".venv" ]]; then
  python3 -m venv .venv
fi

. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "WSL setup complete."
echo "Server command: bash deploy/wsl/run_server.sh"
echo "Client command: bash deploy/wsl/run_client.sh 127.0.0.1"
