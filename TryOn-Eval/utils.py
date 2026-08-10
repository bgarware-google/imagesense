import os
import yaml

def _load_config():
    """Loads the YAML configuration file and injects dynamic environment variables."""
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')

    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            print(f"[TryOn-Eval] Warning parsing config.yaml: {e}")

    # Fallback / Environment variable overrides for production
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or config.get("project", {}).get("id", "gdc-ai-playground")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION") or config.get("project", {}).get("location", "us-central1")
    zone = os.environ.get("GOOGLE_CLOUD_ZONE") or config.get("project", {}).get("zone", "us-central1-a")

    if "project" not in config:
        config["project"] = {}
    config["project"]["id"] = project_id
    config["project"]["location"] = location
    config["project"]["zone"] = zone

    if "gemini" not in config:
        config["gemini"] = {}
    if not config["gemini"].get("model_name") or "3.5" in config["gemini"].get("model_name", ""):
        config["gemini"]["model_name"] = "gemini-2.5-flash"

    return config

CONFIG = _load_config()
