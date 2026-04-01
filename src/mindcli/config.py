import os
import sys
import json

# Default AI Parameters
DEFAULT_PARAMS = {
    "max_tokens": 2048,
    "temp": 0.4,
    "top_p": 0.9,
    "repeat_penalty": 1.1
}

def get_base_path():
    """Returns the base path for config and resources, adjusting for PyInstaller."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_assets_path():
    """Returns the path to the assets folder."""
    return os.path.join(get_base_path(), "assets")

def load_config():
    """Loads config settings like model_path and base_prompt."""
    config_path = os.path.join(get_assets_path(), "config.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            try:
                config = json.load(f)
            except json.JSONDecodeError:
                config = {}
    except FileNotFoundError:
        config = {}

    # Extract values with defaults
    return {
        "model_path": config.get("model_path"),
        "base_prompt": config.get("base_prompt"),
        "download_source": config.get("download_source", "N/A"),
        "device": config.get("device", "cpu"),
        "parameters": config.get("parameters", DEFAULT_PARAMS.copy())
    }

def save_config_to_file(model_path, base_prompt, parameters=None, download_source=None, device=None):
    """Saves the given values to config.json."""
    if parameters is None:
        parameters = DEFAULT_PARAMS.copy()
    if download_source is None:
        download_source = "N/A"
    if device is None:
        device = "cpu"
        
    config_path = os.path.join(get_assets_path(), "config.json")
    cfg = {
        "model_path": model_path,
        "base_prompt": base_prompt,
        "download_source": download_source,
        "device": device,
        "parameters": parameters
    }
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False
