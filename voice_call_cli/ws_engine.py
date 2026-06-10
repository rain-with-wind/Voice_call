"""@file ws_engine.py
@brief WebSocket-based audio transport for voice calls through the backend.
"""
import array
import json
import threading
import time

import pyaudio
from websocket import WebSocket

from .config import VoiceCallConfig
from .console import accent, bold, error, format_volume_bar, info, print_banner, success, warning
from .stats import CallStats


class VoiceCallWS:
    """Manage WebSocket-based voice calls through the public backend relay."""

    def __init__(self, config: VoiceCallConfig):
        self.config = config
        self.format = pyaudio.paInt16

        self.audio = pyaudio.PyAudio()
        self.ws_a = None  # send channel
        self.ws_b = None  # recv channel (same ws, different threads)
        self.exit_event = threading.Event()
        self.connected = False

        self.play_stream = None
        self.record_stream = None
        self.stats = CallStats()

    def _init_streams(self):
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
        import array as arr
        samples = arr.array("h", data)
        if not samples:
            return 0.0
        rms = (sum(s * s for s in samples) / len(samples)) ** 0.5
        return min(1.0, rms / 32768.0)

    def _send_audio(self, ws):
        while not self.exit_event.is_set():
            try:
                data = self.record_stream.read(self.config.chunk, exception_on_overflow=False)
                ws.send_binary(data)
                self.stats.add_sent(len(data))
                self.stats.set_volume(self._calculate_volume(data))
            except Exception:
                self.exit_event.set()
                break

    def _recv_audio(self, ws):
        while not self.exit_event.is_set():
            try:
                opcode, data = ws.recv_data()
                if opcode == 8:
                    break
                if opcode == 2:
                    self.stats.add_received(len(data))
                    self.play_stream.write(data)
            except Exception:
                self.exit_event.set()
                break

    def _show_status(self):
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

    def start(self, backend_url: str, room_code: str, role: str):
        """Connect to backend WebSocket relay and start the call.

        @param backend_url Public backend base URL (http/https).
        @param room_code Room code from the backend.
        @param role Either 'host' or 'client'.
        """
        ws_url = backend_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = f"{ws_url}/api/voice/ws/{room_code}/{role}"

        print_banner(f"Voice Call ({role.upper()})")
        print(f"Room code: {success(room_code)}")
        print(f"Connecting to relay...")

        ws = WebSocket()
        try:
            ws.connect(ws_url)
        except Exception as exc:
            print(error(f"[ERR] Failed to connect: {exc}"))
            self._cleanup()
            return

        self.ws_a = ws
        self.connected = True
        print(success(f"[OK] Connected to relay (role: {role})"))
        print(info("Waiting for peer...\n"))

        try:
            self._init_streams()
            self.stats.mark_started()

            sender = threading.Thread(target=self._send_audio, args=(ws,), daemon=True)
            receiver = threading.Thread(target=self._recv_audio, args=(ws,), daemon=True)
            status = threading.Thread(target=self._show_status, daemon=True)

            sender.start()
            receiver.start()
            status.start()

            while not self.exit_event.is_set():
                if not sender.is_alive() and not receiver.is_alive():
                    break
                time.sleep(0.1)
        except KeyboardInterrupt:
            print(warning("\n\n[!] Stopping call..."))
            self.stop()
        finally:
            self._cleanup()

    def _cleanup(self):
        self.exit_event.set()
        self.connected = False

        if self.ws_a is not None:
            try:
                self.ws_a.close()
            except Exception:
                pass
            self.ws_a = None

        if self.play_stream is not None:
            try:
                self.play_stream.stop_stream()
                self.play_stream.close()
            except Exception:
                pass
            self.play_stream = None

        if self.record_stream is not None:
            try:
                self.record_stream.stop_stream()
                self.record_stream.close()
            except Exception:
                pass
            self.record_stream = None

        try:
            self.audio.terminate()
        except Exception:
            pass

        snapshot = self.stats.snapshot()
        if snapshot["started"]:
            print(accent("\nCall summary:"))
            print(f"  Duration: {snapshot['duration']} seconds")
            print(f"  Sent: {snapshot['bytes_sent'] / 1024:.2f} KB")
            print(f"  Received: {snapshot['bytes_received'] / 1024:.2f} KB")

        print(success("Goodbye."))

    def stop(self):
        self.exit_event.set()
        self._cleanup()
