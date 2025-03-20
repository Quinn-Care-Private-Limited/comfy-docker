"""
This module contains utility functions for file handling.
"""


# required imports for utility functions:
import base64
import json 

# # import nudenet lib: (nudity detection)
# # see: https://github.com/notAI-tech/NudeNet/tree/v3
# from nudenet import NudeDetector

# def detect_nudity(img_file):
#     """
#     Returns:
#     list: of detected nudity for img_file if able
#     """
#     log(f"scanning nudity for {img_file}")
#     return NudeDetector().detect(img_file) 


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
    if value is None: return False
    if isinstance(value, bool): return value
    true_strings = ['true', 't', 'yes', 'y', 'ok', '1']
    if isinstance(value, str): return value.lower().strip() in true_strings
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
    log(error_message) # log message then return error value
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
    

class ProgressTracker:
    def __init__(self, payload):
        self.payload = payload
        self.total_nodes = len(payload)
        self.node_progress = {node: 0 for node in payload}
        self.node_status = {node: 'pending' for node in payload}
        self.progress = 0
        self.previous_node = None

    def update_progress(self, status_callback):
        try:
            data = status_callback['data']
    
            if status_callback['type'] == 'executing':
                node = data['node']
                self.node_status[node] = 'executing'
                self.node_progress[node] = 0  # Reset progress for executing node
                if self.previous_node:
                    self.node_status[self.previous_node] = 'completed'
                    self.node_progress[self.previous_node] = 1
                self.previous_node = node


            elif status_callback['type'] == 'progress':
                node = data['node']
                self.node_status[node] = 'executing'
                self.node_progress[node] = data['value'] / data['max']

            self.calculate_overall_progress()
        except Exception as e:
            log(f"Error updating progress: {e}")

    def calculate_overall_progress(self):
        total_progress = sum(self.node_progress.values())
        self.progress = int((total_progress / self.total_nodes) * 100)