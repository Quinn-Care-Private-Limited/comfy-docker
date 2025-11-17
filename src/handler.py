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
env = os.environ.get("ENV", "production")
cloud_type = os.environ.get("CLOUD_TYPE")
data_path = os.environ.get("FS_PATH") + os.environ.get("DATA_PATH")

LOG_JOB_OUTPUTS = env == "development"

utils.log(f"ENV: {env}")
utils.log(f"CLOUD_TYPE: {cloud_type}")

callback_data = {}
utils.setup_storage_credentials()


def get_status(run_id):
    return callback_data[run_id]


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
    run_id = job["id"]
    job_input = job["input"]
    workflow = job_input["workflow"]
    metadata = job_input.get("metadata")
    callback_url = job_input.get("callback_url")
    callback_auth_header = job_input.get("callback_auth_header")

    def callback(data):
        prev_data = callback_data.get(data["run_id"])
        prev_progress = prev_data.get("data", {}).get("progress", 0)
        new_progress = data.get("data", {}).get("progress", 0)
        status = data.get("status")

        callback_data[data["run_id"]] = data

        if prev_data and status == "processing" and prev_progress == new_progress:
            return

        if cloud_type == "RUNPOD":
            import runpod

            if env == "development":
                utils.log(data)
            else:
                runpod.serverless.progress_update({"id": data["run_id"]}, data)

        if callback_url is None:
            return

        headers = {"Content-Type": "application/json"}
        if callback_auth_header:
            headers.update(callback_auth_header)
        try:
            requests.post(
                callback_url,
                headers=headers,
                data=json.dumps(data),
            )
        except Exception as e:
            pass

    # input workflow
    callback_data[run_id] = {
        "run_id": run_id,
        "status": "processing",
        "data": {"progress": 0},
    }

    # Validate inputs
    if workflow is None:
        return utils.error(f"no 'input' property found on job data")

    # if workflow is a string then validate will try convert to json
    workflow = utils.validate_json(workflow)
    # ensure workflow is valid JSON:
    if workflow is None:
        return utils.error(
            f"'workflow' must be a valid JSON object or JSON-encoded string"
        )

    # set callback for when comftroller processes incomming data

    tracker = utils.ProgressTracker(workflow)

    update_progress = lambda data: callback(
        {
            "run_id": run_id,
            "status": "processing",
            "data": process_callback(tracker, data),
            "metadata": metadata,
        }
    )

    input_files = job_input.get("files", [])

    # outputs is equal to the completed comfyui job id history object
    outputs = comftroller.run(workflow, input_files, update_progress)
    # if LOG_JOB_OUTPUTS:
    #     utils.log("---- RAW OUTPUTS ----")
    #     utils.log(outputs)
    #     utils.log("")

    # if 'run' had an error, then stop job and return error as result
    if outputs.get("error"):
        callback(
            {
                "run_id": run_id,
                "status": "failed",
                "data": {"error": outputs.get("error")},
                "metadata": metadata,
            },
        )
        return {"error": outputs.get("error")}

    # Fetching generated images
    output_files = []  # array of output filepath/urls
    # uglry nesterd lewpz: el boo!
    for node_id, node_output in outputs.items():
        # add output data to output_datas if not images or gifs data
        # scan job outputs for images/gifs (videos)
        if "images" in node_output:
            for data in node_output["images"]:
                if data.get("type") == "output":
                    output_files.append(
                        {
                            "name": data["filename"],
                            "path": os.path.join(data_path, data["filename"]),
                        }
                    )

        if "gifs" in node_output:
            for data in node_output["gifs"]:
                if data.get("type") == "output":
                    output_files.append(
                        {
                            "name": data["filename"],
                            "path": os.path.join(data_path, data["filename"]),
                        }
                    )

    # if you dont know what this does... you shouldnt be here.
    if LOG_JOB_OUTPUTS:
        utils.log(f"#files generated: {len(output_files)}")
        utils.log("---- OUTPUT FILES ----")
        utils.log(output_files)
        utils.log("")

    try:
        if "upload" in job_input:
            output_files = utils.upload_files(
                output_files,
                job_input["upload"]["bucket"],
                job_input["upload"]["key"],
                job_input["upload"]["cloud_type"],
                job_input["upload"]["credentials"],
            )
    except Exception as e:
        utils.log(f"Error uploading files to GCS: {e}")
        callback(
            {
                "run_id": run_id,
                "status": "failed",
                "data": {"error": "Error uploading files to GCS"},
                "metadata": metadata,
            },
        )
        return {"error": "Error uploading files to GCS"}

    callback(
        {
            "run_id": run_id,
            "status": "completed",
            "data": {"progress": 100, "output": output_files},
            "metadata": metadata,
        },
    )
    return {"output": output_files}
