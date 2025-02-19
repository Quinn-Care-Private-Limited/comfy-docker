from aiohttp import web
import uuid
import asyncio
import rp_handler

async def run_handler(job_id, data):
     await asyncio.to_thread(rp_handler.handler, {
        "id": job_id,
        "callback_url": data.get("callback_url"),
        "input": data.get("input")
    })

async def handle_post(request):
    try:
        data = await request.json()  # Read JSON data from the request
        job_id = str(uuid.uuid4())   # Generate a unique job ID

        # Send response back immediately
        response_data = {"message": "Job created!", "job_id": job_id}
        response = web.json_response(response_data)

        # Schedule the rp_handler to run in the background
        asyncio.create_task(run_handler(job_id, data))

        return response
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)
    

# Create the aiohttp web app
app = web.Application()
app.add_routes([web.post('/', handle_post)])  # Route for POST requests

if __name__ == '__main__':
    web.run_app(app, port=8000)