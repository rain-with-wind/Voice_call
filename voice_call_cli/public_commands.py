"""@file public_commands.py
@brief High-level workflows for public room registration and discovery.
"""

import json
import socket
import threading

from .backend_client import PublicBackendClient
from .config import VoiceCallConfig
from .console import accent, info, print_banner, success, warning
from .engine import VoiceCall


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
    """@brief Register a public room and start the local audio server.

    @param args Parsed command-line arguments for the `host-public` workflow.
    @return None
    """
    backend = PublicBackendClient(args.backend_url)
    public_host = args.public_host or _guess_public_host()
    payload = {
        "name": args.room_name,
        "public_host": public_host,
        "public_port": args.port,
        "owner_name": args.owner_name,
        "notes": args.notes,
    }
    room = backend.register_room(payload)

    print_banner("Public Room Registered")
    print(success(f"Room code: {room['room']['room_code']}"))
    print(f"Join domain: {room['room']['public_host']}:{room['room']['public_port']}")
    print(f"Backend URL: {args.backend_url}")
    print(info("Clients can either connect directly to the domain or use join-public with the room code.\n"))

    stop_event = threading.Event()
    heartbeat_thread = threading.Thread(
        target=_heartbeat_loop,
        args=(backend, room["room"]["room_code"], room["manage_token"], room["heartbeat_interval_seconds"], stop_event),
        daemon=True,
    )
    heartbeat_thread.start()

    try:
        call = VoiceCall(
            VoiceCallConfig(
                host=args.bind_host,
                port=args.port,
                chunk=args.chunk,
                rate=args.rate,
                channels=args.channels,
            )
        )
        call.start_server()
    finally:
        stop_event.set()
        try:
            backend.close_room(room["room"]["room_code"], room["manage_token"])
        except RuntimeError as exc:
            print(warning(f"Room close request failed: {exc}"))


def join_public_room(args):
    """@brief Resolve a public room code and join its audio endpoint.

    @param args Parsed command-line arguments for the `join-public` workflow.
    @return None
    """
    backend = PublicBackendClient(args.backend_url)
    room_response = backend.get_room(args.room_code)
    room = room_response["room"]
    target = f"{room['public_host']}:{room['public_port']}"

    print_banner("Join Public Room")
    print(f"Room code: {success(room['room_code'])}")
    print(f"Room name: {room['name']}")
    print(f"Connecting to domain: {accent(target)}")

    call = VoiceCall(
        VoiceCallConfig(
            host="0.0.0.0",
            port=room["public_port"],
            chunk=args.chunk,
            rate=args.rate,
            channels=args.channels,
        )
    )
    call.connect_to_server(room["public_host"])


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


def _guess_public_host():
    """@brief Infer a reasonable public host name from the local machine.

    @return str Fully qualified domain name when available, otherwise the local
        hostname.
    """
    hostname = socket.gethostname()
    try:
        return socket.getfqdn(hostname)
    except OSError:
        return hostname
