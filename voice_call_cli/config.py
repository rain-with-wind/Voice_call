from dataclasses import dataclass


@dataclass(slots=True)
class VoiceCallConfig:
    host: str = "0.0.0.0"
    port: int = 5000
    chunk: int = 1024
    rate: int = 44100
    channels: int = 2
    socket_timeout: float = 0.5
