import os

import yaml

config_path = os.environ.get("CONFIG_PATH", "config.yaml")


def check_config():
    basic_conf = {
        "connection_key": "",
        "server": "0.0.0.0:8000"
    }
    if not os.path.exists(config_path):
        with open(config_path, "w") as f:
            try:
                f.write(yaml.dump(basic_conf))
            except yaml.YAMLError as exc:
                return None


def collect_config():
    check_config()
    with open(config_path, "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            return None


def save_config(conf: dict):
    with open(config_path, "w") as f:
        try:
            f.write(yaml.dump(conf))
        except yaml.YAMLError as exc:
            return None


config = collect_config()
