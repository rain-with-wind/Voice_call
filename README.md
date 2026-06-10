# Voice Call CLI

`Voice Call CLI` is a WSL/Linux-friendly voice room project built around a
simple TCP audio engine plus a public coordination backend.

It supports:

- direct client/server voice calls over TCP
- public room registration and discovery through a Flask backend
- a lightweight browser frontend for room creation and voice-call visualization
- frontend-generated device tokens for stable room identity reuse
- deployment and smoke-test scripts for WSL and Linux virtual machines

## Documentation

- [Project Report](./docs/PROJECT_REPORT.md)
- [API Reference](./docs/API.md)
- [Deployment Guide](./docs/DEPLOYMENT.md)
- [Doxygen Comment Guide](./docs/DOXYGEN.md)
- [Contributing Guide](./CONTRIBUTING.md)
- [Security Policy](./SECURITY.md)
- [Code of Conduct](./CODE_OF_CONDUCT.md)
- [License](./LICENSE)

## Features

- Real-time duplex voice transport over TCP
- Public room registration, lookup, refresh, and close APIs
- Browser-based room management panel
- Backward-compatible CLI entrypoint: `python voice_call.py ...`
- WSL smoke-test scripts for both audio mode and backend mode

## Project Structure

```text
Voice_call_cli/
├── deploy/
│   ├── public/
│   └── wsl/
├── docs/
│   ├── API.md
│   ├── DEPLOYMENT.md
│   ├── DOXYGEN.md
│   └── PROJECT_REPORT.md
├── public_backend/
│   ├── app/
│   ├── frontend/
│   ├── run.py
│   └── wsgi.py
├── voice_call_cli/
│   ├── backend_client/
│   ├── cli.py
│   ├── config.py
│   ├── console.py
│   ├── engine.py
│   ├── public_commands.py
│   └── stats.py
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── LICENSE
├── README.md
├── SECURITY.md
├── requirements-backend.txt
├── requirements.txt
└── voice_call.py
```

## Quick Start

### 1. Install WSL/Linux system dependencies

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip portaudio19-dev
```

### 2. Prepare the audio CLI environment

```bash
cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_cli
bash deploy/wsl/setup_wsl.sh
```

### 3. Prepare the public backend environment

```bash
cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_cli
bash deploy/public/setup_backend_wsl.sh
```

### 4. Optional: install a native WSL GUI browser

If you want to open the frontend from a Linux GUI browser inside WSL rather
than reusing the Windows browser:

```bash
wsl -u root bash /mnt/d/QQ/Downloads/Voice_call/Voice_call_cli/deploy/wsl/install_gui_browser.sh
```

## Usage

### Direct TCP mode

Start a server:

```bash
python3 voice_call.py --mode server --port 5000
```

Start a client:

```bash
python3 voice_call.py --mode client --host 192.168.43.62 --port 5000
```

### Public room mode

Run the public backend:

```bash
bash deploy/public/run_backend_wsl.sh
```

Create a room from the host side:

```bash
python3 voice_call.py host-public \
  --backend-url https://voice.example.com \
  --room-name demo-room \
  --public-host call.example.com \
  --port 5000
```

Join a room by room code:

```bash
python3 voice_call.py join-public \
  --backend-url https://voice.example.com \
  --room-code ABC123
```

List active rooms:

```bash
python3 voice_call.py list-rooms --backend-url https://voice.example.com
```

Check backend availability:

```bash
python3 voice_call.py backend-health --backend-url https://voice.example.com
```

Collect local device identity information:

```bash
python3 voice_call.py device-info --json
```

## Web Console

Once the backend is running, open:

- `http://127.0.0.1:8100/` for local WSL testing
- `https://voice.example.com/` for public deployment

The frontend keeps only core operations:

- create room
- join room by room code
- see active members in the room
- view room state for voice-call coordination
- close current room

Identity behavior:

- the frontend generates a stable device token on first visit
- repeated joins from the same browser/device reuse the same room identity
- different device tokens are treated as different members, even behind the same IP

To open the frontend with a native WSL GUI browser:

```bash
bash deploy/wsl/open_frontend_wsl.sh
```

The launcher prefers `Microsoft Edge (Linux)` with safe software-rendering
flags on WSL, then falls back to other installed Linux browsers.

## Verification

Compile Python sources:

```bash
python3 -m compileall voice_call.py voice_call_cli public_backend
```

Run audio smoke test:

```bash
bash deploy/wsl/smoke_test.sh
```

Run backend smoke test:

```bash
bash deploy/public/smoke_test_backend.sh
```

## Deployment Notes

For a public Linux or WSL deployment:

1. run the backend with `gunicorn public_backend.wsgi:app`
2. place `nginx` or another reverse proxy in front of the backend
3. configure DNS for the public backend domain
4. expose the backend port and the audio server port in firewall rules
5. ensure the room host domain and audio port are reachable by clients

Reference files:

- `deploy/public/backend.service`
- `deploy/public/nginx.conf`

## License

This project is released under the [MIT License](./LICENSE).

## Repository Address

This workspace can now be prepared as a standard git repository, but a public
remote URL cannot be generated locally. After pushing to GitHub, Gitee, or
another hosting platform, record that remote URL in your submission materials.
