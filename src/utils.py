"""
This module contains utility functions for file handling.
"""

# required imports for utility functions:
import base64
import json
import os


def log(string):
    """
    Logs string to console with basic system prefix

    Args:
    - string (str): The string to log
    """
    print(f"[worker-comfy] {string}")


def job_prop_to_bool(job_input, propname):
    """
    Returns boolean based on variable value.
    Allows for checking string booleans, eg: "true"

    Args:
    - job_input (dict): A dictionary containing job input parameters.

    Returns:
    bool: True if job_input dict has propname that seems bool-ish
    """
    value = job_input.get(propname)
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    true_strings = ["true", "t", "yes", "y", "ok", "1"]
    if isinstance(value, str):
        return value.lower().strip() in true_strings
    return False


def validate_json(maybe_json):
    if isinstance(maybe_json, str):
        try:
            maybe_json = json.loads(maybe_json)
        except json.JSONDecodeError:
            return None

    # ensure workflow is valid JSON:
    if not isinstance(maybe_json, dict):
        return None

    return maybe_json


def error(error_message):
    """
    Logs error message and then returns basic dict with "error" prop using message

    Args:
    - error_message (string): A string containing the error emssage to show

    Returns:
    dict: containing error property with error message
    """
    log(error_message)  # log message then return error value
    return {"error": error_message}


def base64_encode(img_file):
    """
    Returns base64 encoded image.
    """
    log(f"scanning base64 for {img_file}")
    with open(img_file, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
        return encoded_string.decode("utf-8")


def safe_parse(data):
    if isinstance(data, dict):
        return data
    try:
        return json.loads(data)  # Attempt to parse if it's a string
    except json.JSONDecodeError:
        return {"error": "Invalid JSON", "raw_data": data}


def setup_storage_credentials():
    import base64

    gcp_credentials = os.environ.get("GCP_CREDENTIALS")
    aws_credentials = os.environ.get("AWS_CREDENTIALS")
    gcp_credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    aws_config_file_path = os.environ.get("AWS_CONFIG_FILE")
    aws_shared_credentials_file_path = os.environ.get("AWS_SHARED_CREDENTIALS_FILE")

    # if gcp_credentials is set, set it in gcp credentials file
    if gcp_credentials:
        with open(gcp_credentials_path, "w") as f:
            f.write(base64.b64decode(gcp_credentials).decode("utf-8"))
    elif aws_credentials:
        credentials = json.loads(base64.b64decode(aws_credentials).decode("utf-8"))

        with open(aws_config_file_path, "w") as f:
            content = f"""[default]
            region = {credentials["region_name"]}
            output = json"""
            f.write(content)

        with open(aws_shared_credentials_file_path, "w") as f:
            content = f"""[default]
            aws_access_key_id = {credentials["aws_access_key_id"]}
            aws_secret_access_key = {credentials["aws_secret_access_key"]}"""
            f.write(content)
    else:
        log("No storage credentials set")


def upload_file(file, bucket, key, cloud_type="GCP", credentials=None):
    """
    Uploads a file to a cloud storage bucket (GCP or AWS).
    Converts PNG files to JPEG before uploading.

    Args:
    - file (dict): Dictionary with 'name' and 'path' keys for the file to upload.
    - bucket (str): The name of the bucket to upload to.
    - key (str): The key/path to upload the file to.
    - cloud_type (str): Either "GCP" for Google Cloud Storage or "AWS" for S3.
    - credentials (dict): Optional credentials for cloud provider.
    """

    file_name = file["name"]
    file_path = file["path"]

    if credentials is None and os.getenv("UPLOAD_CREDENTIALS"):
        credentials = json.loads(
            base64.b64decode(os.getenv("UPLOAD_CREDENTIALS")).decode("utf-8")
        )

    # Convert PNG to JPEG if necessary
    if file_name.endswith(".png") and not key.endswith(".png"):
        from PIL import Image

        log(f"Converting PNG to JPEG: {file_name}")

        # Open the PNG image
        img = Image.open(file_path)

        # Convert RGBA to RGB if necessary (JPEG doesn't support transparency)
        if img.mode in ("RGBA", "LA", "P"):
            # Create a white background
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(
                img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None
            )
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # Create new file path with .jpg extension
        jpeg_path = file_path.rsplit(".", 1)[0] + ".jpg"

        # Save as JPEG with high quality
        img.save(jpeg_path, "JPEG", quality=95)

        # Remove the original PNG file
        os.remove(file_path)

        # Update file path and name
        file_path = jpeg_path
        file_name = file_name.rsplit(".", 1)[0] + ".jpg"

        log(f"Converted to JPEG: {file_name}")

    if cloud_type == "AWS":
        import boto3

        # Initialize S3 client
        aws_url = credentials.get("aws_url") if credentials else None
        aws_public_url = credentials.get("aws_public_url") if credentials else None

        if credentials:
            # Check if custom endpoint URL is provided (for S3-compatible services)
            if aws_url:
                s3_client = boto3.client(
                    "s3",
                    aws_access_key_id=credentials.get("aws_access_key_id"),
                    aws_secret_access_key=credentials.get("aws_secret_access_key"),
                    endpoint_url=aws_url,
                    region_name="auto",
                )
            else:
                s3_client = boto3.client(
                    "s3",
                    aws_access_key_id=credentials.get("aws_access_key_id"),
                    aws_secret_access_key=credentials.get("aws_secret_access_key"),
                    region_name=credentials.get("region_name", "us-east-1"),
                )
        else:
            # Use default credentials from environment/IAM role
            s3_client = boto3.client("s3")

        # Upload file to S3
        s3_client.upload_file(file_path, bucket, key)
        log(f"File {file_name} uploaded to S3 bucket {bucket} at {key}.")

        # Generate the S3 URL
        if aws_public_url:
            url = f"{aws_public_url}/{key}"
        elif aws_url:
            # Cloudflare doesn't provide a default URL for R2 buckets
            url = None
        else:
            region = (
                credentials.get("region_name", "us-east-1")
                if credentials
                else "us-east-1"
            )
            url = f"https://{bucket}.s3.{region}.amazonaws.com/{key}"

        os.remove(file_path)

        return {
            "name": file_name,
            "path": file_path,
            "url": url,
        }

    else:  # Default to GCP
        from google.cloud import storage

        if credentials:
            storage_client = storage.Client.from_service_account_json(credentials)
        else:
            storage_client = storage.Client()
        bucket_obj = storage_client.bucket(bucket)

        blob = bucket_obj.blob(key)
        blob.upload_from_filename(file_path)
        log(f"File {file_name} uploaded to GCS bucket {bucket} at {key}.")
        os.remove(file_path)

        # return the url of the uploaded file
        return {
            "name": file_name,
            "path": file_path,
            "url": blob.public_url,
        }


def upload_files(files, bucket, key, cloud_type, credentials=None):
    """
    Uploads a list of files to a cloud storage bucket (GCP or AWS).
    """
    uploaded_files = []
    if len(files) == 1:
        uploaded_files.append(
            upload_file(files[0], bucket, key, cloud_type, credentials)
        )
    else:
        ## replace any extension from key
        key = key.split(".")[0]
        for index, file in enumerate(files):
            file_name = file["name"]
            file_name = file_name.replace("_00001_", "")
            uploaded_files.append(
                upload_file(file, bucket, f"{key}/{file_name}", cloud_type, credentials)
            )
    return uploaded_files


class ProgressTracker:
    def __init__(self, payload):
        self.payload = payload
        self.total_nodes = len(payload)
        self.node_progress = {node: 0 for node in payload}
        self.node_status = {node: "pending" for node in payload}
        self.progress = 0
        self.previous_node = None

    def update_progress(self, status_callback):
        try:
            data = status_callback["data"]

            if status_callback["type"] == "executing":
                node = data["node"]
                self.node_status[node] = "executing"
                # Don't reset progress - preserve existing progress to prevent going backwards
                if self.previous_node:
                    self.node_status[self.previous_node] = "completed"
                    self.node_progress[self.previous_node] = 1
                self.previous_node = node

            elif status_callback["type"] == "progress":
                node = data["node"]
                self.node_status[node] = "executing"
                new_progress = data["value"] / data["max"]
                # Only update if progress is not reducing
                if new_progress >= self.node_progress[node]:
                    self.node_progress[node] = new_progress

            self.calculate_overall_progress()
        except Exception as e:
            log(f"Error updating progress: {e}")

    def calculate_overall_progress(self):
        total_progress = sum(self.node_progress.values())
        self.progress = int((total_progress / self.total_nodes) * 100)
