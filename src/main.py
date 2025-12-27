import os
import json
import handler

port = int(os.environ.get("PORT", 3000))
cloud_type = os.environ.get("CLOUD_TYPE")
env = os.environ.get("ENV", "production")


def run():
    if cloud_type == "GCP" or cloud_type == "AWS":
        import uuid
        import asyncio
        import gpustat
        import psutil
        from aiohttp import web

        if env == "development":
            test_json_path = "/app/test_input.json"
            if os.path.exists(test_json_path):
                with open(test_json_path, "r") as f:
                    test_data = json.load(f)
                run_id = str(uuid.uuid4())
                job = {"id": run_id, "input": test_data["input"]}
                print(f"Running test with JSON file: {test_json_path}")
                handler.handler(job)
                print(f"Test completed with successfully")
            else:
                print(f"Test JSON file not found: {test_json_path}")

            return

        async def run_handler(run_id, data):
            await asyncio.to_thread(handler.handler, {"id": run_id, "input": data["input"]})

        async def handle_post(request):
            try:
                data = await request.json()  # Read JSON data from the request
                run_id = str(uuid.uuid4())  # Generate a unique job ID

                # Send response back immediately
                response_data = {"message": "Job created!", "run_id": run_id}
                response = web.json_response(response_data)

                # Schedule the rp_handler to run in the background
                asyncio.create_task(run_handler(run_id, data))

                return response
            except Exception as e:
                return web.json_response({"error": str(e)}, status=500)

        def status(request):
            run_id = request.match_info["run_id"]  # Extract path parameter
            return web.json_response(handler.callback_data[run_id])

        def health(request):
            gpu_stats = gpustat.new_query()
            response_data = {
                "status": "ok",
                "gpu": gpu_stats.gpus[0].utilization,
                "cpu": psutil.cpu_percent(interval=1),
            }
            response = web.json_response(response_data)
            return response

        # Create the aiohttp web app
        app = web.Application()
        app.add_routes([web.get("/health", health)])  # Route for GET requests
        app.add_routes([web.post("/run", handle_post)])  # Route for POST requests
        app.add_routes([web.get("/status/{run_id}", status)])  # Route for POST requests

        web.run_app(app, port=port)

    elif cloud_type == "RUNPOD":
        import runpod

        runpod.serverless.start({"handler": handler.handler})
    else:
        raise ValueError(f"Invalid cloud type: {cloud_type}")


if __name__ == "__main__":
    run()
