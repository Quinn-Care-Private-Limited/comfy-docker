#!/usr/bin/env bash
set -eo pipefail

# mount file store if fs ip is set
echo "Mounting Cloud Filestore."
# if Cloud storage type is S3
if [ "$CLOUD_STORAGE_TYPE" = "S3" ]; then
  if [ -n "$DATA_FS_SHARE" ]; then
    mount -t nfs4 -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport $DATA_FS_SHARE $DATA_PATH
  fi
  if [ -n "$MODELS_FS_SHARE" ]; then
    mount -t nfs4 -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport $MODELS_FS_SHARE $MODELS_PATH
  fi
  if [ -n "$EXTRA_LORAS_FS_SHARE" ]; then
    mount -t nfs4 -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport $EXTRA_LORAS_FS_SHARE $EXTRA_LORAS_PATH
  fi
fi

# if Cloud storage type is GCS
if [ "$CLOUD_STORAGE_TYPE" = "GCS" ]; then
  if [ -n "$DATA_FS_SHARE" ]; then
    mount -o nolock $DATA_FS_SHARE $DATA_PATH
  fi
  if [ -n "$MODELS_FS_SHARE" ]; then
    mount -o nolock $MODELS_FS_SHARE $DATA_PATH
  fi
  if [ -n "$EXTRA_LORAS_FS_SHARE" ]; then
    mount -o nolock $EXTRA_LORAS_FS_SHARE $DATA_PATH
  fi
fi

# Use libtcmalloc for better memory management
TCMALLOC="$(ldconfig -p | grep -Po "libtcmalloc.so.\d" | head -n 1)"
export LD_PRELOAD="${TCMALLOC}"


echo "worker-comfy: Starting ComfyUI"
python3 /comfyui/main.py --input-directory /comfyui/data --output-directory /comfyui/data --disable-auto-launch --disable-metadata &

echo "worker-comfy: Starting Handler"
python3 -u /app/main.py

# Exit immediately when one of the background processes terminate.
wait -n