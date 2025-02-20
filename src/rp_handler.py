"""
The main serverless worker module for runpod
"""
import os
import requests
import json
# src imports
import comftroller
import utils 

# additional outputs logging. helpful for testing 
LOG_JOB_OUTPUTS = True
env = os.environ.get('ENV', 'production')

utils.log(f"ENV: {env}")

def callback(callback_url, data):
    if(callback_url is None):
        return
    requests.post(callback_url, headers={'Content-Type': 'application/json'}, data=json.dumps(data))  

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
    callback_url = job.get("callback_url")
    job_input = job["input"]  # input workflow

    # Validate inputs
    if job_input is None:
        return utils.error(f"no 'input' property found on job data")

    # if workflow is a string then validate will try convert to json
    workflow = utils.validate_json(job_input)
    # ensure workflow is valid JSON:
    if workflow is None:
        return utils.error(f"'workflow' must be a valid JSON object or JSON-encoded string")

    # set callback for when comftroller processes incomming data

    if(env == 'production'):
        update_progress = lambda data: callback(callback_url, {"job_id": job_id, "status": "processing", "data": utils.safe_parse(data)})  
    else:
        update_progress = lambda data: utils.log({"job_id": job_id, "status": "processing", "data": utils.safe_parse(data)})

    input_files = job_input.get("files", [])

    # outputs is equal to the completed comfyui job id history object
    outputs = comftroller.run(workflow, input_files, update_progress)
    # if LOG_JOB_OUTPUTS:
    #     utils.log("---- RAW OUTPUTS ----")
    #     utils.log(outputs)
    #     utils.log("")

    # if 'run' had an error, then stop job and return error as result
    if outputs.get('error'):
        update_progress({"job_id": job_id, "status": "error", "data":  outputs.get('error')})
        return

    # Fetching generated images
    output_files = [] # array of output filepath/urls
    output_datas = {} # dict of nont image output node datas as {"nodeid":{"outputdata":...}}

    # uglry nesterd lewpz: el boo!
    for node_id, node_output in outputs.items():
        # add output data to output_datas if not images or gifs data
        # scan job outputs for images/gifs (videos)
        if "images" in node_output:
            for data in node_output["images"]:
                output_datas[node_id] = node_output
                if data.get("type") == 'output':
                    if(data['subfolder'] == ''):
                        path = f"{data['filename']}"
                    else:    
                        path = f"{data['subfolder']}/{data['filename']}"
                    output_files.append(path)

    # if you dont know what this does... you shouldnt be here.
    utils.log(f"#files generated: {len(output_files)}")
    if LOG_JOB_OUTPUTS:
        utils.log("---- OUTPUT DATAS ----")
        utils.log(output_datas)
        utils.log("")

    update_progress({"job_id": job_id, "status": "success", "output": output_files})



