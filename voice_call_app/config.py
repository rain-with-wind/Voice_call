"""Configuration values shared by the voice call runtime."""

from dataclasses import dataclass


@dataclass(slots=True)
class VoiceCallConfig:
    host: str = "0.0.0.0"
    port: int = 5000
    chunk: int = 1024
    rate: int = 48000
    channels: int = 1
    password: str | None = None
    use_encryption: bool = False
    socket_timeout: float = 0.5
    auth_timeout: float = 10.0
    input_device_index: int | None = None
    output_device_index: int | None = None

    @property
    def frame_size(self) -> int:
        return 2 * self.channels
