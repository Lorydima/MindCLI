# Configuration management — loads and saves model configs, paths, and API keys.

import os
import json
from mindcli import state
from mindcli.utils import get_base_path, detect_gpu_device
from mindcli.memory_manager import load_memories


def sanitize_model_filename(model_name: str) -> str:
    """Sanitizes model name to make it a safe JSON filename."""
    sanitized = (model_name or "").replace(":", "_").replace("/", "_").replace("\\", "_")
    return f"{sanitized}.json"


def get_model_base_name(model_name: str) -> str:
    """Returns the model name without the quantization tag (e.g. 'model:latest' -> 'model')."""
    if not model_name:
        return ""
    return model_name.split(":", 1)[0]


def normalize_parameters(params):
    """Normalizes stored parameters and backfills missing defaults with v1.0 compatibility."""
    normalized = state.DEFAULT_PARAMS.copy()
    if isinstance(params, dict):
        normalized.update(params)
    # Backward compatibility with v1.0 key names
    if "max_tokens" in normalized:
        normalized["num_predict"] = normalized.pop("max_tokens")
    if "temp" in normalized:
        normalized["temperature"] = normalized.pop("temp")
    normalized.setdefault("num_predict", state.DEFAULT_PARAMS["num_predict"])
    normalized.setdefault("temperature", state.DEFAULT_PARAMS["temperature"])
    normalized.setdefault("top_p", state.DEFAULT_PARAMS["top_p"])
    normalized.setdefault("repeat_penalty", state.DEFAULT_PARAMS["repeat_penalty"])
    normalized.setdefault("num_ctx", state.DEFAULT_PARAMS["num_ctx"])
    return normalized


def get_models_dir():
    """Returns the path to the model-specific configs directory, creating it if necessary."""
    d = os.path.join(get_base_path(), "models")
    os.makedirs(d, exist_ok=True)
    return d


def get_chats_dir():
    """Returns the path to the chats directory, creating it if necessary."""
    d = os.path.join(get_base_path(), "chats")
    os.makedirs(d, exist_ok=True)
    return d


def load_config():
    """Loads all configuration files and populates global state with saved values."""
    config_dir = os.path.join(get_base_path(), "configs")
    os.makedirs(config_dir, exist_ok=True)

    paths_path = os.path.join(config_dir, "paths.json")
    hardware_path = os.path.join(config_dir, "hardware.json")
    tavily_path = os.path.join(config_dir, "tavily_API.json")

    saved_model = ""
    saved_device = detect_gpu_device()
    state.config_tavily_api_key = ""

    # Load paths config
    if os.path.exists(paths_path):
        try:
            with open(paths_path, "r", encoding="utf-8") as f:
                pcfg = json.load(f)
                saved_model = pcfg.get("active_model", "")
        except Exception:
            pass

    # Load Tavily API key
    if os.path.exists(tavily_path):
        try:
            with open(tavily_path, "r", encoding="utf-8") as f:
                tcfg = json.load(f)
                state.config_tavily_api_key = tcfg.get("tavily_api_key", "")
        except Exception:
            pass

    # Load hardware config
    if os.path.exists(hardware_path):
        try:
            with open(hardware_path, "r", encoding="utf-8") as f:
                hcfg = json.load(f)
                saved_device = hcfg.get("device", saved_device)
        except Exception:
            pass

    desktop_default = os.path.join(os.path.expanduser("~"), "Desktop")

    # Create default config files if they don't exist
    if not os.path.exists(paths_path):
        try:
            with open(paths_path, "w", encoding="utf-8") as f:
                json.dump({"active_model": "", "desktop_path": desktop_default}, f, indent=2)
        except Exception:
            pass

    if not os.path.exists(tavily_path):
        try:
            with open(tavily_path, "w", encoding="utf-8") as f:
                json.dump({"tavily_api_key": ""}, f, indent=2)
        except Exception:
            pass

    if not os.path.exists(hardware_path):
        try:
            with open(hardware_path, "w", encoding="utf-8") as f:
                json.dump({"device": saved_device}, f, indent=2)
        except Exception:
            pass

    state.config_model_path = saved_model
    state.config_device = saved_device
    state.config_base_prompt = state.DEFAULT_BASE_PROMPT
    state.config_download_source = "N/A"
    state.config_parameters = state.DEFAULT_PARAMS.copy()

    # Load per-model configuration if a model is saved
    if saved_model:
        models_dir = get_models_dir()
        model_cfg_filename = sanitize_model_filename(saved_model)
        model_cfg_path = os.path.join(models_dir, model_cfg_filename)

        model_config = {}
        if os.path.exists(model_cfg_path):
            try:
                with open(model_cfg_path, "r", encoding="utf-8") as f:
                    model_config = json.load(f)
            except Exception:
                pass

        if model_config.get("base_prompt"):
            state.config_base_prompt = model_config["base_prompt"]

        state.config_download_source = model_config.get("download_source", "N/A")
        state.config_device = model_config.get("device", saved_device)
        state.config_parameters = normalize_parameters(model_config.get("parameters", state.DEFAULT_PARAMS.copy()))

    load_memories()


def save_config_to_file(model_name, base_prompt, parameters=None, download_source=None, device=None):
    """Saves active model config and its per-model JSON file. Updates paths, hardware, and Tavily configs."""
    if parameters is None:
        parameters = state.config_parameters
    if download_source is None:
        download_source = state.config_download_source
    if device is None:
        device = state.config_device
    if not base_prompt:
        base_prompt = state.DEFAULT_BASE_PROMPT

    config_dir = os.path.join(get_base_path(), "configs")
    os.makedirs(config_dir, exist_ok=True)

    paths_path = os.path.join(config_dir, "paths.json")
    tavily_path = os.path.join(config_dir, "tavily_API.json")
    hardware_path = os.path.join(config_dir, "hardware.json")

    # Save paths config
    try:
        pcfg = {}
        if os.path.exists(paths_path):
            with open(paths_path, "r", encoding="utf-8") as f:
                pcfg = json.load(f)
        pcfg["active_model"] = model_name
        with open(paths_path, "w", encoding="utf-8") as f:
            json.dump(pcfg, f, indent=2)
    except Exception as e:
        state.console.print(f"[red]Error saving paths: {e}[/red]")

    # Save Tavily API key
    try:
        tcfg = {}
        if os.path.exists(tavily_path):
            with open(tavily_path, "r", encoding="utf-8") as f:
                tcfg = json.load(f)
        tcfg["tavily_api_key"] = state.config_tavily_api_key
        with open(tavily_path, "w", encoding="utf-8") as f:
            json.dump(tcfg, f, indent=2)
    except Exception as e:
        state.console.print(f"[red]Error saving Tavily API key: {e}[/red]")

    # Save hardware config
    try:
        hcfg = {}
        if os.path.exists(hardware_path):
            with open(hardware_path, "r", encoding="utf-8") as f:
                hcfg = json.load(f)
        hcfg["device"] = device
        with open(hardware_path, "w", encoding="utf-8") as f:
            json.dump(hcfg, f, indent=2)
    except Exception as e:
        state.console.print(f"[red]Error saving hardware config: {e}[/red]")

    state.config_model_path = model_name
    state.config_device = device

    # If no model name, save global state only
    if not model_name:
        state.config_parameters = normalize_parameters(parameters)
        state.config_download_source = download_source
        state.config_device = device
        return True

    # Save per-model configuration
    models_dir = get_models_dir()
    model_cfg_filename = sanitize_model_filename(model_name)
    model_cfg_path = os.path.join(models_dir, model_cfg_filename)

    cfg = {
        "base_prompt": base_prompt,
        "download_source": download_source,
        "device": device,
        "parameters": normalize_parameters(parameters)
    }

    try:
        with open(model_cfg_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        state.config_parameters = normalize_parameters(parameters)
        state.config_download_source = download_source
        state.config_device = device
        return True
    except Exception as e:
        state.console.print(f"[red]Error saving model config: {e}[/red]")
        return False
