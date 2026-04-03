import os
import tempfile
import pytest
from src.config import load_config


def test_load_config_from_file():
    yaml_content = """
hashtags:
  - "#travel"
  - "#adventure"

settings:
  max_profiles_per_run: 20
  max_posts_per_hashtag: 40
  delay_between_profiles: [1, 3]
  cooldown_every: 5
  cooldown_duration: [10, 20]
  daily_cap_warning: 50
  headless: true

output:
  directory: "./out"
  filename_prefix: "test"
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        f.flush()
        config = load_config(config_path=f.name)

    assert config["hashtags"] == ["#travel", "#adventure"]
    assert config["settings"]["max_profiles_per_run"] == 20
    assert config["settings"]["headless"] is True
    assert config["output"]["directory"] == "./out"
    os.unlink(f.name)


def test_load_config_with_cli_overrides():
    yaml_content = """
hashtags:
  - "#travel"

settings:
  max_profiles_per_run: 30
  max_posts_per_hashtag: 50
  delay_between_profiles: [2, 5]
  cooldown_every: 10
  cooldown_duration: [30, 60]
  daily_cap_warning: 80
  headless: false

output:
  directory: "./output"
  filename_prefix: "leads"
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        f.flush()
        overrides = {
            "hashtags": ["#beach", "#surf"],
            "output_file": "custom.csv",
            "max_profiles": 10,
            "headless": True,
        }
        config = load_config(config_path=f.name, overrides=overrides)

    assert config["hashtags"] == ["#beach", "#surf"]
    assert config["output"]["custom_output_file"] == "custom.csv"
    assert config["settings"]["max_profiles_per_run"] == 10
    assert config["settings"]["headless"] is True
    os.unlink(f.name)


def test_load_config_default_path(monkeypatch):
    """When no path given, loads from config.yaml in project root."""
    config = load_config()
    assert "#travelcreator" in config["hashtags"]
    assert config["settings"]["max_profiles_per_run"] == 30
