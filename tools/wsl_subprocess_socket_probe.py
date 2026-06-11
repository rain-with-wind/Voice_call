"""Verify localhost connectivity between WSL Python subprocesses."""

from __future__ import annotations

import socket
import subprocess
import sys
import time
from pathlib import Path


PORT = 5062
ROOT = Path(__file__).resolve().parent
SERVER_SCRIPT = ROOT / "_tmp_socket_server.py"


SERVER_CODE = """\
import socket
import sys
import time

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("0.0.0.0", 5062))
s.listen(1)
print("listening", flush=True)
c, addr = s.accept()
print(f"accepted={addr}", flush=True)
c.sendall(b"ok")
c.close()
s.close()
time.sleep(0.2)
"""


def main() -> int:
    SERVER_SCRIPT.write_text(SERVER_CODE, encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, str(SERVER_SCRIPT)],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        time.sleep(1)
        try:
            output_so_far = proc.stdout.read(10)
        except Exception:
            output_so_far = ""
        print(f"server_output_prefix={output_so_far!r}")

        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        probe.settimeout(3)
        result = probe.connect_ex(("127.0.0.1", PORT))
        print(f"connect_ex={result}")
        if result == 0:
            print(f"recv={probe.recv(2)!r}")
        probe.close()

        proc.wait(timeout=5)
        remaining = proc.stdout.read() if proc.stdout else ""
        print(f"server_remaining={remaining!r}")
        print(f"server_exit={proc.returncode}")
        return 0
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)
        try:
            SERVER_SCRIPT.unlink()
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    sys.exit(main())
