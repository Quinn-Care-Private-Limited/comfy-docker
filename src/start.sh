#!/usr/bin/env bash
set -eo pipefail


echo "worker-comfy: Starting ComfyUI"
python3 /comfyui/main.py --listen --port $COMFY_PORT --input-directory /comfyui/data --output-directory /comfyui/data --disable-auto-launch --disable-metadata &

echo "worker-comfy: Starting Handler"
python3 -u /app/main.py

# Exit immediately when one of the background processes terminate.
wait -n