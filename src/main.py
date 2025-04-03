
import rp_handler
import runpod


if __name__ == '__main__':
    runpod.serverless.start({"handler": rp_handler.handler})