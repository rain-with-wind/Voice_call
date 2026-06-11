"""认证与可选对称加密。"""

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
    """管理密码认证和可选的 Fernet 端到端加密。"""

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
            print(warning(f"[警告] 加密初始化失败: {exc}"))
            self.use_encryption = False
            self.fernet = None
            return None

    def authenticate(self, conn: socket.socket, *, is_server: bool, timeout: float) -> bool:
        if not self.password:
            return True

        try:
            conn.settimeout(timeout)
            if is_server:
                print("[等待] 等待客户端密码认证...")
                raw = conn.recv(4096)
                if not raw:
                    print(error("[错误] 未收到认证数据"))
                    return False
                try:
                    message = raw.decode()
                except Exception:
                    print(error("[错误] 认证数据解码失败"))
                    return False

                if not message.startswith("AUTH:"):
                    print(error("[错误] 不支持的认证协议"))
                    return False

                received_hash = message[5:]
                if received_hash == self._hash_password(self.password):
                    conn.sendall(b"AUTH:OK")
                    print(success("[认证] 密码正确，认证通过"))
                    return True

                conn.sendall(b"AUTH:FAIL")
                print(error("[错误] 密码错误，认证失败"))
                return False

            conn.sendall(f"AUTH:{self._hash_password(self.password)}".encode())
            response = conn.recv(4096).decode()
            if response == "AUTH:OK":
                print(success("[认证] 密码正确，认证通过"))
                return True

            print(error("[错误] 密码错误，认证失败"))
            return False
        except socket.timeout:
            print(error("[错误] 认证超时"))
            return False
        except Exception as exc:
            print(error(f"[错误] 认证异常: {exc}"))
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
