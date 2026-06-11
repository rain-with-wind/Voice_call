"""Windows-specific terminal helpers."""

import sys


def enable_utf8_console() -> None:
    """Best-effort UTF-8 console setup for native Windows terminals."""
    if sys.platform != "win32":
        return

    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(65001)
        kernel32.SetConsoleCP(65001)
    except Exception:
        # The tool should remain usable even when the console cannot be tuned.
        pass
