"""@file public_commands.py
@brief High-level workflows for public room registration and discovery.
"""

import json
import threading

from .backend_client import PublicBackendClient
from .config import VoiceCallConfig
from .console import accent, info, print_banner, success, warning
from .ws_engine import VoiceCallWS


def print_rooms(backend_url):
    """@brief Print the active room list returned by the public backend.

    @param backend_url Base URL of the public coordination backend.
    @return None
    """
    client = PublicBackendClient(backend_url)
    response = client.list_rooms()
    rooms = response.get("rooms", [])

    print_banner("Public Rooms")
    if not rooms:
        print(warning("No active rooms found."))
        return

    for room in rooms:
        print(success(f"[{room['room_code']}] {room['name']}"))
        print(f"  Domain: {room['public_host']}:{room['public_port']}")
        print(f"  Owner: {room['owner_name'] or 'anonymous'}")
        print(f"  Notes: {room['notes'] or '-'}")
        print(f"  Last update: {room['last_heartbeat_at']}")


def describe_backend(backend_url):
    """@brief Print the backend health payload as formatted JSON.

    @param backend_url Base URL of the public coordination backend.
    @return None
    """
    client = PublicBackendClient(backend_url)
    payload = client.health()
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def host_public_room(args):
    """@brief Register a public room and start WebSocket audio.

    @param args Parsed command-line arguments for the `host-public` workflow.
    @return None
    """
    backend = PublicBackendClient(args.backend_url)
    payload = {
        "name": args.room_name,
        "public_host": "relay",
        "public_port": 0,
        "owner_name": args.owner_name or "",
        "notes": args.notes or "",
    }
    room = backend.register_room(payload)

    print_banner("Public Room Registered")
    print(success(f"Room code: {room['room']['room_code']}"))
    print(f"Backend URL: {args.backend_url}")
    print(info("Client can join with: python voice_call.py join-public "
               f"--backend-url {args.backend_url} --room-code {room['room']['room_code']}\n"))

    stop_event = threading.Event()
    heartbeat_thread = threading.Thread(
        target=_heartbeat_loop,
        args=(backend, room["room"]["room_code"], room["manage_token"], room["heartbeat_interval_seconds"], stop_event),
        daemon=True,
    )
    heartbeat_thread.start()

    try:
        call = VoiceCallWS(
            VoiceCallConfig(
                host="0.0.0.0",
                port=args.port,
                chunk=args.chunk,
                rate=args.rate,
                channels=args.channels,
            )
        )
        call.start(args.backend_url, room["room"]["room_code"], "host")
    finally:
        stop_event.set()
        try:
            backend.close_room(room["room"]["room_code"], room["manage_token"])
        except RuntimeError as exc:
            print(warning(f"Room close request failed: {exc}"))


def join_public_room(args):
    """@brief Resolve a public room code and join via WebSocket audio.

    @param args Parsed command-line arguments for the `join-public` workflow.
    @return None
    """
    backend = PublicBackendClient(args.backend_url)
    room_response = backend.get_room(args.room_code)
    room = room_response["room"]

    print_banner("Join Public Room")
    print(f"Room code: {success(room['room_code'])}")
    print(f"Room name: {room['name']}")

    call = VoiceCallWS(
        VoiceCallConfig(
            host="0.0.0.0",
            port=0,
            chunk=args.chunk,
            rate=args.rate,
            channels=args.channels,
        )
    )
    call.start(args.backend_url, room["room_code"], "client")


def _heartbeat_loop(backend, room_code, manage_token, interval_seconds, stop_event):
    """@brief Periodically refresh room availability on the backend.

    @param backend Backend API client instance.
    @param room_code Room code to refresh.
    @param manage_token Secret token used to authorize room maintenance.
    @param interval_seconds Refresh interval in seconds.
    @param stop_event Event used to stop the background loop.
    @return None
    """
    while not stop_event.wait(interval_seconds):
        try:
            backend.heartbeat(room_code, manage_token)
        except RuntimeError as exc:
            print(warning(f"Heartbeat failed: {exc}"))
