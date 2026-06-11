"""Core direct TCP voice call runtime."""

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
    """Manage a duplex TCP audio call with optional password auth and encryption."""

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

    def start_server(self) -> None:
        banner("[VOICE CALL] Direct TCP Voice Call Server")
        self._print_runtime_settings()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.config.host, self.config.port))
        self.socket.listen(1)
        self.socket.settimeout(self.config.socket_timeout)

        print(info("[WAIT] Waiting for a client connection...\n"))

        conn = None
        while not self.exit_event.is_set():
            try:
                conn, addr = self.socket.accept()
                print(success(f"[OK] Client connected: {addr[0]}:{addr[1]}"))
                self.conn = conn
                self.connected = True

                if not self.security.authenticate(conn, is_server=True, timeout=self.config.auth_timeout):
                    print(warning("[INFO] Closing unauthenticated connection."))
                    conn.close()
                    self.connected = False
                    continue

                if self.security.use_encryption and self.security.password:
                    salt = self.security.configure_fernet()
                    conn.sendall(salt)
                    print(success("[OK] Encryption enabled."))

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

    def connect_to_server(self, server_host: str) -> None:
        banner("[VOICE CALL] Direct TCP Voice Call Client")
        self._print_runtime_settings(server_host=server_host)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.socket.connect((server_host, self.config.port))
            self.conn = self.socket
            self.connected = True
            print(success("[OK] Connected to the server.\n"))

            if not self.security.authenticate(self.socket, is_server=False, timeout=self.config.auth_timeout):
                print(warning("[INFO] Authentication failed."))
                return

            if self.security.use_encryption and self.security.password:
                salt = self.socket.recv(16)
                self.security.configure_fernet(salt)
                print(success("[OK] Encryption enabled."))

            self._run_call(self.socket)
        except ConnectionRefusedError:
            print(error(f"[ERR] Could not connect to {server_host}:{self.config.port}"))
            print(warning("  1. Ensure the server process is already running."))
            print(warning("  2. Ensure the firewall allows the TCP port."))
            print(warning("  3. Ensure the host/IP address is correct."))
        except Exception as exc:
            print(error(f"[ERR] Connection error: {exc!r}"))
        finally:
            self._close_socket(self.socket)
            self._cleanup()

    def stop(self) -> None:
        self.exit_event.set()
        self._close_socket(self.conn)
        self._close_socket(self.socket)

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
            print(warning("\n\n[INFO] Stopping call..."))
            self.stop()

        print(success("\n\n[OK] Call finished."))

    def _record_and_send(self, conn: socket.socket) -> None:
        print(success("[OK] Microphone stream started."))
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
                    print(error(f"\n[ERR] Send failed: {exc!r}"))
                break

        print(warning("[INFO] Sender thread stopped."))
        self.exit_event.set()

    def _receive_and_play(self, conn: socket.socket) -> None:
        print(success("[OK] Speaker stream started."))
        while not self.exit_event.is_set():
            try:
                length_data = self._recv_exact(conn, 4)
                if not length_data:
                    print(warning("\n[INFO] Peer disconnected."))
                    break

                length = struct.unpack("!I", length_data)[0]
                if length <= 0 or length > 1024 * 1024:
                    print(error(f"\n[ERR] Invalid audio packet size: {length}"))
                    break

                encrypted_data = self._recv_exact(conn, length)
                if not encrypted_data:
                    print(warning("\n[INFO] Peer disconnected."))
                    break

                decrypted = self.security.decrypt(encrypted_data)
                if len(decrypted) % self.config.frame_size != 0:
                    print(error(f"\n[ERR] Invalid PCM frame length: {len(decrypted)}"))
                    break

                self.stats.bytes_received += len(decrypted)
                self.audio.play_chunk(decrypted)
            except socket.timeout:
                continue
            except Exception as exc:
                if not self.exit_event.is_set():
                    print(error(f"\n[ERR] Receive failed: {exc!r}"))
                break

        print(warning("[INFO] Receiver thread stopped."))
        self.exit_event.set()

    def _show_status(self) -> None:
        last_sent = 0
        last_recv = 0
        while not self.exit_event.is_set():
            time.sleep(1)
            if not self.connected:
                continue

            duration = int(time.time() - self.start_time) if self.start_time else 0
            minutes = duration // 60
            seconds = duration % 60
            sent_rate = (self.stats.bytes_sent - last_sent) / 1024
            recv_rate = (self.stats.bytes_received - last_recv) / 1024
            status = (
                f"\r[STATUS] {minutes:02d}:{seconds:02d} | "
                f"UP {sent_rate:5.1f} KB/s | DOWN {recv_rate:5.1f} KB/s | "
                f"Mic {self.stats.format_volume_bar()} {self.stats.last_volume * 100:5.1f}%"
            )
            print(status, end="", flush=True)
            last_sent = self.stats.bytes_sent
            last_recv = self.stats.bytes_received

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
        print(f"Address: {address}")
        print(f"Audio: {self.config.rate}Hz / {self.config.channels} channel(s) / chunk {self.config.chunk}")
        print(success("[AUTH] Password protection enabled.") if self.config.password else warning("[AUTH] Password protection disabled."))
        if self.security.use_encryption:
            print(success("[ENCRYPT] End-to-end encryption enabled."))
        print()

    def _cleanup(self) -> None:
        self.exit_event.set()
        self.connected = False
        self.audio.stop()

        if self.start_time:
            duration = int(time.time() - self.start_time)
            print("\n[STATS] Call summary:")
            print(f"  Duration: {duration} seconds")
            print(f"  Sent: {self.stats.bytes_sent / 1024:.2f} KB")
            print(f"  Received: {self.stats.bytes_received / 1024:.2f} KB")
            print(f"  Audio: {self.config.rate}Hz / {self.config.channels} channel(s)")
            if self.security.use_encryption:
                print("  Encryption: Fernet")

        print(success("[INFO] Goodbye."))

    @staticmethod
    def _close_socket(sock: socket.socket | None) -> None:
        if sock is None:
            return
        try:
            sock.close()
        except Exception:
            pass
