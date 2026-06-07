"""@file cli.py
@brief Command-line argument parsing for audio calls and public room workflows.
"""

import argparse
import signal
import sys

from .config import VoiceCallConfig
from .console import warning
from .public_commands import describe_backend, host_public_room, join_public_room, print_rooms


def build_parser():
    """@brief Build the top-level CLI parser.

    @return argparse.ArgumentParser Configured parser for all supported
        subcommands.
    """
    parser = argparse.ArgumentParser(
        description="Enhanced command-line voice call tool with public backend support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  Server: python3 voice_call.py --mode server --port 5000\n"
            "  Client: python3 voice_call.py --mode client --host 192.168.1.100 --port 5000\n"
            "  Host public room: python3 voice_call.py host-public --backend-url https://voice.example.com --room-name demo --public-host call.example.com\n"
            "  Join public room: python3 voice_call.py join-public --backend-url https://voice.example.com --room-code ABC123"
        ),
    )

    subparsers = parser.add_subparsers(dest="command")

    host_parser = subparsers.add_parser("host-public", help="Register a public room on the backend and start the audio server")
    host_parser.add_argument("--backend-url", required=True, help="Public backend base URL, for example https://voice.example.com")
    host_parser.add_argument("--room-name", required=True, help="Display name of the room")
    host_parser.add_argument("--public-host", help="Public domain clients should connect to")
    host_parser.add_argument("--bind-host", default="0.0.0.0", help="Local bind host for the audio server")
    host_parser.add_argument("--owner-name", default="", help="Owner display name")
    host_parser.add_argument("--notes", default="", help="Optional room notes")
    _add_audio_args(host_parser)

    join_parser = subparsers.add_parser("join-public", help="Look up a room from the backend and connect by domain")
    join_parser.add_argument("--backend-url", required=True, help="Public backend base URL")
    join_parser.add_argument("--room-code", required=True, help="Room code returned by the backend")
    _add_audio_args(join_parser)

    list_parser = subparsers.add_parser("list-rooms", help="List active public rooms on the backend")
    list_parser.add_argument("--backend-url", required=True, help="Public backend base URL")

    health_parser = subparsers.add_parser("backend-health", help="Check whether the public backend is reachable")
    health_parser.add_argument("--backend-url", required=True, help="Public backend base URL")

    return parser


def main():
    """@brief Run the command-line entrypoint.

    The function dispatches either the legacy direct TCP mode or the newer
    public-backend subcommands.

    @return None
    """
    if "--mode" in sys.argv[1:]:
        return _run_legacy_mode()

    parser = build_parser()
    args = parser.parse_args()

    if args.command == "host-public":
        host_public_room(args)
        return
    if args.command == "join-public":
        join_public_room(args)
        return
    if args.command == "list-rooms":
        print_rooms(args.backend_url)
        return
    if args.command == "backend-health":
        describe_backend(args.backend_url)
        return

    parser.print_help()


def _run_legacy_mode():
    """@brief Preserve compatibility with the original direct TCP interface.

    @return None
    """
    parser = argparse.ArgumentParser(description="Legacy direct TCP mode")
    parser.add_argument("--mode", type=str, choices=["server", "client"], required=True, help="Run mode")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Server host in client mode")
    _add_audio_args(parser)
    args = parser.parse_args()

    config = VoiceCallConfig(
        host="0.0.0.0",
        port=args.port,
        chunk=args.chunk,
        rate=args.rate,
        channels=args.channels,
    )
    from .engine import VoiceCall

    call = VoiceCall(config)

    def signal_handler(_signum, _frame):
        print(warning("\n\n[!] Stopping call..."))
        call.stop()

    signal.signal(signal.SIGINT, signal_handler)

    if args.mode == "server":
        call.start_server()
    else:
        call.connect_to_server(args.host)


def _add_audio_args(parser):
    """@brief Add shared audio transport arguments to a parser.

    @param parser Target parser or sub-parser instance.
    @return None
    """
    parser.add_argument("--port", type=int, default=5000, help="Server port")
    parser.add_argument("--chunk", type=int, default=1024, help="Audio frame buffer size")
    parser.add_argument("--rate", type=int, default=44100, help="Sample rate")
    parser.add_argument("--channels", type=int, default=2, help="Audio channel count")
