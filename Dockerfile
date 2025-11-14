### Use Nvidia CUDA base image
FROM nvidia/cuda:12.8.1-cudnn-runtime-ubuntu22.04 AS base

USER root

### Prevents prompts from packages asking for user input during installation
ENV DEBIAN_FRONTEND=noninteractive \
    ### Prefer binary wheels over source distributions for faster pip installations
    PIP_PREFER_BINARY=1 \
    ### Ensures output from python is printed immediately to the terminal without buffering
    PYTHONUNBUFFERED=1 

ENV PORT=80
ENV COMFY_PORT=8188
ENV CLOUD_TYPE=RUNPOD

ENV FS_PATH=/volume
ENV HF_HOME=/volume
ENV GOOGLE_APPLICATION_CREDENTIALS=/gcp.json

ENV DATA_PATH=/data
ENV MODELS_PATH=/models

ARG HF_TOKEN
ARG PRESET=flux-krea

RUN mkdir -p $FS_PATH$DATA_PATH
RUN mkdir -p $FS_PATH$MODELS_PATH

### Install Python, git and other necessary tools
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3.10 \
    wget \
    git \
    ffmpeg \
    libpng-dev \
    libjpeg-dev \
    libgl1-mesa-glx \
    tini \
    nfs-common

### Clean up to reduce image size
RUN apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/* 

### Clone ComfyUI repository 
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /comfyui

### Change working directory to ComfyUI
WORKDIR /comfyui

### set comfyui to specific commit id (useful if they update and introduce bugs...)
RUN git checkout 5ebcab3c7d974963a89cecd37296a22fdb73bd2b

RUN pip3 install --upgrade pip

RUN pip3 install torch==2.7.1 torchvision==0.22.1 torchaudio==2.7.1 --index-url https://download.pytorch.org/whl/cu128

### Install ComfyUI dependencies
RUN pip3 install -r requirements.txt 

### Add /custom folder - this includes the installer script and any manually added custom nodes/models
ADD custom/${PRESET}.json ./
ADD custom/custom-file-installer.py ./
ADD custom/extra_model_paths.yaml ./

### install each of the custom models/nodes etc within custom-files.json
RUN python3 -u custom-file-installer.py 

### Check for custom nodes 'requirements.txt' files and then run install
RUN for dir in /comfyui/custom_nodes/*/; do \
    if [ -f "$dir/requirements.txt" ]; then \
    pip3 install --no-cache-dir -r "$dir/requirements.txt"; \
    fi; \
    done

RUN pip3 install huggingface-hub onnxruntime diffusers sageattention triton peft

### Go back to the root
WORKDIR /app

### Add the src directory
ADD src/requirements.txt ./

### Install each of the defined requirements then make start.sh file executable
RUN pip3 install --no-cache-dir -r requirements.txt

# Clean up after pip installs
RUN pip3 cache purge

ADD src/ ./
RUN chmod +x start.sh

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/app/start.sh"]