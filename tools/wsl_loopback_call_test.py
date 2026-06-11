"""Run a local server/client call inside WSL and capture logs."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path


PORT = 5051
ROOT = Path(__file__).resolve().parents[1]
PYTHON = "/mnt/d/QQ/Downloads/Voice_call/Voice_call/.venv/bin/python3"
ENTRYPOINT = ROOT / "voice_call.py"
SERVER_LOG = ROOT / "server_loopback.log"
CLIENT_LOG = ROOT / "client_loopback.log"


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def main() -> int:
    for path in (SERVER_LOG, CLIENT_LOG):
        try:
            path.unlink()
        except FileNotFoundError:
            pass

    server_cmd = [PYTHON, str(ENTRYPOINT), "--mode", "server", "--port", str(PORT)]
    client_cmd = [
        PYTHON,
        str(ENTRYPOINT),
        "--mode",
        "client",
        "--host",
        "127.0.0.1",
        "--port",
        str(PORT),
    ]

    server_log = SERVER_LOG.open("w", encoding="utf-8")
    client_log = CLIENT_LOG.open("w", encoding="utf-8")
    server = None
    client = None

    try:
        server = subprocess.Popen(
            server_cmd,
            cwd=ROOT,
            stdout=server_log,
            stderr=subprocess.STDOUT,
            text=True,
        )
        time.sleep(2)
        client = subprocess.Popen(
            client_cmd,
            cwd=ROOT,
            stdout=client_log,
            stderr=subprocess.STDOUT,
            text=True,
        )
        time.sleep(8)
    finally:
        for proc in (client, server):
            if proc is None or proc.poll() is not None:
                continue
            proc.send_signal(signal.SIGINT)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)

        server_log.close()
        client_log.close()

    print("--- server log ---")
    print(_read_text(SERVER_LOG))
    print("--- client log ---")
    print(_read_text(CLIENT_LOG))
    print("--- exit codes ---")
    print(
        f"server={None if server is None else server.returncode} "
        f"client={None if client is None else client.returncode}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
