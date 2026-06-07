from dataclasses import dataclass, field
from threading import Lock
import time


@dataclass(slots=True)
class CallStats:
    bytes_sent: int = 0
    bytes_received: int = 0
    last_volume: float = 0.0
    start_time: float | None = None
    _lock: Lock = field(default_factory=Lock, repr=False)

    def mark_started(self):
        with self._lock:
            self.start_time = time.time()

    def add_sent(self, size):
        with self._lock:
            self.bytes_sent += size

    def add_received(self, size):
        with self._lock:
            self.bytes_received += size

    def set_volume(self, volume):
        with self._lock:
            self.last_volume = volume

    def snapshot(self):
        with self._lock:
            duration = 0
            if self.start_time is not None:
                duration = int(time.time() - self.start_time)

            return {
                "bytes_sent": self.bytes_sent,
                "bytes_received": self.bytes_received,
                "last_volume": self.last_volume,
                "duration": duration,
                "started": self.start_time is not None,
            }
