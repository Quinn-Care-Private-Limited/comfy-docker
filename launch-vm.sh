#!/usr/bin/env bash
gcloud compute instances create $1 \
  --project=ai-rnd-431419 \
  --zone=us-central1-a \
  --machine-type=g2-standard-4 \
  --network-interface=network-tier=PREMIUM,stack-type=IPV4_ONLY,subnet=default \
  --maintenance-policy=TERMINATE \
  --provisioning-model=SPOT \
  --accelerator=count=1,type=nvidia-l4 \
  --tags=http-server,https-server \
  --create-disk=auto-delete=yes,boot=yes,device-name=$1,image=projects/cos-cloud/global/images/cos-105-17412-535-63,mode=rw,size=30,type=pd-balanced \
  --metadata-from-file user-data=cloud-config.yaml