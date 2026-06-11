"""音频设备管理（麦克风 / 扬声器）。"""

from __future__ import annotations

import array
import os

import pyaudio

from .config import VoiceCallConfig
from .console import Colors, colored, info, warning


class AudioIO:
    """管理 PyAudio 实例和输入/输出音频流。"""

    def __init__(self, config: VoiceCallConfig) -> None:
        self.config = config
        self.audio: pyaudio.PyAudio | None = None
        self.play_stream = None
        self.record_stream = None
        self._input_device_name: str = "?"

    def start(self) -> None:
        if self.audio is None:
            self.audio = pyaudio.PyAudio()

        print(info(f"[音频] {self.config.rate}Hz / {self.config.channels} 声道 / 帧长 {self.config.chunk}"))

        # 列出所有音频设备
        self._list_devices()

        output_device_index = self.config.output_device_index
        if output_device_index is None:
            output_device_index = self._pick_device_index(is_input=False)

        input_device_index = self.config.input_device_index
        if input_device_index is None:
            input_device_index = self._pick_device_index(is_input=True)

        if output_device_index is not None:
            name = self.audio.get_device_info_by_index(output_device_index).get("name", "?")
            print(info(f"[输出] {name}"))
        if input_device_index is not None:
            name = self.audio.get_device_info_by_index(input_device_index).get("name", "?")
            self._input_device_name = name
            print(info(f"[输入] {name}"))

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

    # ---- 设备选择 ----

    @staticmethod
    def list_devices_static() -> None:
        """仅列出所有音频设备（无需完整初始化）。"""
        audio = pyaudio.PyAudio()
        count = audio.get_device_count()
        if count == 0:
            print(warning("[音频] 未检测到任何音频设备！"))
            audio.terminate()
            return

        default_in = audio.get_default_input_device_info()
        default_out = audio.get_default_output_device_info()
        print(info(f"[音频] 共 {count} 个设备 (默认输入: {default_in.get('name')}, 默认输出: {default_out.get('name')}):"))
        for i in range(count):
            dev = audio.get_device_info_by_index(i)
            name = dev.get("name", "?")
            inp = int(dev.get("maxInputChannels", 0))
            out = int(dev.get("maxOutputChannels", 0))
            tags = []
            if inp > 0:
                tags.append(colored(f"输入×{inp}", Colors.GREEN))
            if out > 0:
                tags.append(colored(f"输出×{out}", Colors.CYAN))
            tag_str = " / ".join(tags) if tags else "—"
            marker = ""
            if i == default_in.get("index"):
                marker = colored(" ← 默认输入", Colors.YELLOW)
            if i == default_out.get("index"):
                marker += colored(" ← 默认输出", Colors.YELLOW)
            print(f"  [{i}] {name}  [{tag_str}]{marker}")
        audio.terminate()

    def _list_devices(self) -> None:
        if self.audio is None:
            return
        count = self.audio.get_device_count()
        if count == 0:
            print(warning("[音频] 未检测到任何音频设备！"))
            return

        print(info(f"[音频] 共检测到 {count} 个设备:"))
        for i in range(count):
            dev = self.audio.get_device_info_by_index(i)
            name = dev.get("name", "?")
            inp = int(dev.get("maxInputChannels", 0))
            out = int(dev.get("maxOutputChannels", 0))
            tags = []
            if inp > 0:
                tags.append(colored("输入", Colors.GREEN))
            if out > 0:
                tags.append(colored("输出", Colors.CYAN))
            tag_str = " / ".join(tags) if tags else "—"
            print(f"  [{i}] {name}  [{tag_str}]")

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
