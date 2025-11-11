#!/usr/bin/env bash
set -eo pipefail

# mount file store if fs ip is set
if [ -n "$FS_SHARE" ]; then
  echo "Mounting Cloud Filestore."

  if [ "$CLOUD_TYPE" = "AWS" ]; then
      mount -t nfs4 -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport $FS_SHARE$DATA_PATH $FS_PATH$DATA_PATH
      mount -t nfs4 -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport $FS_SHARE$MODELS_PATH $FS_PATH$MODELS_PATH
  fi

  if [ "$CLOUD_TYPE" = "GCP" ]; then
      mount -o nolock $FS_SHARE$DATA_PATH $FS_PATH$DATA_PATH
      mount -o nolock $FS_SHARE$MODELS_PATH $FS_PATH$MODELS_PATH
  fi
  echo "Mounting completed."
fi

yq e '.comfyui.base_path = strenv(FS_PATH) + strenv(MODELS_PATH)' -i /comfyui/extra_model_paths.yaml

echo "worker-comfy: Starting ComfyUI"
python3 /comfyui/main.py --listen --port $COMFY_PORT --input-directory $FS_PATH$DATA_PATH --output-directory $FS_PATH$DATA_PATH --disable-auto-launch --disable-metadata &

echo "worker-comfy: Starting Handler"
python3 -u /app/main.py

# Exit immediately when one of the background processes terminate.
wait -n