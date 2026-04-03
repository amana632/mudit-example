from pathlib import Path
import yaml


def load_config(config_path=None, overrides=None):
    """Load config from YAML file and apply CLI overrides."""
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.yaml"

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    if overrides:
        if overrides.get("hashtags"):
            config["hashtags"] = overrides["hashtags"]
        if overrides.get("output_file"):
            config["output"]["custom_output_file"] = overrides["output_file"]
        if overrides.get("max_profiles") is not None:
            config["settings"]["max_profiles_per_run"] = overrides["max_profiles"]
        if overrides.get("headless") is not None:
            config["settings"]["headless"] = overrides["headless"]

    return config
