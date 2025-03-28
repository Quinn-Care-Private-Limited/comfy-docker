### Use Nvidia CUDA base image
FROM nvidia/cuda:12.6.2-cudnn-runtime-ubuntu22.04 AS base

USER root

### Prevents prompts from packages asking for user input during installation
ENV DEBIAN_FRONTEND=noninteractive \
    ### Prefer binary wheels over source distributions for faster pip installations
    PIP_PREFER_BINARY=1 \
    ### Ensures output from python is printed immediately to the terminal without buffering
    PYTHONUNBUFFERED=1 

ENV PORT=80
ENV DATA_PATH=/comfyui/data
ENV MODELS_PATH=/comfyui/models
ENV EXTRA_MODELS_PATH=/comfyui/extra_models


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
# RUN git checkout 723847f6b3d5da21e5d712bc0139fb7197ba60a4

### Add /custom folder - this includes the installer script and any manually added custom nodes/models
ADD custom/custom-files.json ./
ADD custom/custom-file-installer.py ./

RUN pip3 install --upgrade pip

RUN pip3 install torch==2.4.1 torchvision==0.19.1 torchaudio==2.4.1 --index-url https://download.pytorch.org/whl/cu124

### Install ComfyUI dependencies
RUN pip3 install -r requirements.txt 

### install each of the custom models/nodes etc within custom-files.json
RUN python3 custom-file-installer.py 

### Check for custom nodes 'requirements.txt' files and then run install
RUN for dir in /comfyui/custom_nodes/*/; do \
    if [ -f "$dir/requirements.txt" ]; then \
    pip3 install --no-cache-dir -r "$dir/requirements.txt"; \
    fi; \
    done

RUN pip3 install huggingface-hub onnxruntime diffusers sageattention==1.0.6 triton==3.1.0
RUN mkdir -p /comfyui/data
RUN mkdir -p /comfyui/extra_models/loras

### Go back to the root
WORKDIR /app

### Add the src directory
ADD src/requirements.txt ./

### Install each of the defined requirements then make start.sh file executable
RUN pip3 install --no-cache-dir -r requirements.txt

# Clean up after pip installs
RUN pip3 cache purge

ADD custom/extra_model_paths.yaml /comfyui/
ADD src/ ./
RUN chmod +x start.sh

ENV GOOGLE_APPLICATION_CREDENTIALS=/gcp.json

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/app/start.sh"]