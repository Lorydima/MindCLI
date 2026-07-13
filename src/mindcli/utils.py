# Utility functions for common operations across the application.

import sys
import os
import contextlib
import pyperclip
from mindcli.state import console


def get_base_path():
    """Returns the base path for config and resources, adjusting for PyInstaller."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def copy_to_clipboard(text: str) -> bool:
    """Copies text using pyperclip and returns success status."""
    try:
        pyperclip.copy(text)
        return True
    except Exception:
        pass
    return False


def prompt_masked_windows(prompt: str) -> str:
    """Prompts for hidden input using Windows-style asterisks or Rich password field."""
    try:
        import msvcrt
    except Exception:
        return console.input(prompt, password=True).strip()

    console.print(prompt, end="")
    chars = []
    while True:
        ch = msvcrt.getwch()
        if ch in ("\r", "\n"):
            sys.stdout.write("\n")
            sys.stdout.flush()
            break
        if ch == "\b":
            if chars:
                chars.pop()
                sys.stdout.write("\b \b")
                sys.stdout.flush()
            continue
        if ch in ("\x00", "\xe0"):
            msvcrt.getwch()
            continue
        chars.append(ch)
        sys.stdout.write("*")
        sys.stdout.flush()
    return "".join(chars).strip()


def extract_domain(value: str) -> str:
    """Extracts a domain from a URL-like value (e.g. https://example.com/path -> example.com)."""
    if not value:
        return ""
    value = value.strip()
    if not value.startswith(("http://", "https://")):
        return ""
    try:
        from urllib.parse import urlparse as _urlparse
        return _urlparse(value).netloc.lower()
    except Exception:
        return ""


def sanitize_response(text: str) -> str:
    """Sanitizes text output from the AI response by stripping whitespace."""
    if not text:
        return ""
    return text.strip()


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


def detect_gpu_device() -> str:
    """Detects if an NVIDIA GPU is available via nvidia-smi and returns 'gpu' or 'cpu'."""
    try:
        if sys.platform == "win32":
            result = os.system("nvidia-smi > NUL 2>&1")
        else:
            result = os.system("nvidia-smi > /dev/null 2>&1")
        if result == 0:
            return "gpu"
    except Exception:
        pass
    return "cpu"


def open_path_with_default_app(path: str):
    """Opens a file or folder with the platform default application."""
    os.startfile(path)
