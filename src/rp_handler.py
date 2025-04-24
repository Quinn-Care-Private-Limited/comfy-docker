"""
The main serverless worker module for runpod
"""
import os
import requests
import json
# src imports
import comftroller
import utils 
import runpod

# additional outputs logging. helpful for testing 
LOG_JOB_OUTPUTS = True
env = os.environ.get('ENV', 'production')

data_path = os.environ.get('DATA_PATH', '/comfyui/data')

utils.log(f"ENV: {env}")

def callback(job, data):
    if env == 'production':
        runpod.serverless.callback(job, data)
    else:   
        utils.log(data)
    
    if "callback_url" in job["input"]:
        # send callback to comfyui
        requests.post(job["input"]["callback_url"], headers={'Content-Type': 'application/json'}, data=json.dumps(data))  

def process_callback(tracker, data):
    data = utils.safe_parse(data)
    tracker.update_progress(data)
    return {"progress": tracker.progress}
    
def handler(job):
    """
    The main function that handles a job of generating an image.

    This function validates the input, sends a prompt to ComfyUI for processing,
    polls ComfyUI for result, and retrieves generated images.

    Args:
        job (dict): A dictionary containing job details and input parameters.

    Returns:
        dict: A dictionary containing either an error message or a success status with generated images.
    """
    job_id = job["id"]
    job_input = job["input"]

    # Validate inputs
    if "workflow" not in job_input:
        return utils.error(f"no 'workflow' property found on job input")

    # if workflow is a string then validate will try convert to json
    workflow = utils.validate_json(job_input["workflow"])
    # ensure workflow is valid JSON:
    if workflow is None:
        return utils.error(f"'workflow' must be a valid JSON object or JSON-encoded string")

    # set callback for when comftroller processes incomming data

    tracker = utils.ProgressTracker(workflow)

    update_progress = lambda data: callback(job, {"run_id": job_id, "status": "processing", "data": process_callback(tracker, data)})  
    
    input_files = job_input.get("files", [])

    # outputs is equal to the completed comfyui job id history object
    outputs = comftroller.run(workflow, input_files, update_progress)
    # if LOG_JOB_OUTPUTS:
    #     utils.log("---- RAW OUTPUTS ----")
    #     utils.log(outputs)
    #     utils.log("")

    # if 'run' had an error, then stop job and return error as result
    if outputs.get('error'):
        callback(job, {"run_id": job_id, "status": "failed", "data": outputs.get('error')})
        return

    # Fetching generated images
    output_files = [] # array of output filepath/urls
    # uglry nesterd lewpz: el boo!
    for node_id, node_output in outputs.items():
        # add output data to output_datas if not images or gifs data
        # scan job outputs for images/gifs (videos)
        if "images" in node_output:
            for data in node_output["images"]:
                if data.get("type") == 'output':
                    output_files.append({"name": data['filename'], "path": os.path.join(data_path, data['filename'])})
        
        if "gifs" in node_output:
            for data in node_output["gifs"]:
                if data.get("type") == 'output':
                    output_files.append({"name": data['filename'], "path": os.path.join(data_path, data['filename'])})

    # if you dont know what this does... you shouldnt be here.
    if LOG_JOB_OUTPUTS:
        utils.log(f"#files generated: {len(output_files)}")
        utils.log("---- OUTPUT FILES ----")
        utils.log(output_files)
        utils.log("")

    if "bucket" in job_input and "creds" in job_input:
        utils.upload_file_gcs(output_files, job_input["bucket"], job_input["creds"])

    callback(job, {"run_id": job_id, "status": "completed", "data": {"progress": 100, "output": output_files}})
    return output_files



