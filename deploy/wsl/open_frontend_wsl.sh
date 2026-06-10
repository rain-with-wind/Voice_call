#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

URL="${1:-http://127.0.0.1:8100/}"
BACKEND_HOST="${PUBLIC_VOICE_BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${PUBLIC_VOICE_BACKEND_PORT:-8100}"
BACKEND_LOG="/tmp/voice_call_frontend_backend.log"

launch_background() {
    local log_file="$1"
    shift

    nohup "$@" >"$log_file" 2>&1 &
    local pid=$!
    sleep 5

    if kill -0 "$pid" 2>/dev/null; then
        return 0
    fi

    return 1
}

ensure_backend() {
    if curl -fsS "$URL" >/dev/null 2>&1; then
        return
    fi

    . .venv-backend/bin/activate
    nohup bash deploy/public/run_backend_wsl.sh >"$BACKEND_LOG" 2>&1 &

    for _ in $(seq 1 20); do
        if curl -fsS "http://${BACKEND_HOST}:${BACKEND_PORT}/" >/dev/null 2>&1; then
            return
        fi
        sleep 1
    done

    echo "Backend did not become ready. Check $BACKEND_LOG" >&2
    exit 1
}

open_with_falkon() {
    if ! command -v falkon >/dev/null 2>&1; then
        return 1
    fi

    export LIBGL_ALWAYS_SOFTWARE=1
    export QTWEBENGINE_DISABLE_SANDBOX=1
    export QTWEBENGINE_CHROMIUM_FLAGS="--no-sandbox --disable-gpu --disable-gpu-compositing --use-gl=swiftshader --disable-features=UseSkiaRenderer,Vulkan"

    launch_background /tmp/falkon-wsl-browser.log falkon "$URL"
}

open_with_edge() {
    if ! command -v microsoft-edge-stable >/dev/null 2>&1; then
        return 1
    fi

    if launch_background \
        /tmp/edge-wsl-browser.log \
        env \
        XDG_SESSION_TYPE=wayland \
        microsoft-edge-stable \
        --no-first-run \
        --user-data-dir=/tmp/edge-wsl-safe-profile \
        --enable-features=UseOzonePlatform \
        --ozone-platform=wayland \
        --disable-gpu \
        --disable-gpu-compositing \
        --disable-software-rasterizer \
        --disable-features=UseSkiaRenderer,Vulkan,VaapiVideoDecoder \
        --use-gl=swiftshader \
        --in-process-gpu \
        "$URL"; then
        return 0
    fi

    launch_background \
        /tmp/edge-wsl-browser-x11.log \
        microsoft-edge-stable \
        --no-first-run \
        --user-data-dir=/tmp/edge-wsl-safe-profile \
        --disable-gpu \
        --disable-gpu-compositing \
        --disable-software-rasterizer \
        --disable-features=UseSkiaRenderer,Vulkan,VaapiVideoDecoder \
        --use-gl=swiftshader \
        --in-process-gpu \
        "$URL"
}

open_with_epiphany() {
    if ! command -v epiphany-browser >/dev/null 2>&1; then
        return 1
    fi

    export LIBGL_ALWAYS_SOFTWARE=1
    export GSK_RENDERER=cairo
    export WEBKIT_DISABLE_COMPOSITING_MODE=1
    export WEBKIT_DISABLE_DMABUF_RENDERER=1

    launch_background /tmp/epiphany-wsl-browser.log epiphany-browser "$URL"
}

open_with_netsurf() {
    if ! command -v netsurf-gtk >/dev/null 2>&1; then
        return 1
    fi

    launch_background /tmp/netsurf-wsl-browser.log netsurf-gtk "$URL"
}

if [[ -z "${DISPLAY:-}" && -z "${WAYLAND_DISPLAY:-}" ]]; then
    echo "No GUI display detected in WSL. Make sure WSLg is enabled." >&2
    exit 1
fi

ensure_backend

if open_with_edge; then
    echo "Opened frontend with Microsoft Edge (Linux): $URL"
    exit 0
fi

if open_with_falkon; then
    echo "Opened frontend with Falkon: $URL"
    exit 0
fi

if open_with_epiphany; then
    echo "Opened frontend with Epiphany: $URL"
    exit 0
fi

if open_with_netsurf; then
    echo "Opened frontend with NetSurf: $URL"
    exit 0
fi

echo "No supported Linux GUI browser found in WSL." >&2
echo "Install one of: microsoft-edge-stable, falkon, epiphany-browser, netsurf-gtk" >&2
exit 1
