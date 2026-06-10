"""@file device_info.py
@brief Device token generation and local environment collection helpers.
"""

from __future__ import annotations

import json
from pathlib import Path
import platform
import secrets
import socket
from typing import Any


TOKEN_DIR = Path.home() / ".voice_call"
TOKEN_FILE = TOKEN_DIR / "device_token.json"


def get_or_create_device_token(reset_token: bool = False) -> str:
    """@brief Load or create a persistent local device token.

    @param reset_token Whether to force-generate a fresh token.
    @return str Stable device token stored on disk.
    """
    if reset_token and TOKEN_FILE.exists():
        TOKEN_FILE.unlink()

    if TOKEN_FILE.exists():
        try:
            payload = json.loads(TOKEN_FILE.read_text(encoding="utf-8"))
            token = str(payload.get("device_token", "")).strip()
            if token:
                return token
        except (json.JSONDecodeError, OSError):
            pass

    token = f"vc-{secrets.token_urlsafe(18)}"
    TOKEN_DIR.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(json.dumps({"device_token": token}, ensure_ascii=True, indent=2), encoding="utf-8")
    return token


def collect_device_info(reset_token: bool = False) -> dict[str, Any]:
    """@brief Collect a local device token and environment information.

    @param reset_token Whether to regenerate the stored device token.
    @return dict Structured device information.
    """
    hostname = socket.gethostname()
    return {
        "device_token": get_or_create_device_token(reset_token=reset_token),
        "hostname": hostname,
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "python_version": platform.python_version(),
        "local_ip_candidates": _collect_local_ip_candidates(hostname),
        "token_file": str(TOKEN_FILE),
    }


def print_device_info(json_output: bool = False, reset_token: bool = False) -> None:
    """@brief Print collected device information to stdout.

    @param json_output Whether to emit JSON only.
    @param reset_token Whether to regenerate the stored device token.
    @return None
    """
    info = collect_device_info(reset_token=reset_token)
    if json_output:
        print(json.dumps(info, ensure_ascii=False, indent=2))
        return

    print("Voice Call Device Info")
    print(f"  Device token : {info['device_token']}")
    print(f"  Hostname     : {info['hostname']}")
    print(f"  Platform     : {info['platform']}")
    print(f"  Python       : {info['python_version']}")
    print(f"  Token file   : {info['token_file']}")
    print("  Local IPs    :")
    for ip in info["local_ip_candidates"]:
        print(f"    - {ip}")


def _collect_local_ip_candidates(hostname: str) -> list[str]:
    """@brief Best-effort collection of local IP candidates.

    @param hostname Local host name.
    @return list[str] Unique local IP addresses.
    """
    candidates = {"127.0.0.1"}
    try:
        for family, _socktype, _proto, _canon, sockaddr in socket.getaddrinfo(hostname, None):
            if family in (socket.AF_INET, socket.AF_INET6):
                ip = sockaddr[0]
                if ip:
                    candidates.add(ip)
    except socket.gaierror:
        pass

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            candidates.add(sock.getsockname()[0])
    except OSError:
        pass

    return sorted(candidates)
