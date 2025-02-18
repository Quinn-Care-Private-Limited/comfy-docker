# import os
import json
import requests
import subprocess

# Load JSON data from the file
json_file_path = 'custom-files.json'  # Replace with the path to your JSON file
path = "/comfyui/custom_nodes"

with open(json_file_path, 'r') as json_file:
    data = json.load(json_file)
    # Iterate over each object in the JSON array
    for url in data:
        if url.endswith('.git'):
            try:# Clone the Git repository into the specified path
                subprocess.check_call(['git', 'clone', url, path])
                print(f"Cloned Git repository from {url} to {path}")
            except subprocess.CalledProcessError as e:
                print(f"Error cloning Git repository from {url}: {e}")


print("Download process completed.")