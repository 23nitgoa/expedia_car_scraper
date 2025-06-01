import json

def load_json_config(file_path):
    with open(file_path, 'r') as file:
        configs = json.load(file)
        return configs
