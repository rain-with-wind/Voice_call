"""直接 TCP 语音通话核心引擎。"""

from __future__ import annotations

import socket
import struct
import threading
import time

from .audio import AudioIO
from .config import VoiceCallConfig
from .console import banner, error, info, success, warning
from .crypto import SecurityContext
from .stats import CallStats


class VoiceCall:
    """管理双向 TCP 语音通话，支持可选密码认证和 Fernet 加密。"""

    def __init__(self, config: VoiceCallConfig) -> None:
        self.config = config
        self.audio = AudioIO(config)
        self.security = SecurityContext(config.password, config.use_encryption)
        self.stats = CallStats()

        self.exit_event = threading.Event()
        self.socket: socket.socket | None = None
        self.conn: socket.socket | None = None
        self.connected = False
        self.start_time: float | None = None

    # ---- 服务端 ----

    def start_server(self) -> None:
        banner("语音通话 - 服务端")
        self._print_runtime_settings()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.config.host, self.config.port))
        self.socket.listen(1)
        self.socket.settimeout(self.config.socket_timeout)

        print(info(f"[等待] 等待客户端连接 {self.config.host}:{self.config.port} ...\n"))

        conn = None
        while not self.exit_event.is_set():
            try:
                conn, addr = self.socket.accept()
                print(success(f"[连接] 客户端已连接: {addr[0]}:{addr[1]}"))
                self.conn = conn
                self.connected = True

                if not self.security.authenticate(conn, is_server=True, timeout=self.config.auth_timeout):
                    print(warning("[提示] 认证失败，断开连接。"))
                    conn.close()
                    self.connected = False
                    continue

                if self.security.use_encryption and self.security.password:
                    salt = self.security.configure_fernet()
                    conn.sendall(salt)
                    print(success("[加密] 端到端加密已启用。"))

                break
            except socket.timeout:
                continue
            except OSError:
                if self.exit_event.is_set():
                    break
                raise

        if self.exit_event.is_set() or not self.connected or conn is None:
            self._close_socket(self.socket)
            return

        try:
            self._run_call(conn)
        finally:
            self._close_socket(conn)
            self._cleanup()

    # ---- 客户端 ----

    def connect_to_server(self, server_host: str) -> None:
        banner("语音通话 - 客户端")
        self._print_runtime_settings(server_host=server_host)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.socket.connect((server_host, self.config.port))
            self.conn = self.socket
            self.connected = True
            print(success(f"[连接] 已连接到服务器 {server_host}:{self.config.port}\n"))

            if not self.security.authenticate(self.socket, is_server=False, timeout=self.config.auth_timeout):
                print(warning("[提示] 认证失败。"))
                return

            if self.security.use_encryption and self.security.password:
                salt = self.socket.recv(16)
                self.security.configure_fernet(salt)
                print(success("[加密] 端到端加密已启用。"))

            self._run_call(self.socket)
        except ConnectionRefusedError:
            print(error(f"[错误] 无法连接到 {server_host}:{self.config.port}"))
            print(warning("  1. 请确认服务端已启动"))
            print(warning("  2. 请确认防火墙未阻止该端口"))
            print(warning("  3. 请确认 IP 地址正确"))
        except socket.timeout:
            print(error(f"[错误] 连接超时，请检查网络可达性。"))
        except Exception as exc:
            print(error(f"[错误] 连接失败: {exc!r}"))
        finally:
            self._close_socket(self.socket)
            self._cleanup()

    def stop(self) -> None:
        self.exit_event.set()
        self._close_socket(self.conn)
        self._close_socket(self.socket)

    # ---- 通话主循环 ----

    def _run_call(self, conn: socket.socket) -> None:
        conn.settimeout(self.config.socket_timeout)
        self.audio.start()
        self.start_time = time.time()

        send_thread = threading.Thread(target=self._record_and_send, args=(conn,), daemon=True)
        receive_thread = threading.Thread(target=self._receive_and_play, args=(conn,), daemon=True)
        status_thread = threading.Thread(target=self._show_status, daemon=True)

        send_thread.start()
        receive_thread.start()
        status_thread.start()

        try:
            while not self.exit_event.is_set():
                if not send_thread.is_alive() and not receive_thread.is_alive():
                    break
                time.sleep(0.1)
        except KeyboardInterrupt:
            print(warning("\n\n[提示] 正在退出通话..."))
            self.stop()

        print(success("\n\n[通话结束]"))

    # ---- 音频发送 ----

    def _record_and_send(self, conn: socket.socket) -> None:
        print(success("[麦克风] 已启动"))
        while not self.exit_event.is_set():
            try:
                raw = self.audio.read_chunk()
                encrypted = self.security.encrypt(raw)
                packet = struct.pack("!I", len(encrypted)) + encrypted
                conn.sendall(packet)
                self.stats.bytes_sent += len(raw)
                self.stats.last_volume = self.audio.calculate_volume(raw)

            except Exception as exc:
                if not self.exit_event.is_set():
                    print(error(f"\n[错误] 发送失败: {exc!r}"))
                break

        print(warning("[提示] 发送线程已停止"))
        self.exit_event.set()

    # ---- 音频接收 ----

    def _receive_and_play(self, conn: socket.socket) -> None:
        print(success("[扬声器] 已启动"))
        while not self.exit_event.is_set():
            try:
                length_data = self._recv_exact(conn, 4)
                if not length_data:
                    print(warning("\n[提示] 对方已断开连接"))
                    break

                length = struct.unpack("!I", length_data)[0]
                if length <= 0 or length > 1024 * 1024:
                    print(error(f"\n[错误] 无效的音频包大小: {length}"))
                    break

                encrypted_data = self._recv_exact(conn, length)
                if not encrypted_data:
                    print(warning("\n[提示] 对方已断开连接"))
                    break

                decrypted = self.security.decrypt(encrypted_data)
                if len(decrypted) % self.config.frame_size != 0:
                    print(error(f"\n[错误] PCM 帧长度异常: {len(decrypted)}"))
                    break

                self.stats.bytes_received += len(decrypted)
                self.audio.play_chunk(decrypted)
            except socket.timeout:
                continue
            except Exception as exc:
                if not self.exit_event.is_set():
                    print(error(f"\n[错误] 接收失败: {exc!r}"))
                break

        print(warning("[提示] 接收线程已停止"))
        self.exit_event.set()

    # ---- 实时状态栏 ----

    def _show_status(self) -> None:
        last_sent = 0
        last_recv = 0
        while not self.exit_event.is_set():
            time.sleep(0.25)
            if not self.connected:
                continue

            duration = int(time.time() - self.start_time) if self.start_time else 0
            m, s = duration // 60, duration % 60
            up_kbps = (self.stats.bytes_sent - last_sent) / 1024 / 0.25
            down_kbps = (self.stats.bytes_received - last_recv) / 1024 / 0.25
            vol_bar = self.stats.format_volume_bar()
            vol_pct = self.stats.last_volume * 100

            line = (
                f"\r通话 {m:02d}:{s:02d} │ "
                f"上传 {up_kbps:5.1f} KB/s │ "
                f"下载 {down_kbps:5.1f} KB/s │ "
                f"麦克风 {vol_bar} {vol_pct:5.1f}%"
            )
            print(line, end="", flush=True)
            last_sent = self.stats.bytes_sent
            last_recv = self.stats.bytes_received

    # ---- 工具方法 ----

    def _recv_exact(self, conn: socket.socket, expected: int) -> bytes | None:
        data = b""
        while len(data) < expected and not self.exit_event.is_set():
            try:
                packet = conn.recv(expected - len(data))
            except socket.timeout:
                continue

            if not packet:
                return None
            data += packet

        return data if len(data) == expected else None

    def _print_runtime_settings(self, server_host: str | None = None) -> None:
        address = f"{server_host}:{self.config.port}" if server_host else f"{self.config.host}:{self.config.port}"
        print(f"地址: {address}")
        print(f"音频: {self.config.rate}Hz / {self.config.channels} 声道 / 帧 {self.config.chunk}")
        if self.config.password:
            print(success("[认证] 密码保护已启用"))
        else:
            print(warning("[认证] 密码保护未启用"))
        if self.security.use_encryption:
            print(success("[加密] 端到端加密已启用"))
        else:
            print(warning("[加密] 端到端加密未启用"))
        print()

    def _cleanup(self) -> None:
        self.exit_event.set()
        self.connected = False
        self.audio.stop()

        if self.start_time:
            duration = int(time.time() - self.start_time) if self.start_time else 0
            m, s = duration // 60, duration % 60
            print(f"\n{'─' * 40}")
            print(f"  通话统计")
            print(f"  时长:  {m} 分 {s} 秒")
            print(f"  发送:  {self.stats.bytes_sent / 1024:.1f} KB")
            print(f"  接收:  {self.stats.bytes_received / 1024:.1f} KB")
            print(f"  音频:  {self.config.rate}Hz / {self.config.channels} 声道")
            if self.security.use_encryption:
                print(f"  加密:  Fernet (端到端)")
            print(f"{'─' * 40}")

        print(success("[提示] 再见！"))

    @staticmethod
    def _close_socket(sock: socket.socket | None) -> None:
        if sock is None:
            return
        try:
            sock.close()
        except Exception:
            pass
