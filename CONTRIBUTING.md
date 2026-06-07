# Contributing

Thanks for your interest in improving `Voice Call CLI`.

## Getting Started

1. Set up the WSL system dependencies:

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip portaudio19-dev
```

2. Set up the audio CLI environment:

```bash
bash deploy/wsl/setup_wsl.sh
```

3. Set up the backend environment:

```bash
bash deploy/public/setup_backend_wsl.sh
```

## Development Guidelines

- Keep changes focused and reviewable.
- Preserve the existing CLI entrypoint when possible.
- Prefer small, testable modules over large single-file changes.
- Document user-facing behavior changes in `README.md`.
- Avoid introducing platform assumptions beyond WSL/Linux unless clearly documented.

## Before Opening a Pull Request

Please run the relevant checks:

```bash
python3 -m compileall voice_call.py voice_call_cli public_backend
bash deploy/wsl/smoke_test.sh
bash deploy/public/smoke_test_backend.sh
```

If your change only affects one area, mention what you did and did not test in the pull request description.

## Pull Request Checklist

- The code builds or runs locally.
- The scope is explained clearly.
- User-facing behavior is documented.
- New commands, flags, or routes are described.
- Breaking changes are called out explicitly.

## Reporting Issues

When filing a bug, please include:

- operating system and WSL version
- Python version
- exact command used
- expected behavior
- actual behavior
- logs or screenshots if available
