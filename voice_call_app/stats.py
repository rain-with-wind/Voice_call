"""Runtime metrics and small presentation helpers."""

from dataclasses import dataclass

from .console import Colors, colored


@dataclass(slots=True)
class CallStats:
    bytes_sent: int = 0
    bytes_received: int = 0
    last_volume: float = 0.0

    def format_volume_bar(self, length: int = 20) -> str:
        filled = int(self.last_volume * length)
        bar = "█" * filled + "░" * (length - filled)

        if self.last_volume < 0.3:
            color = Colors.GREEN
        elif self.last_volume < 0.7:
            color = Colors.YELLOW
        else:
            color = Colors.RED

        return colored(bar, color)
