
import rp_handler
import runpod

runpod.serverless.start({"handler": rp_handler.handler})
    