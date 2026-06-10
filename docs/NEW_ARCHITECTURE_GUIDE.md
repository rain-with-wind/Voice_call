# New Architecture Guide

## Scope

This guide documents the current recommended architecture for this workspace.

Use only:

- `D:\QQ\Downloads\Voice_call\Voice_call_cli_new_architecture`

Do not use as the main path anymore:

- `D:\QQ\Downloads\Voice_call\Voice_call`
- `D:\QQ\Downloads\Voice_call\Voice_call_terminal`
- `D:\QQ\Downloads\Voice_call\Voice_call_cli`

Those folders may still exist, but this package is the current curated runtime
set for the CLI-only architecture.

## Architecture Summary

The new architecture has three runtime roles:

1. Public backend
   - Runs on the host machine locally.
   - Is exposed to the internet through `ngrok`.
   - Handles room APIs, room state, and WebSocket voice relay.
2. Host client
   - Uses the CLI to create a room and start talking.
   - Connects to the public backend through the `ngrok` URL.
3. Join client
   - Uses the CLI to join a room by room code and start talking.
   - Connects to the same public backend through the `ngrok` URL.

The old browser frontend has been removed from this package.

## High-Level Flow

1. Host machine starts the backend locally on port `8100`.
2. Host machine exposes port `8100` with `ngrok http 8100`.
3. Host machine gets a public URL such as `https://xxxx.ngrok-free.app`.
4. Host machine runs `host-public` with that public backend URL.
5. Join machine runs `join-public` with the same backend URL and the room code.
6. Both CLI clients send and receive voice through the backend WebSocket relay.

## Key Files

### Entrypoint and CLI

- `voice_call.py`
  - Project entrypoint.
  - Delegates all command parsing to `voice_call_cli.cli`.

- `voice_call_cli/cli.py`
  - Defines all supported commands.
  - Important commands:
    - `host-public`
    - `join-public`
    - `list-rooms`
    - `backend-health`
    - `device-info`
    - legacy `--mode server/client`

- `voice_call_cli/public_commands.py`
  - Implements public room workflows.
  - `host-public` registers a room and starts host-side voice streaming.
  - `join-public` looks up a room and joins voice streaming.

### Voice Engine

- `voice_call_cli/ws_engine.py`
  - WebSocket-based audio engine.
  - Captures microphone audio with `PyAudio`.
  - Sends and receives binary audio frames over WebSocket.

- `voice_call_cli/config.py`
  - Audio transport configuration defaults such as port, chunk, rate, and channels.

- `voice_call_cli/stats.py`
  - Call statistics and status display support.

- `voice_call_cli/console.py`
  - Terminal output helpers.

### Backend

- `public_backend/wsgi.py`
  - WSGI entrypoint for production serving.

- `public_backend/run.py`
  - Direct backend startup file for local development.

- `public_backend/app/__init__.py`
  - Flask application factory.
  - Registers HTTP routes and WebSocket routes.
  - Root path now returns a minimal JSON payload for CLI-first deployments.

- `public_backend/app/routes/health.py`
  - Health check endpoint.

- `public_backend/app/routes/rooms.py`
  - Room creation, lookup, join, heartbeat, leave, close, and room-state APIs.

- `public_backend/app/routes/voice.py`
  - WebSocket relay endpoint:
    - `/api/voice/ws/<room_code>/<role>`

- `public_backend/app/room_registry.py`
  - In-memory room and participant lifecycle management.

- `public_backend/app/config.py`
  - Backend host, port, TTL, and other service settings.

- `public_backend/app/database.py`
  - Backend persistence support used by the public backend.

### Environment and Startup Scripts

- `requirements.txt`
  - CLI-side dependencies:
    - `pyaudio`
    - `websocket-client`

- `requirements-backend.txt`
  - Backend-side dependencies:
    - `Flask`
    - `flask-sock`
    - `gunicorn`

- `deploy/wsl/setup_wsl.sh`
  - Creates `.venv` and installs CLI dependencies.

- `deploy/public/setup_backend_wsl.sh`
  - Creates `.venv-backend` and installs backend dependencies.

- `deploy/public/run_backend_wsl.sh`
  - Starts the backend with Gunicorn on port `8100` by default.

- `deploy/public/nginx.conf`
  - Optional reverse proxy example for a real server deployment.

- `deploy/public/backend.service`
  - Optional systemd service example for a real server deployment.

## Commands Overview

### Backend Commands

- Start backend locally:

```bash
python3 public_backend/run.py
```

- Start backend through the packaged WSL script:

```bash
bash deploy/public/run_backend_wsl.sh
```

- Check backend health:

```bash
python3 voice_call.py backend-health --backend-url https://your-backend-url
```

### Room and Call Commands

- Create room and start host-side talking:

```bash
python3 voice_call.py host-public --backend-url https://your-backend-url --room-name demo-room
```

- Join room and start talking:

```bash
python3 voice_call.py join-public --backend-url https://your-backend-url --room-code ABC123
```

- List rooms:

```bash
python3 voice_call.py list-rooms --backend-url https://your-backend-url
```

- Print local device information:

```bash
python3 voice_call.py device-info --json
```

### Legacy Direct Mode

These commands still exist, but they are not the preferred architecture now.

- Host:

```bash
python3 voice_call.py --mode server --port 5000
```

- Join:

```bash
python3 voice_call.py --mode client --host 1.2.3.4 --port 5000
```

## Recommended Usage

Use this sequence:

1. Prepare backend environment on the host machine.
2. Prepare CLI environment on both machines.
3. Start the backend on the host machine.
4. Expose the backend with `ngrok`.
5. Run `host-public` on the host machine.
6. Run `join-public` on the join machine.

## Windows + WSL Setup

### One-Time Preparation on the Host Machine

#### Line-by-Line Input

Open PowerShell and run:

```powershell
wsl bash -lc "cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_cli_new_architecture && bash deploy/public/setup_backend_wsl.sh"
```

```powershell
wsl bash -lc "cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_cli_new_architecture && bash deploy/wsl/setup_wsl.sh"
```

If `ngrok` is installed but not initialized, run:

```powershell
ngrok config add-authtoken YOUR_NGROK_TOKEN
```

#### Batch-Style Version

Copy and run these one by one in the same PowerShell window:

```powershell
wsl bash -lc "cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_cli_new_architecture && bash deploy/public/setup_backend_wsl.sh"
wsl bash -lc "cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_cli_new_architecture && bash deploy/wsl/setup_wsl.sh"
ngrok config add-authtoken YOUR_NGROK_TOKEN
```

### One-Time Preparation on the Join Machine

#### Line-by-Line Input

```powershell
wsl bash -lc "cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_cli_new_architecture && bash deploy/wsl/setup_wsl.sh"
```

#### Batch-Style Version

```powershell
wsl bash -lc "cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_cli_new_architecture && bash deploy/wsl/setup_wsl.sh"
```

## Host Machine Runtime

The host machine needs three running terminals:

- backend terminal
- ngrok terminal
- host call terminal

### Method A: Line-by-Line Input

#### Terminal 1: start the backend

```powershell
wsl
cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_cli_new_architecture
bash deploy/public/run_backend_wsl.sh
```

#### Terminal 2: expose the backend with ngrok

```powershell
ngrok http 8100
```

After this command starts, note the public URL:

- Example: `https://xxxx.ngrok-free.app`

This document refers to that as `BACKEND_URL`.

#### Terminal 3: create the room and start talking

```powershell
wsl
cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_cli_new_architecture
source .venv/bin/activate
python3 voice_call.py host-public --backend-url https://xxxx.ngrok-free.app --room-name demo-room
```

The CLI will print a room code such as `ABC123`.
Send both of these to the other person:

- `BACKEND_URL`
- `ROOM_CODE`

### Method B: Batch-Style Commands

#### Terminal 1

```powershell
wsl bash -lc "cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_cli_new_architecture && bash deploy/public/run_backend_wsl.sh"
```

#### Terminal 2

```powershell
ngrok http 8100
```

#### Terminal 3

```powershell
wsl bash -lc "cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_cli_new_architecture && . .venv/bin/activate && python3 voice_call.py host-public --backend-url https://xxxx.ngrok-free.app --room-name demo-room"
```

## Join Machine Runtime

### Method A: Line-by-Line Input

```powershell
wsl
cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_cli_new_architecture
source .venv/bin/activate
python3 voice_call.py join-public --backend-url https://xxxx.ngrok-free.app --room-code ABC123
```

### Method B: Batch-Style Command

```powershell
wsl bash -lc "cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_cli_new_architecture && . .venv/bin/activate && python3 voice_call.py join-public --backend-url https://xxxx.ngrok-free.app --room-code ABC123"
```

## Helpful Auxiliary Commands

### Check backend health

#### Line-by-Line Input

```powershell
wsl
cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_cli_new_architecture
source .venv/bin/activate
python3 voice_call.py backend-health --backend-url https://xxxx.ngrok-free.app
```

#### Batch-Style Command

```powershell
wsl bash -lc "cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_cli_new_architecture && . .venv/bin/activate && python3 voice_call.py backend-health --backend-url https://xxxx.ngrok-free.app"
```

### List rooms

#### Line-by-Line Input

```powershell
wsl
cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_cli_new_architecture
source .venv/bin/activate
python3 voice_call.py list-rooms --backend-url https://xxxx.ngrok-free.app
```

#### Batch-Style Command

```powershell
wsl bash -lc "cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_cli_new_architecture && . .venv/bin/activate && python3 voice_call.py list-rooms --backend-url https://xxxx.ngrok-free.app"
```

### Show local device info

#### Line-by-Line Input

```powershell
wsl
cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_cli_new_architecture
source .venv/bin/activate
python3 voice_call.py device-info --json
```

#### Batch-Style Command

```powershell
wsl bash -lc "cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_cli_new_architecture && . .venv/bin/activate && python3 voice_call.py device-info --json"
```

## Operational Notes

- Keep the backend terminal running.
- Keep the `ngrok` terminal running.
- Keep the host `host-public` terminal running.
- If `ngrok` restarts, the public URL may change.
- If the public URL changes, all later commands must use the new URL.
- The join side does not need to run a backend.
- This package is CLI-only.

## Troubleshooting

### Room can be created but the other side cannot talk

Check:

- the backend is still running
- `ngrok` is still running
- the host `host-public` process is still running
- both machines are using the same `BACKEND_URL`
- the join side is using the correct `ROOM_CODE`

### `ngrok` command is not found

Use the full Windows path to `ngrok.exe`, for example:

```powershell
& "C:\path\to\ngrok.exe" http 8100
```

### Python audio errors

Check the CLI environment again:

```powershell
wsl bash -lc "cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_cli_new_architecture && bash deploy/wsl/setup_wsl.sh"
```

### Backend dependency errors

Rebuild the backend virtual environment:

```powershell
wsl bash -lc "cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_cli_new_architecture && bash deploy/public/setup_backend_wsl.sh"
```

## Minimal Quick Reference

### Host

```powershell
wsl bash -lc "cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_cli_new_architecture && bash deploy/public/run_backend_wsl.sh"
```

```powershell
ngrok http 8100
```

```powershell
wsl bash -lc "cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_cli_new_architecture && . .venv/bin/activate && python3 voice_call.py host-public --backend-url https://xxxx.ngrok-free.app --room-name demo-room"
```

### Join

```powershell
wsl bash -lc "cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_cli_new_architecture && . .venv/bin/activate && python3 voice_call.py join-public --backend-url https://xxxx.ngrok-free.app --room-code ABC123"
```
