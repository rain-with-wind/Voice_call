# Voice Call CLI New Architecture Pack

## What This Folder Is

This folder is a curated package of the code and documents that are actually
useful for the current recommended architecture.

Source project:

- `D:\QQ\Downloads\Voice_call\Voice_call_cli`

Packaged folder:

- `D:\QQ\Downloads\Voice_call\Voice_call_cli_new_architecture`

## What Was Kept

- CLI entrypoint and command parsing
- WebSocket voice call engine
- Public backend code
- Minimal deployment scripts
- Core docs for API, deployment, and the new architecture

## What Was Intentionally Left Out

- old sibling projects outside `Voice_call_cli`
- virtual environments
- `__pycache__` and `.pyc` files
- unrelated governance files such as code of conduct and contributing docs
- extra smoke-test and GUI-browser helper scripts
- all old frontend assets and frontend-serving backend glue

## Runtime Roles

This pack is centered on three roles:

1. Host backend
   - runs locally on the host machine
   - is exposed to the internet through `ngrok`
2. Host caller
   - creates a room with `host-public`
3. Join caller
   - joins the room with `join-public`

This pack is now CLI-only.
The old browser frontend has been removed.

## Most Important Files

- `voice_call.py`
- `voice_call_cli/cli.py`
- `voice_call_cli/public_commands.py`
- `voice_call_cli/ws_engine.py`
- `public_backend/app/__init__.py`
- `public_backend/app/routes/rooms.py`
- `public_backend/app/routes/voice.py`
- `deploy/public/setup_backend_wsl.sh`
- `deploy/public/run_backend_wsl.sh`
- `deploy/wsl/setup_wsl.sh`
- `docs/NEW_ARCHITECTURE_GUIDE.md`

## Fast Start

### Host machine

Prepare backend dependencies:

```powershell
wsl bash -lc "cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_cli_new_architecture && bash deploy/public/setup_backend_wsl.sh"
```

Prepare CLI dependencies:

```powershell
wsl bash -lc "cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_cli_new_architecture && bash deploy/wsl/setup_wsl.sh"
```

Start the backend:

```powershell
wsl bash -lc "cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_cli_new_architecture && bash deploy/public/run_backend_wsl.sh"
```

Expose it with `ngrok`:

```powershell
ngrok http 8100
```

Create a room:

```powershell
wsl bash -lc "cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_cli_new_architecture && . .venv/bin/activate && python3 voice_call.py host-public --backend-url https://xxxx.ngrok-free.app --room-name demo-room"
```

### Join machine

Prepare CLI dependencies:

```powershell
wsl bash -lc "cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_cli_new_architecture && bash deploy/wsl/setup_wsl.sh"
```

Join the room:

```powershell
wsl bash -lc "cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_cli_new_architecture && . .venv/bin/activate && python3 voice_call.py join-public --backend-url https://xxxx.ngrok-free.app --room-code ABC123"
```

## Documentation

- Architecture and step-by-step commands:
  `docs/NEW_ARCHITECTURE_GUIDE.md`
- Backend API details:
  `docs/API.md`
- Deployment notes:
  `docs/DEPLOYMENT.md`

## Notes

- Keep the backend terminal running.
- Keep the `ngrok` terminal running.
- Keep the host `host-public` terminal running.
- If the `ngrok` URL changes, both sides must switch to the new backend URL.
