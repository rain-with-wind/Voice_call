#!/usr/bin/env bash
set -euo pipefail

if [[ "$(id -u)" -ne 0 ]]; then
    echo "Please run this script as root inside WSL." >&2
    echo "Example: wsl -u root bash /mnt/d/QQ/Downloads/Voice_call/Voice_call_cli/deploy/wsl/install_gui_browser.sh" >&2
    exit 1
fi

install -m 0755 -d /etc/apt/keyrings

if [[ ! -f /etc/apt/keyrings/microsoft.gpg ]]; then
    curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /etc/apt/keyrings/microsoft.gpg
fi

printf '%s\n' \
    'deb [arch=amd64 signed-by=/etc/apt/keyrings/microsoft.gpg] https://packages.microsoft.com/repos/edge stable main' \
    >/etc/apt/sources.list.d/microsoft-edge.list

apt-get update -o Acquire::ForceIPv4=true
DEBIAN_FRONTEND=noninteractive apt-get install -y \
    microsoft-edge-stable \
    falkon \
    epiphany-browser \
    netsurf-gtk \
    xdg-utils

echo "Installed WSL GUI browsers."
echo "Recommended launcher:"
echo "  bash /mnt/d/QQ/Downloads/Voice_call/Voice_call_cli/deploy/wsl/open_frontend_wsl.sh"
