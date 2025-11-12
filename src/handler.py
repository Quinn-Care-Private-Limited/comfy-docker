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
env = os.environ.get("ENV", "production")
cloud_type = os.environ.get("CLOUD_TYPE")
data_path = os.environ.get("FS_PATH") + os.environ.get("DATA_PATH")


utils.log(f"ENV: {env}")
utils.log(f"CLOUD_TYPE: {cloud_type}")

callback_data = {}


def setup_storage_credentials():
    gcp_credentials = os.environ.get("GCP_CREDENTIALS")
    gcp_credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

    # if gcp_credentials is set, set it in gcp credentials file
    if gcp_credentials:
        with open(gcp_credentials_path, "w") as f:
            import base64

            f.write(base64.b64decode(gcp_credentials).decode("utf-8"))
    else:
        utils.log("No storage credentials set")


def callback(data, callback_url=None, callback_auth_header=None):
    callback_data[data["run_id"]] = data
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
    requests.post(
        callback_url,
        headers=headers,
        data=json.dumps(data),
    )


def get_status(run_id):
    return callback_data[run_id]


def process_callback(tracker, data):
    data = utils.safe_parse(data)
    tracker.update_progress(data)
    return {"progress": tracker.progress, "status": data}


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
    callback_url = job_input.get("callback_url")
    callback_auth_header = job_input.get("callback_auth_header")

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
        },
        callback_url,
        callback_auth_header,
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
            {"run_id": run_id, "status": "failed", "data": outputs.get("error")},
            callback_url,
            callback_auth_header,
        )
        return

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
        if "bucket" in job_input:
            utils.upload_file_gcs_path(output_files, job_input["bucket"])
        elif "upload" in job_input:
            utils.upload_file_gcs(
                output_files[0],
                job_input["upload"]["bucket"],
                job_input["upload"]["key"],
            )
    except Exception as e:
        utils.log(f"Error uploading files to GCS: {e}")
        callback(
            {
                "run_id": run_id,
                "status": "failed",
                "data": {"error": "Error uploading files to GCS"},
            },
            callback_url,
            callback_auth_header,
        )
        return output_files

    callback(
        {
            "run_id": run_id,
            "status": "completed",
            "data": {"progress": 100, "output": output_files},
        },
        callback_url,
        callback_auth_header,
    )
    return output_files
