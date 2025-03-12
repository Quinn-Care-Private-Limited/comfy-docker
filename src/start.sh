#!/usr/bin/env bash
set -eo pipefail

# mount file store if fs ip is set
# if Cloud storage type is S3
if [ -n "$FS_SHARE" ]; then
  echo "Mounting Cloud Filestore."

  if [ "$CLOUD_STORAGE_TYPE" = "S3" ]; then
      mount -t nfs4 -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport $FS_SHARE$DATA_PATH $DATA_PATH
      mount -t nfs4 -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport $FS_SHARE$MODELS_PATH $MODELS_PATH

    if [ -n "$LORAS_PATH" ]; then
      mount -t nfs4 -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport $FS_SHARE$LORAS_PATH $EXTRA_LORAS_PATH
    fi
  fi


  # if Cloud storage type is GCS
  if [ "$CLOUD_STORAGE_TYPE" = "GCS" ]; then
      mount -o nolock $FS_SHARE$DATA_PATH $DATA_PATH
      mount -o nolock $FS_SHARE$MODELS_PATH $MODELS_PATH

    if [ -n "$LORAS_PATH" ]; then
      mount -o nolock $$FS_SHARE$LORAS_PATH $EXTRA_LORAS_PATH
    fi
  fi
  echo "Mounting completed."
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