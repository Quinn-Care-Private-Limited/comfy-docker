from aiohttp import web
import uuid
import asyncio
import rp_handler
import os
import gpustat

port = int(os.environ.get('PORT', 3000))

async def run_handler(run_id, data):
     await asyncio.to_thread(rp_handler.handler, {
        "id": run_id,
        "data": data
    })

async def handle_post(request):
    try:
        data = await request.json()  # Read JSON data from the request
        run_id = str(uuid.uuid4())   # Generate a unique job ID

        # Send response back immediately
        response_data = {"message": "Job created!", "run_id": run_id}
        response = web.json_response(response_data)

        # Schedule the rp_handler to run in the background
        asyncio.create_task(run_handler(run_id, data))

        return response
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)
    
def status(request): 
    run_id = request.match_info["run_id"]  # Extract path parameter
    return web.json_response(rp_handler.callback_data[run_id])

def health(request):
    gpu_stats = gpustat.new_query()
    response_data = {"status": "ok", "gpus": gpu_stats.gpus}
    response = web.json_response(response_data)
    return response
    

# Create the aiohttp web app
app = web.Application()
app.add_routes([web.get('/health', health)])  # Route for GET requests
app.add_routes([web.post('/run', handle_post)])  # Route for POST requests
app.add_routes([web.get('/status/{run_id}', status)])  # Route for POST requests

if __name__ == '__main__':
    web.run_app(app, port=port)