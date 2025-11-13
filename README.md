[![Runpod](https://api.runpod.io/badge/Quinn-Care-Private-Limited/comfy-docker)](https://console.runpod.io/hub/Quinn-Care-Private-Limited/comfy-docker)
# ComfyUI Serverless Worker

A production-ready serverless worker for running ComfyUI workflows on Runpod. This worker supports Flux models, custom nodes, and advanced image generation workflows with real-time progress tracking and Google Cloud Storage (GCS) upload capabilities.

## Features

- 🚀 **Serverless Architecture**: Deploy and scale ComfyUI workflows on Runpod's serverless infrastructure
- 🎨 **Flux Model Support**: Pre-configured presets for Flux Krea and Flux Kontext models
- 📊 **Progress Tracking**: Real-time progress updates via callbacks and Runpod's progress API
- ☁️ **GCS Integration**: Automatic upload of generated images to Google Cloud Storage
- 🔧 **Custom Nodes**: Support for custom ComfyUI nodes and models
- 🔄 **Webhook Support**: Optional webhook callbacks for job status updates
- 📦 **Dockerized**: Fully containerized with CUDA 12.8 support

## Requirements

- Runpod account with serverless access
- GPU with CUDA 12.8 support (RTX A4000, RTX A5000, RTX A6000, RTX 3090, RTX 4090)
- (Optional) Google Cloud Storage credentials for automatic uploads
- (Optional) Hugging Face token for private model access

## Quick Start

### Deploy from Runpod Hub

1. Navigate to the [Runpod Hub](https://www.runpod.io/hub)
2. Search for "ComfyUI Serverless Worker"
3. Click "Deploy" and configure your environment variables
4. Select your preferred preset (Flux Krea or Flux Kontext)
5. Deploy and start generating images!

### Local Development

```bash
# Clone the repository
git clone <your-repo-url>
cd comfy-docker

# Build the Docker image
docker build --build-arg PRESET=flux-krea -t comfyui-worker .

# Run locally (requires Runpod API key)
docker run -e RUNPOD_API_KEY=your_key comfyui-worker
```

## Usage

### Basic Workflow Execution

Send a job to your deployed endpoint with a ComfyUI workflow:

```json
{
  "input": {
    "workflow": {
      "1": {
        "inputs": {
          "text": "A beautiful landscape with mountains",
          "clip": ["2", 0]
        },
        "class_type": "CLIPTextEncode"
      },
      "2": {
        "inputs": {
          "clip_name1": "clip_l.safetensors",
          "clip_name2": "t5xxl_fp8_e4m3fn_scaled.safetensors",
          "type": "flux",
          "device": "default"
        },
        "class_type": "DualCLIPLoader"
      },
      "3": {
        "inputs": {
          "unet_name": "flux1-krea-dev.safetensors",
          "weight_dtype": "default"
        },
        "class_type": "UNETLoader"
      },
      "4": {
        "inputs": {
          "vae_name": "ae.safetensors"
        },
        "class_type": "VAELoader"
      },
      "5": {
        "inputs": {
          "seed": 123456,
          "steps": 20,
          "cfg": 3.5,
          "sampler_name": "euler",
          "scheduler": "normal",
          "denoise": 1.0,
          "model": ["3", 0],
          "positive": ["1", 0],
          "negative": ["1", 0],
          "vae": ["4", 0]
        },
        "class_type": "KSampler"
      },
      "6": {
        "inputs": {
          "filename_prefix": "ComfyUI",
          "images": ["5", 0]
        },
        "class_type": "SaveImage"
      }
    }
  }
}
```

### With Progress Callbacks

```json
{
  "input": {
    "workflow": { /* your workflow */ },
    "callback_url": "https://your-server.com/webhook",
    "callback_auth_header": {
      "x-auth-token": "your-secret-token"
    },
    "metadata": {
      "user_id": "123",
      "job_type": "image_generation"
    }
  }
}
```

### With GCS Upload

```json
{
  "input": {
    "workflow": { /* your workflow */ },
    "upload": {
      "bucket": "your-gcs-bucket",
      "key": "path/to/image.png"
    }
  }
}
```

Or upload to a bucket path:

```json
{
  "input": {
    "workflow": { /* your workflow */ },
    "bucket": "your-bucket/path/to/folder"
  }
}
```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `PRESET` | Preset configuration (flux-krea or flux-kontext) | Yes | flux-krea |
| `HF_TOKEN` | Hugging Face API token for private models | No | - |
| `GCP_CREDENTIALS` | Base64 encoded GCP credentials JSON | No | - |
| `ENV` | Environment mode (development/production) | No | production |
| `CLOUD_TYPE` | Cloud provider (RUNPOD/GCP/AWS) | No | RUNPOD |

### Presets

#### Flux Krea
Optimized for high-quality image generation with the Flux Krea model.

#### Flux Kontext
Configured for context-aware image generation with the Flux Kontext model.

## API Reference

### Job Input Structure

```typescript
{
  input: {
    workflow: object | string,  // ComfyUI workflow JSON or JSON string
    files?: array,               // Optional input files
    callback_url?: string,       // Optional webhook URL
    callback_auth_header?: object, // Optional auth headers for webhook
    metadata?: object,           // Optional metadata
    upload?: {                   // Optional single file upload
      bucket: string,
      key: string
    },
    bucket?: string              // Optional batch upload path
  }
}
```

### Response Structure

**Success:**
```json
{
  "output": [
    {
      "name": "ComfyUI_00001_.png",
      "path": "/volume/data/ComfyUI_00001_.png"
    }
  ]
}
```

**Error:**
```json
{
  "error": "Error message description"
}
```

### Progress Callback Format

```json
{
  "run_id": "job-id",
  "status": "processing" | "completed" | "failed",
  "data": {
    "progress": 0-100,
    "output": [...] // Only on completion
  },
  "metadata": { /* your metadata */ }
}
```

## Examples

Example workflows are available in the `examples/` directory:

- `flux-krea-input.json` - Basic Flux Krea workflow with upscaling
- `flux-kontext-input.json` - Flux Kontext workflow with image context

## Project Structure

```
comfy-docker/
├── .runpod/
│   ├── hub.json          # Runpod Hub configuration
│   └── tests.json        # Test cases for Hub validation
├── custom/
│   ├── flux-krea.json    # Flux Krea preset configuration
│   ├── flux-kontext.json # Flux Kontext preset configuration
│   └── custom-file-installer.py
├── examples/
│   ├── flux-krea-input.json
│   └── flux-kontext-input.json
├── src/
│   ├── handler.py        # Main job handler
│   ├── main.py           # Entry point
│   ├── comftroller.py    # ComfyUI controller
│   ├── utils.py          # Utility functions
│   └── requirements.txt
├── Dockerfile
└── README.md
```

## Development

### Running Tests

The project includes test cases defined in `.runpod/tests.json` that are automatically executed during Hub builds.

### Building Locally

```bash
# Build with Flux Krea preset
docker build --build-arg PRESET=flux-krea -t comfyui-krea .

# Build with Flux Kontext preset
docker build --build-arg PRESET=flux-kontext -t comfyui-kontext .
```

### Adding Custom Models/Nodes

1. Add your custom files to the `custom/` directory
2. Update the preset JSON file (`flux-krea.json` or `flux-kontext.json`) with your custom files
3. Rebuild the Docker image

## Deployment on Runpod Hub

This repository is configured for Runpod Hub publishing:

1. **Required Files** (already included):
   - `.runpod/hub.json` - Hub configuration
   - `.runpod/tests.json` - Test cases
   - `Dockerfile` - Container definition
   - `src/handler.py` - Serverless handler

2. **Publishing Steps**:
   - Create a GitHub release
   - Submit your repo to Runpod Hub
   - Wait for build and test validation
   - Your worker will be available on the Hub!

## Troubleshooting

### Common Issues

**Workflow validation errors:**
- Ensure your workflow JSON is valid
- Check that all referenced nodes are available in your preset

**GCS upload failures:**
- Verify your GCP credentials are correctly base64 encoded
- Ensure the bucket exists and has proper permissions

**Model loading errors:**
- Check that required model files are available
- Verify Hugging Face token if accessing private models

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Support

For issues and questions:
- Open an issue on GitHub
- Check the [Runpod Documentation](https://docs.runpod.io)
- Visit the [ComfyUI GitHub](https://github.com/comfyanonymous/ComfyUI)

