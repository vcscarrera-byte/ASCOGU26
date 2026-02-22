"""Load .env secrets and config.yaml settings."""

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env", override=True)

X_BEARER_TOKEN = os.environ.get("X_BEARER_TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


def load_config() -> dict:
    """Load and return config.yaml as a dict."""
    config_path = PROJECT_ROOT / "config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


_config = load_config()


def get_db_path() -> Path:
    """Resolve database path (relative to project root)."""
    return PROJECT_ROOT / _config["project"]["db_path"]


def get_exports_dir() -> Path:
    path = PROJECT_ROOT / _config["project"]["exports_dir"]
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_briefs_dir() -> Path:
    path = PROJECT_ROOT / _config["project"]["briefs_dir"]
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_collection_config() -> dict:
    return _config["collection"]


def get_api_config() -> dict:
    return _config["api"]


def get_topic_config() -> dict:
    return _config["topic_modeling"]


def get_summarizer_config() -> dict:
    return _config["summarizer"]


def get_clinical_filter_config() -> dict:
    return _config.get("clinical_filters", {})
