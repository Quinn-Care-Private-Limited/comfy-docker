### Use Nvidia CUDA base image
FROM nvidia/cuda:12.6.2-cudnn-runtime-ubuntu22.04 AS base

### Prevents prompts from packages asking for user input during installation
ENV DEBIAN_FRONTEND=noninteractive \
    ### Prefer binary wheels over source distributions for faster pip installations
    PIP_PREFER_BINARY=1 \
    ### Ensures output from python is printed immediately to the terminal without buffering
    PYTHONUNBUFFERED=1 

### Install Python, git and other necessary tools
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3.10 \
    wget \
    git \
    ### Install libs used for exporting mp4, for nodes like animatediff. can be removed if not required.
    ffmpeg \
    libpng-dev \
    libjpeg-dev \
    libgl1-mesa-glx 

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
# ADD volume/extra_model_paths.yaml ./

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

RUN pip3 install huggingface-hub==0.25.2 onnxruntime

### Go back to the root
WORKDIR /

### Add the src directory
ADD src/ ./

### Install each of the defined requirements then make start.sh file executable
RUN pip3 install --no-cache-dir -r requirements.txt && chmod +x /start.sh

# Clean up after pip installs
RUN pip3 cache purge

### Start the container
CMD /start.sh
# because 69 :*