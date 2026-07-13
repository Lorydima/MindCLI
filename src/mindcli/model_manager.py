# Model management — download, delete, list, and switch between Ollama models.

import os
import json
import time
import ollama
from mindcli import state
from mindcli.state import console
from mindcli.utils import get_base_path
from mindcli.config_manager import (
    sanitize_model_filename, get_model_base_name, normalize_parameters,
    get_models_dir, load_config, save_config_to_file
)
from mindcli.ollama_utils import (
    ollama_is_available, start_ollama_process, ensure_ollama_or_warn,
    shutdown_ollama_everywhere, generate_ai_response, get_ollama_version
)
from mindcli.chat_manager import (
    chat_command_list_function, chat_loop
)


def download_model_with_progress(model_name: str) -> bool:
    """Downloads an Ollama model displaying a spinner, then prompts for config setup."""
    try:
        if not ollama_is_available():
            console.print("[red]Error: Ollama is not reachable.[/red]")
            return False

        with console.status(f"[yellow]Downloading model {model_name}...[/yellow]", spinner="dots"):
            for chunk in ollama.pull(model_name, stream=True):
                pass

        console.print(f"[yellow]Model {model_name} downloaded and ready to use[/yellow]")

        # Prompt for base prompt
        base_prompt = console.input("[cyan]Enter base prompt (press Enter for default) > [/cyan]").strip()
        if not base_prompt:
            base_prompt = "You are a helpful coding assistant. Answer the user's questions clearly and provide code blocks when necessary."
        console.print("[cyan]Enter parameters (press Enter for default values):[/cyan]")
        params = state.DEFAULT_PARAMS.copy()

        # Prompt for AI parameters
        try:
            mt = console.input(f"[cyan]Num Predict (Current {params.get('num_predict', 2048)}) > [/cyan]").strip()
            if mt: params['num_predict'] = int(mt)
            tmp = console.input(f"[cyan]Temperature (Current {params.get('temperature', 0.5)}) > [/cyan]").strip()
            if tmp: params['temperature'] = float(tmp)
            tp = console.input(f"[cyan]Top P (Current {params.get('top_p', 0.9)}) > [/cyan]").strip()
            if tp: params['top_p'] = float(tp)
            rp = console.input(f"[cyan]Repeat Penalty (Current {params.get('repeat_penalty', 1.1)}) > [/cyan]").strip()
            if rp: params['repeat_penalty'] = float(rp)
            ctx = console.input(f"[cyan]Num Ctx (Current {params.get('num_ctx', 4096)}) > [/cyan]").strip()
            if ctx: params['num_ctx'] = int(ctx)
        except ValueError:
            console.print("[yellow]Invalid input, using default parameters.[/yellow]")
            params = state.DEFAULT_PARAMS.copy()

        # Prompt for hardware device
        console.print("[cyan]Select device for this model:[/cyan]")
        console.print(" 1. CPU (default)")
        console.print(" 2. GPU (NVIDIA)")
        device_choice = console.input("[cyan]Enter choice (1 or 2, press Enter for CPU) > [/cyan]").strip()
        device = "gpu" if device_choice == "2" else "cpu"

        if save_config_to_file(model_name, base_prompt, params, device=device):
            console.print("[green]Model configuration saved successfully![/green]")

        return True
    except Exception as e:
        console.print(f"[red]Error downloading model: {e}[/red]")
        return False


def delete_model_cmd():
    """Prints the list of installed models and lets the user choose one to delete."""
    try:
        if not ollama_is_available():
            console.print("[red]Error: Ollama is not reachable.[/red]")
            return

        # Fetch installed models
        with console.status("[cyan]Retrieving models list...[/cyan]", spinner="dots"):
            models_list = ollama.list()
            installed = [m.model for m in models_list.models if "-cloud" not in m.model.lower()]

        if not installed:
            console.print("[yellow]No local models found to delete.[/yellow]")
            return

        console.print("[bold yellow]Installed Local Models:[/bold yellow]")
        for m in installed:
            console.print(f" - [bold white]{m}[/bold white]")

        model_to_delete = console.input("[cyan]Enter the name of the model to delete > [/cyan]").strip()
        if not model_to_delete:
            console.print("[yellow]Cancelled.[/yellow]")
            return

        # Match model by name or base name
        matched_model = None
        for m in installed:
            if m == model_to_delete or m.split(":")[0] == model_to_delete:
                matched_model = m
                break

        if not matched_model:
            console.print(f"[red]Error: Model '[bold]{model_to_delete}[/bold]' is not installed.[/red]")
            return

        confirm = console.input(f"[red]Are you sure you want to delete '[bold]{matched_model}[/bold]'? (y/n) > [/red]").strip().lower()
        if confirm == 'y':
            with console.status(f"[red]Deleting model '[bold]{matched_model}[/bold]'...[/red]", spinner="dots"):
                ollama.delete(model=matched_model)
            console.print(f"[green]Model '[bold]{matched_model}[/bold]' deleted successfully.[/green]")

            # Handle fallback if active model was deleted
            active_base = get_model_base_name(state.config_model_path)
            deleted_base = get_model_base_name(matched_model)
            if state.config_model_path == matched_model or active_base == deleted_base:
                fallback_model = next((m for m in installed if m != matched_model), "")
                if fallback_model:
                    console.print(f"[yellow]Warning: You deleted the active model. Switching to '[bold]{fallback_model}[/bold]'.[/yellow]")
                    state.config_model_path = fallback_model
                    save_config_to_file(state.config_model_path, state.config_base_prompt or state.DEFAULT_BASE_PROMPT)
                else:
                    console.print("[yellow]Warning: You deleted the last local model. Clearing the active model.[/yellow]")
                    state.config_model_path = ""
                    save_config_to_file("", state.config_base_prompt or state.DEFAULT_BASE_PROMPT)
        else:
            console.print("[yellow]Cancelled.[/yellow]")
    except Exception as e:
        console.print(f"[red]Error deleting model: {e}[/red]")


def list_models_cmd():
    """Displays a Rich table listing all installed local models and their sizes."""
    try:
        if not ollama_is_available():
            console.print("[red]Error: Ollama is not reachable.[/red]")
            return

        with console.status("[cyan]Retrieving models list...[/cyan]", spinner="dots"):
            models_list = ollama.list()
            installed = [m for m in models_list.models if "-cloud" not in m.model.lower()]

        if not installed:
            console.print("[yellow]No local models found.[/yellow]")
            return

        from rich.table import Table
        from rich.align import Align
        table = Table(title="Local Ollama Models List", border_style="cyan")
        table.add_column("Model Name", style="white bold")
        table.add_column("Weight (Size)", style="yellow")

        for m in installed:
            size_gb = f"{m.size / (1024**3):.2f} GB"
            table.add_row(m.model, size_gb)

        console.print(Align.center(table))
    except Exception as e:
        console.print(f"[red]Error listing models: {e}[/red]")


def change_model_function():
    """Switches the active AI model during a chat session."""
    try:
        with console.status("[cyan]Retrieving models list...[/cyan]", spinner="dots"):
            models_list = ollama.list()
            installed = [m.model for m in models_list.models if "-cloud" not in m.model.lower()]

        if not installed:
            console.print("[yellow]No local models found. Please download a model first.[/yellow]")
            return

        # Display available models
        console.print("[bold yellow]Available Local Models:[/bold yellow]")
        for i, m in enumerate(installed, 1):
            console.print(f" [bold white]{i}. {m}[/bold white]")

        choice = console.input("[cyan]Enter the number or name of the model to switch to > [/cyan]").strip()
        if not choice:
            console.print("[yellow]Cancelled.[/yellow]")
            return

        # Parse selection (number or name)
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(installed):
                model_name = installed[idx]
            else:
                console.print("[red]Invalid selection.[/red]")
                return
        else:
            model_name = None
            for m in installed:
                if m == choice or m.split(":")[0] == choice:
                    model_name = m
                    break
            if not model_name:
                console.print(f"[red]Model '[bold]{choice}[/bold]' not found.[/red]")
                return

        # Load model-specific configuration
        models_dir = get_models_dir()
        model_cfg_filename = sanitize_model_filename(model_name)
        model_cfg_path = os.path.join(models_dir, model_cfg_filename)

        model_config = {}
        if os.path.exists(model_cfg_path):
            try:
                with open(model_cfg_path, "r", encoding="utf-8") as f:
                    model_config = json.load(f)
            except Exception as e:
                console.print(f"[yellow]Warning: Could not load config for {model_name}: {e}[/yellow]")

        # Update global state
        state.config_model_path = model_name
        state.config_base_prompt = model_config.get("base_prompt", state.DEFAULT_BASE_PROMPT)
        state.config_parameters = normalize_parameters(model_config.get("parameters", state.DEFAULT_PARAMS.copy()))
        state.config_device = model_config.get("device", state.config_device)

        state.active_model = model_name
        state.active_base_prompt = state.config_base_prompt
        state.chat_history = []
        state.attached_file_content = None
        state.attached_filename = None

        save_config_to_file(model_name, state.config_base_prompt, state.config_parameters, device=state.config_device)

        console.print(f"[green]Model switched to '[bold]{state.active_model}[/bold]' successfully! Chat history cleared.[/green]")

    except Exception as e:
        console.print(f"[red]Error changing model: {str(e)}[/red]")
        return


def load_function():
    """Loads a selected Ollama model and starts the interactive chat loop."""
    state.active_model = None
    state.active_base_prompt = None
    state.ollama_ready = False
    state.attached_file_content = None
    state.attached_filename = None

    try:
        # Fetch available models
        with console.status("[cyan]Retrieving models list...[/cyan]", spinner="dots"):
            models_list = ollama.list()
            installed = [m.model for m in models_list.models if "-cloud" not in m.model.lower()]

        if not installed:
            console.print("[yellow]No local models found. Please download a model first.[/yellow]")
            return

        # Display models for selection
        console.print("[bold yellow]Available Local Models:[/bold yellow]")
        for i, m in enumerate(installed, 1):
            console.print(f" [bold white]{i}. {m}[/bold white]")

        choice = console.input("[cyan]Enter the number or name of the model to run > [/cyan]").strip()
        if not choice:
            console.print("[yellow]Cancelled.[/yellow]")
            return

        # Parse selection
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(installed):
                model_name = installed[idx]
            else:
                console.print("[red]Invalid selection.[/red]")
                return
        else:
            model_name = None
            for m in installed:
                if m == choice or m.split(":")[0] == choice:
                    model_name = m
                    break
            if not model_name:
                console.print(f"[red]Model '[bold]{choice}[/bold]' not found.[/red]")
                return

        # Load model config
        models_dir = get_models_dir()
        model_cfg_filename = sanitize_model_filename(model_name)
        model_cfg_path = os.path.join(models_dir, model_cfg_filename)

        model_config = {}
        if os.path.exists(model_cfg_path):
            try:
                with open(model_cfg_path, "r", encoding="utf-8") as f:
                    model_config = json.load(f)
            except Exception as e:
                console.print(f"[yellow]Warning: Could not load config for {model_name}: {e}[/yellow]")

        # Apply configuration
        state.config_model_path = model_name
        state.config_base_prompt = model_config.get("base_prompt", state.DEFAULT_BASE_PROMPT)
        state.config_parameters = normalize_parameters(model_config.get("parameters", state.DEFAULT_PARAMS.copy()))
        state.config_device = model_config.get("device", state.config_device)

        state.active_model = model_name
        state.active_base_prompt = state.config_base_prompt

        # Start Ollama process
        with console.status("[green]Starting Ollama process...[/green]", spinner="dots"):
            started = ensure_ollama_or_warn()

        if not started:
            return

        state.ollama_ready = True
        console.print(f"[green]Model '[bold]{state.active_model}[/bold]' is active and ready.[/green]")

        # Enter chat mode
        chat_command_list_function()
        chat_loop()

    except Exception as e:
        console.print(f"[red]Error during startup: {str(e)}[/red]")
        return
