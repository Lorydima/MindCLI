# Ollama process management and AI response generation.

import sys
import os
import time
import signal
import atexit
import ollama
from mindcli import state
from mindcli.state import console


def ollama_is_available():
    """Returns True when the Ollama API is reachable."""
    try:
        ollama.list()
        return True
    except Exception:
        return False


def get_ollama_version() -> str:
    """Returns the installed Ollama version string if available."""
    try:
        if sys.platform == "win32":
            import subprocess
            result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
            output = result.stdout.strip()
        else:
            with os.popen("ollama --version") as pipe:
                output = pipe.read().strip()
        return output or "N/A"
    except Exception:
        return "N/A"


def start_ollama_process():
    """Starts Ollama in the background if it is not already reachable."""
    if ollama_is_available():
        return True

    try:
        if sys.platform == "win32":
            os.system("start /B ollama serve > NUL 2>&1")
        else:
            os.system("ollama serve > /dev/null 2>&1 &")
    except Exception:
        return False

    for _ in range(30):
        time.sleep(0.5)
        if ollama_is_available():
            return True

    return False


def kill_all_ollama_processes():
    """Best-effort kill for all Ollama processes."""
    try:
        if sys.platform == "win32":
            os.system("taskkill /IM ollama.exe /T /F > NUL 2>&1")
        else:
            os.system("pkill ollama > /dev/null 2>&1")
    except Exception:
        pass


def close_ollama_process():
    """Best-effort shutdown for an Ollama process started by this app."""
    kill_all_ollama_processes()


def shutdown_ollama_everywhere():
    """Stops Ollama processes and clears local state."""
    close_ollama_process()
    kill_all_ollama_processes()


def _handle_shutdown_signal(signum, frame):
    """Handles OS signals (SIGINT, SIGTERM, SIGHUP) to shut down Ollama gracefully."""
    shutdown_ollama_everywhere()
    raise SystemExit(0)


# Register signal handlers and cleanup hooks
for _sig in ("SIGINT", "SIGTERM", "SIGHUP"):
    if hasattr(signal, _sig):
        signal.signal(getattr(signal, _sig), _handle_shutdown_signal)

atexit.register(close_ollama_process)
atexit.register(kill_all_ollama_processes)


def generate_ai_response(full_prompt: str) -> str | None:
    """Generates a response from Ollama and returns the cleaned text."""
    ai_response = None

    # Build generation options from current config
    options = {
        "num_predict": state.config_parameters.get("num_predict", 2048),
        "temperature": state.config_parameters.get("temperature", 0.5),
        "top_p": state.config_parameters.get("top_p", 0.9),
        "repeat_penalty": state.config_parameters.get("repeat_penalty", 1.1),
    }
    if "num_ctx" in state.config_parameters:
        options["num_ctx"] = state.config_parameters["num_ctx"]

    with console.status("[yellow]Thinking...[/yellow]", spinner="dots"):
        try:
            response = ollama.generate(
                model=state.active_model,
                prompt=full_prompt,
                options=options
            )

            raw = response.response if hasattr(response, 'response') else response.get('response', '')
            from mindcli.utils import sanitize_response
            text = sanitize_response(str(raw or ""))

            # Remove common AI response prefixes
            prefixes_to_remove = ["AI:", "AI Assistant:", "Assistant:", "Response:"]
            for prefix in prefixes_to_remove:
                if text.startswith(prefix):
                    text = text[len(prefix):].strip()
                    break

            ai_response = text
            state.chat_history.append(f"{state.active_model} > {ai_response}")

        except Exception as e:
            state.console.print(f"[red]Error generating response: {str(e)}[/red]")

    return ai_response


def ensure_ollama_or_warn() -> bool:
    """Checks Ollama availability and prints a helpful message when missing."""
    if start_ollama_process():
        console.print("[green]Ollama is available.[/green]")
        return True

    console.print(
        "[red]Ollama not detected.[/red]\n"
        "[yellow]Download it here:[/yellow] https://ollama.com/download\n"
        "[yellow]Main site:[/yellow] https://ollama.com/"
    )
    return False
