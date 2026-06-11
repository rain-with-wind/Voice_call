"""Audio device management helpers."""

from __future__ import annotations

import array
import os

import pyaudio

from .config import VoiceCallConfig
from .console import info


class AudioIO:
    """Own the PyAudio instance and both input/output streams."""

    def __init__(self, config: VoiceCallConfig) -> None:
        self.config = config
        self.audio: pyaudio.PyAudio | None = None
        self.play_stream = None
        self.record_stream = None

    def start(self) -> None:
        if self.audio is None:
            self.audio = pyaudio.PyAudio()

        print(info(f"[AUDIO] rate={self.config.rate}, channels={self.config.channels}, chunk={self.config.chunk}"))
        output_device_index = self._pick_device_index(is_input=False)
        input_device_index = self._pick_device_index(is_input=True)

        if output_device_index is not None:
            print(info(f"[AUDIO] output_device={self.audio.get_device_info_by_index(output_device_index).get('name')}"))
        if input_device_index is not None:
            print(info(f"[AUDIO] input_device={self.audio.get_device_info_by_index(input_device_index).get('name')}"))

        self.play_stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=self.config.channels,
            rate=self.config.rate,
            output=True,
            frames_per_buffer=self.config.chunk,
            output_device_index=output_device_index,
        )
        self.record_stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=self.config.channels,
            rate=self.config.rate,
            input=True,
            frames_per_buffer=self.config.chunk,
            input_device_index=input_device_index,
        )

    def read_chunk(self) -> bytes:
        return self.record_stream.read(self.config.chunk, exception_on_overflow=False)

    def play_chunk(self, data: bytes) -> None:
        self.play_stream.write(data)

    def stop(self) -> None:
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

        if self.audio is not None:
            try:
                self.audio.terminate()
            except Exception:
                pass
            self.audio = None

    def calculate_volume(self, data: bytes) -> float:
        try:
            samples = array.array("h", data)
        except Exception:
            return 0.0

        if not samples:
            return 0.0

        rms = (sum(sample * sample for sample in samples) / len(samples)) ** 0.5
        return min(1.0, rms / 32768.0)

    def _pick_device_index(self, *, is_input: bool) -> int | None:
        if self.audio is None:
            return None

        preferred_names: list[str] = []
        if os.environ.get("WSL_DISTRO_NAME") or os.environ.get("PULSE_SERVER"):
            preferred_names.extend(["pulse", "default"])
        else:
            preferred_names.extend(["default", "pulse"])

        matched_fallback = None
        for index in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(index)
            channels = int(info.get("maxInputChannels" if is_input else "maxOutputChannels", 0))
            if channels <= 0:
                continue

            name = str(info.get("name", "")).lower()
            if matched_fallback is None:
                matched_fallback = index

            for preferred_name in preferred_names:
                if preferred_name in name:
                    return index

        return matched_fallback
