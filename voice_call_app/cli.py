"""Command-line interface for the refactored direct TCP voice call tool."""

import argparse
import signal

from .config import VoiceCallConfig
from .windows import enable_utf8_console


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Direct TCP voice call tool with optional password auth and encryption.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  Start server:\n"
            "    python3 voice_call.py --mode server --port 5000\n\n"
            "  Join as client:\n"
            "    python3 voice_call.py --mode client --host 192.168.1.100 --port 5000\n\n"
            "  Secure call:\n"
            "    python3 voice_call.py --mode server --port 5000 --encrypt --password mypassword\n"
            "    python3 voice_call.py --mode client --host 192.168.1.100 --port 5000 --encrypt --password mypassword\n"
        ),
    )
    parser.add_argument("--mode", choices=["server", "client"], required=True, help="Run as a listening server or a connecting client.")
    parser.add_argument("--host", default="127.0.0.1", help="Server address when running in client mode.")
    parser.add_argument("--port", type=int, default=5000, help="TCP port used for the call.")
    parser.add_argument("--password", "-p", default=None, help="Optional shared password used for authentication.")
    parser.add_argument("--encrypt", action="store_true", help="Enable Fernet encryption derived from the shared password.")
    parser.add_argument("--rate", type=int, default=48000, help="Audio sample rate.")
    parser.add_argument("--channels", type=int, default=1, help="Number of audio channels.")
    parser.add_argument("--chunk", type=int, default=1024, help="Audio chunk size per socket frame.")
    return parser


def main() -> None:
    enable_utf8_console()
    parser = build_parser()
    args = parser.parse_args()
    from .engine import VoiceCall

    call = VoiceCall(
        VoiceCallConfig(
            host="0.0.0.0",
            port=args.port,
            chunk=args.chunk,
            rate=args.rate,
            channels=args.channels,
            password=args.password,
            use_encryption=args.encrypt,
        )
    )

    def handle_signal(_signum, _frame) -> None:
        print("\n\n[INFO] Stopping call...")
        call.stop()

    signal.signal(signal.SIGINT, handle_signal)

    if args.mode == "server":
        call.start_server()
    else:
        call.connect_to_server(args.host)
