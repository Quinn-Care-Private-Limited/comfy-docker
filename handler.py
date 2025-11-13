import runpod
import src.handler as rp_handler


def handler(job):
    rp_handler.setup_storage_credentials()
    return rp_handler.handler(job)


runpod.serverless.start({"handler": handler})
