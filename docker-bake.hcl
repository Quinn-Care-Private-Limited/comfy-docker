variable "VERSION" {
  default = "1.0.0"
}

variable "REGISTRY" {
  default = "quinninc"
}

variable "IMAGE_NAME" {
  default = "comfy"
}

variable "HF_TOKEN" {
  default = ""
}

variable "CLOUD_TYPE" {
  default = "runpod"
}

variable "CACHE_FROM" {
  default = "1.0.0"
}

group "default" {
  targets = ["flux-krea", "flux-kontext"]
}

target "base" {
  context = "."
  dockerfile = "Dockerfile"
  platforms = ["linux/amd64"]
}

target "flux-krea" {
  inherits = ["base"]
  tags = [
    "${REGISTRY}/${IMAGE_NAME}:${VERSION}-${CLOUD_TYPE}-flux-krea",
  ]
  args = {
    PRESET = "flux-krea"
    HF_TOKEN = "${HF_TOKEN}"
  }
  cache-from = [
    "type=registry,ref=${REGISTRY}/${IMAGE_NAME}:${CACHE_FROM}-${CLOUD_TYPE}-flux-krea"
  ]
  cache-to = [
    "type=inline"
  ]
}

target "flux-kontext" {
  inherits = ["base"]
  tags = [
    "${REGISTRY}/${IMAGE_NAME}:${VERSION}-${CLOUD_TYPE}-flux-kontext",
  ]
  args = {
    PRESET = "flux-kontext"
    HF_TOKEN = "${HF_TOKEN}"
  }
  cache-from = [
    "type=registry,ref=${REGISTRY}/${IMAGE_NAME}:${CACHE_FROM}-${CLOUD_TYPE}-flux-kontext"
  ]
  cache-to = [
    "type=inline"
  ]
}

