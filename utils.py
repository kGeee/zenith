import json
import os


def get_config():
    # config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open("config.json") as f:
        return json.load(f)