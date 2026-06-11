"""Authentication and optional symmetric encryption helpers."""

from __future__ import annotations

import base64
import hashlib
import secrets
import socket

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .console import error, success, warning


class SecurityContext:
    """Manage password authentication and optional Fernet encryption."""

    def __init__(self, password: str | None, use_encryption: bool) -> None:
        self.password = password
        self.use_encryption = use_encryption
        self.fernet: Fernet | None = None

    def encrypt(self, data: bytes) -> bytes:
        if self.fernet is None:
            return data
        return self.fernet.encrypt(data)

    def decrypt(self, data: bytes) -> bytes:
        if self.fernet is None:
            return data
        return self.fernet.decrypt(data)

    def configure_fernet(self, salt: bytes | None = None) -> bytes | None:
        if not (self.password and self.use_encryption):
            return None

        try:
            if salt is None:
                salt = secrets.token_bytes(16)
            key = self._derive_key(self.password, salt)
            self.fernet = Fernet(key)
            return salt
        except Exception as exc:
            print(warning(f"[WARN] Failed to initialize encryption: {exc}"))
            self.use_encryption = False
            self.fernet = None
            return None

    def authenticate(self, conn: socket.socket, *, is_server: bool, timeout: float) -> bool:
        if not self.password:
            return True

        try:
            conn.settimeout(timeout)
            if is_server:
                print("[WAIT] Waiting for password authentication...")
                raw = conn.recv(4096)
                if not raw:
                    print(error("[ERR] No authentication payload received."))
                    return False
                try:
                    message = raw.decode()
                except Exception:
                    print(error("[ERR] Authentication payload is not valid UTF-8."))
                    return False

                if not message.startswith("AUTH:"):
                    print(error("[ERR] Unsupported authentication payload."))
                    return False

                received_hash = message[5:]
                if received_hash == self._hash_password(self.password):
                    conn.sendall(b"AUTH:OK")
                    print(success("[OK] Authentication accepted."))
                    return True

                conn.sendall(b"AUTH:FAIL")
                print(error("[ERR] Authentication failed: wrong password."))
                return False

            conn.sendall(f"AUTH:{self._hash_password(self.password)}".encode())
            response = conn.recv(4096).decode()
            if response == "AUTH:OK":
                print(success("[OK] Authentication accepted."))
                return True

            print(error("[ERR] Authentication failed: wrong password."))
            return False
        except socket.timeout:
            print(error("[ERR] Authentication timed out."))
            return False
        except Exception as exc:
            print(error(f"[ERR] Authentication error: {exc}"))
            return False

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def _derive_key(password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend(),
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
