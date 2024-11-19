# config/__init__.py

import json

def load_config(config_file_path):
    with open(config_file_path, 'r') as f:
        config = json.load(f)
    return config
