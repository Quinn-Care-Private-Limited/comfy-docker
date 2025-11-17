import os
import json
import subprocess
import sys


# Helper function to print to both stdout and stderr for visibility
def log(message):
    print(message, flush=True)
    # print(message, file=sys.stderr, flush=True)


# Load JSON data from the file (get json_file_path from arg)
if len(sys.argv) < 2:
    log("Usage: python3 custom-file-installer.py <json_file_path>")
    sys.exit(1)

json_file_path = sys.argv[1]

log(f"Loading custom files from {json_file_path}...")
with open(json_file_path, "r") as json_file:
    data = json.load(json_file)

log(f"Found {len(data)} custom file(s) to install.")

# Iterate over each object in the JSON array
for item in data:
    url = item.get("url")
    path = item.get("path")

    if url and path:
        if url.endswith(".git"):
            try:  # Clone the Git repository into the specified path
                log(f"Cloning {url} to {path}...")
                subprocess.check_call(["git", "clone", url, path])
                log(f"✓ Successfully cloned Git repository from {url} to {path}")
            except subprocess.CalledProcessError as e:
                log(f"✗ Error cloning Git repository from {url}: {e}")
        else:
            try:  # Download model into the specified path
                log(f"Downloading {url} to {path}...")
                HF_TOKEN = os.environ.get("HF_TOKEN")
                wget_command = ["wget", "-O", path]
                if HF_TOKEN:
                    wget_command.extend(
                        ["--header", f"Authorization: Bearer {HF_TOKEN}"]
                    )
                wget_command.extend([url])
                subprocess.check_call(wget_command)
                log(f"✓ Successfully downloaded {url} and saved it to {path}")
            except subprocess.CalledProcessError as e:
                log(f"✗ Error downloading {url}: {e}")

log("Download process completed.")
