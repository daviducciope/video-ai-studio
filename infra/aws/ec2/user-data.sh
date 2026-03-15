#!/usr/bin/env bash
set -euo pipefail

# TEMPLATE ONLY.
# Non eseguito in questo step. Pensato per lo step successivo con render remoto reale.

apt-get update
apt-get install -y python3 python3-venv ffmpeg git curl

echo "Template bootstrap completato. Integrare ComfyUI/runner nello step successivo."
