#!/usr/bin/env bash

# Use libtcmalloc for better memory management
TCMALLOC="$(ldconfig -p | grep -Po "libtcmalloc.so.\d" | head -n 1)"
export LD_PRELOAD="${TCMALLOC}"


echo "worker-comfy: Starting ComfyUI"
python3 /comfyui/main.py --disable-auto-launch --disable-metadata &

echo "worker-comfy: Starting Handler"
python3 -u /main.py