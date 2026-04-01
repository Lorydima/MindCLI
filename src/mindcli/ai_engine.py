import os
import time
import contextlib
from gpt4all import GPT4All

@contextlib.contextmanager
def suppress_stderr_fd():
    """Temporarily suppresses stderr to hide verbose model output."""
    try:
        devnull = open(os.devnull, "w")
        old_fd = os.dup(2)
        os.dup2(devnull.fileno(), 2)
        yield
    finally:
        try:
            os.dup2(old_fd, 2)
            os.close(old_fd)
        except Exception:
            pass
        try:
            devnull.close()
        except Exception:
            pass

def sanitize_response(text: str) -> str:
    """Sanitizes text output from the AI response."""
    if not text:
        return ""
    t = text.strip()
    return t.strip()

def initialize_model(model_name, model_dir, device="cpu"):
    """Initializes the GPT4All model."""
    try:
        with suppress_stderr_fd():
            return GPT4All(
                model_name=model_name,
                model_path=model_dir,
                allow_download=False,
                device=device
            )
    except Exception as e:
        raise Exception(f"Error initializing model: {e}")

def get_model_file_and_dir(model_path, project_root):
    """Determines the actual model file and directory."""
    tried = []

    if not model_path:
        return None, None, ["No model_path set"]

    if os.path.isabs(model_path):
        candidate = model_path
    else:
        if os.path.dirname(model_path):
            candidate = os.path.abspath(os.path.join(project_root, model_path))
        else:
            candidate = os.path.join(project_root, "Models", model_path)

    tried.append(candidate)

    alt = os.path.join(project_root, "models", os.path.basename(model_path))
    tried.append(alt)

    if not os.path.exists(candidate) and os.path.exists(alt):
        candidate = alt

    if not os.path.exists(candidate):
        basename = os.path.basename(model_path)
        found = None
        for d in (os.path.join(project_root, "Models"), os.path.join(project_root, "models")):
            if os.path.isdir(d):
                for f in os.listdir(d):
                    full = os.path.join(d, f)
                    tried.append(full)
                    if f.lower().endswith(".gguf") and (os.path.splitext(basename)[0].lower() in f.lower()):
                        found = full
                        break
                if found:
                    break
        if found:
            candidate = found

    if not os.path.exists(candidate):
        return None, None, tried

    return os.path.basename(candidate), os.path.dirname(candidate), tried
