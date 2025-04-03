#!/usr/bin/env bash
set -eo pipefail

# Use libtcmalloc for better memory management
TCMALLOC="$(ldconfig -p | grep -Po "libtcmalloc.so.\d" | head -n 1)"
export LD_PRELOAD="${TCMALLOC}"

echo "/runpod-volume:"
find /runpod-volume -mindepth 1 -maxdepth 2 -exec ls -d {} \;

echo "worker-comfy: Starting ComfyUI"
python3 /comfyui/main.py --listen --port $COMFY_PORT --input-directory /comfyui/data --output-directory /comfyui/data --disable-auto-launch --disable-metadata &

echo "worker-comfy: Starting Handler"
python3 -u /app/main.py

# Exit immediately when one of the background processes terminate.
wait -n