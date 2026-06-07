"""@file engine.py
@brief Audio transport engine for direct duplex voice calls over TCP.
"""

import array
import socket
import threading
import time

import pyaudio

from .config import VoiceCallConfig
from .console import accent, bold, error, format_volume_bar, info, print_banner, success, warning
from .stats import CallStats


class VoiceCall:
    """@brief Manage socket connections, audio streams, and live call status."""

    def __init__(self, config: VoiceCallConfig):
        """@brief Initialize the runtime state for a voice call.

        @param config Audio and socket configuration shared by client/server
            execution paths.
        """
        self.config = config
        self.format = pyaudio.paInt16

        self.audio = pyaudio.PyAudio()
        self.socket = None
        self.conn = None
        self.exit_event = threading.Event()
        self.cleanup_done = False
        self.connected = False

        self.play_stream = None
        self.record_stream = None
        self.stats = CallStats()

    def _init_streams(self):
        """@brief Open playback and recording streams using PyAudio."""
        self.play_stream = self.audio.open(
            format=self.format,
            channels=self.config.channels,
            rate=self.config.rate,
            output=True,
            frames_per_buffer=self.config.chunk,
        )
        self.record_stream = self.audio.open(
            format=self.format,
            channels=self.config.channels,
            rate=self.config.rate,
            input=True,
            frames_per_buffer=self.config.chunk,
        )

    def _calculate_volume(self, data):
        """@brief Estimate microphone loudness from PCM16 audio data.

        @param data Raw PCM16 audio bytes.
        @return float Normalized volume value in the range [0.0, 1.0].
        """
        samples = array.array("h", data)
        if not samples:
            return 0.0

        rms = (sum(sample * sample for sample in samples) / len(samples)) ** 0.5
        return min(1.0, rms / 32768.0)

    def _record_and_send(self, conn):
        """@brief Capture microphone input and forward it to the peer.

        @param conn Active socket connection to the remote peer.
        @return None
        """
        print(success("[OK] Microphone stream started"))
        while not self.exit_event.is_set():
            try:
                data = self.record_stream.read(self.config.chunk, exception_on_overflow=False)
                conn.sendall(data)
                self.stats.add_sent(len(data))
                self.stats.set_volume(self._calculate_volume(data))
            except Exception as exc:
                if not self.exit_event.is_set():
                    print(error(f"\n[ERR] Send failed: {exc}"))
                self.exit_event.set()
                break

        print(warning("[!] Sender thread stopped"))

    def _receive_and_play(self, conn):
        """@brief Receive remote audio and play it through the speaker.

        @param conn Active socket connection to the remote peer.
        @return None
        """
        print(success("[OK] Speaker stream started"))
        while not self.exit_event.is_set():
            try:
                data = conn.recv(self.config.chunk * self.config.channels * 2)
                if not data:
                    print(warning("\n[!] Peer closed the connection"))
                    self.exit_event.set()
                    break

                self.stats.add_received(len(data))
                self.play_stream.write(data)
            except socket.timeout:
                continue
            except Exception as exc:
                if not self.exit_event.is_set():
                    print(error(f"\n[ERR] Receive failed: {exc}"))
                self.exit_event.set()
                break

        print(warning("[!] Receiver thread stopped"))

    def _show_status(self):
        """@brief Render periodic throughput and microphone status updates."""
        last_sent = 0
        last_received = 0

        while not self.exit_event.is_set():
            time.sleep(1)
            if not self.connected:
                continue

            snapshot = self.stats.snapshot()
            if not snapshot["started"]:
                continue

            sent_rate = (snapshot["bytes_sent"] - last_sent) / 1024
            recv_rate = (snapshot["bytes_received"] - last_received) / 1024
            minutes = snapshot["duration"] // 60
            seconds = snapshot["duration"] % 60

            status_line = (
                f"\r{accent('Call')} "
                f"{bold(f'{minutes:02d}:{seconds:02d}')} | "
                f"Up {sent_rate:5.1f} KB/s | "
                f"Down {recv_rate:5.1f} KB/s | "
                f"Mic {format_volume_bar(snapshot['last_volume'])} "
                f"{snapshot['last_volume'] * 100:5.1f}%"
            )
            print(status_line, end="", flush=True)

            last_sent = snapshot["bytes_sent"]
            last_received = snapshot["bytes_received"]

    def _prepare_socket(self):
        """@brief Create a TCP socket configured with the project timeout.

        @return socket.socket Prepared TCP socket instance.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.config.socket_timeout)
        return sock

    def start_server(self):
        """@brief Start the host-side TCP server and wait for one client.

        @return None
        """
        self.socket = self._prepare_socket()
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.config.host, self.config.port))
        self.socket.listen(1)

        print_banner("Voice Call Server")
        print(f"Listening on {warning(f'{self.config.host}:{self.config.port}')}")
        print(info("Waiting for a client...\n"))

        conn = None
        while not self.exit_event.is_set():
            try:
                conn, addr = self.socket.accept()
                conn.settimeout(self.config.socket_timeout)
                print(success(f"[OK] Client connected: {addr[0]}:{addr[1]}"))
                self.conn = conn
                self.connected = True
                break
            except socket.timeout:
                continue

        if self.exit_event.is_set():
            if conn is not None:
                conn.close()
            self._cleanup()
            return

        try:
            self._run_call(conn)
        finally:
            self._cleanup()

    def connect_to_server(self, server_host):
        """@brief Connect to an already running voice call server.

        @param server_host Hostname or IP address of the remote server.
        @return None
        """
        self.socket = self._prepare_socket()

        print_banner("Voice Call Client")
        print(f"Connecting to {warning(f'{server_host}:{self.config.port}')}")

        try:
            self.socket.connect((server_host, self.config.port))
            self.conn = self.socket
            self.connected = True
            print(success("[OK] Connected to server\n"))
            self._run_call(self.socket)
        except ConnectionRefusedError:
            print(error("[ERR] Connection refused. Make sure the server is running."))
        except socket.timeout:
            print(error("[ERR] Connection timed out. Check host reachability and firewall rules."))
        except Exception as exc:
            print(error(f"[ERR] Connection failed: {exc}"))
        finally:
            self._cleanup()

    def _run_call(self, conn):
        """@brief Start worker threads and keep the call alive until exit.

        @param conn Connected socket shared by sender and receiver threads.
        @return None
        """
        self._init_streams()
        self.stats.mark_started()

        sender = threading.Thread(target=self._record_and_send, args=(conn,), daemon=True)
        receiver = threading.Thread(target=self._receive_and_play, args=(conn,), daemon=True)
        status = threading.Thread(target=self._show_status, daemon=True)

        sender.start()
        receiver.start()
        status.start()

        try:
            while not self.exit_event.is_set():
                if not sender.is_alive() and not receiver.is_alive():
                    break
                time.sleep(0.1)
        except KeyboardInterrupt:
            print(warning("\n\n[!] Stopping call..."))
            self.stop()

        print(success("\n\n[OK] Call finished"))

    def _cleanup(self):
        """@brief Release sockets, audio streams, and print a call summary."""
        if self.cleanup_done:
            return

        self.cleanup_done = True
        self.exit_event.set()
        self.connected = False

        if self.conn is not None:
            try:
                self.conn.close()
            except OSError:
                pass
            self.conn = None

        if self.socket is not None:
            try:
                self.socket.close()
            except OSError:
                pass
            self.socket = None

        if self.play_stream is not None:
            try:
                self.play_stream.stop_stream()
                self.play_stream.close()
            except OSError:
                pass
            self.play_stream = None

        if self.record_stream is not None:
            try:
                self.record_stream.stop_stream()
                self.record_stream.close()
            except OSError:
                pass
            self.record_stream = None

        try:
            self.audio.terminate()
        except OSError:
            pass

        snapshot = self.stats.snapshot()
        if snapshot["started"]:
            print(accent("\nCall summary:"))
            print(f"  Duration: {snapshot['duration']} seconds")
            print(f"  Sent: {snapshot['bytes_sent'] / 1024:.2f} KB")
            print(f"  Received: {snapshot['bytes_received'] / 1024:.2f} KB")

        print(success("Goodbye."))

    def stop(self):
        """@brief Request call termination and perform cleanup."""
        self.exit_event.set()
        self._cleanup()
