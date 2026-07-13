# Terminal UI — introduction, main command list, folder openers, and app information display.

import os
import sys
import json
import pyfiglet
import webbrowser
from rich.text import Text
from rich.panel import Panel
from rich.align import Align
from rich.rule import Rule
from rich.table import Table
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.live import Live
from rich.group import Group
from mindcli import state
from mindcli.state import console
from mindcli.utils import (
    get_base_path, prompt_masked_windows, open_path_with_default_app
)
from mindcli.config_manager import (
    load_config, save_config_to_file, normalize_parameters,
    get_models_dir, sanitize_model_filename
)
from mindcli.ollama_utils import (
    start_ollama_process, ollama_is_available,
    ensure_ollama_or_warn, shutdown_ollama_everywhere, get_ollama_version
)
from mindcli.model_manager import (
    load_function, download_model_with_progress,
    delete_model_cmd, list_models_cmd
)
from mindcli.chat_manager import (
    list_chats_cmd, open_chat_cmd, remove_chat_cmd
)
from mindcli.memory_manager import (
    memory_add, memory_view, memory_remove, memory_clear
)
from mindcli.web_search import open_tavily_site


def open_models_folder():
    """Opens the Ollama local models directory in the file manager."""
    models_path = os.environ.get("OLLAMA_MODELS")
    if not models_path:
        home = os.path.expanduser("~")
        if sys.platform == "win32":
            models_path = os.path.join(home, ".ollama", "models")
        elif sys.platform == "darwin":
            models_path = os.path.join(home, ".ollama", "models")
        else:
            system_path = "/usr/share/ollama/.ollama/models"
            user_path = os.path.join(home, ".ollama", "models")
            if os.path.exists(system_path):
                models_path = system_path
            else:
                models_path = user_path

    if not os.path.exists(models_path):
        try:
            os.makedirs(models_path, exist_ok=True)
        except Exception:
            pass

    try:
        if os.path.exists(models_path):
            os.startfile(models_path)
            console.print(f"[green]Opening Ollama models folder: {models_path}[/green]")
        else:
            console.print(f"[red]Ollama models folder not found at: {models_path}[/red]")
    except Exception as e:
        console.print(f"[red]Error opening folder: {e}[/red]")


def open_models_folder_content():
    """Opens the application's models configuration directory."""
    models_path = os.path.join(get_base_path(), "models")
    os.makedirs(models_path, exist_ok=True)
    try:
        if os.path.exists(models_path):
            os.startfile(models_path)
            console.print(f"[green]Opening models folder: {models_path}[/green]")
        else:
            console.print(f"[red]Models folder not found at: {models_path}[/red]")
    except Exception as e:
        console.print(f"[red]Error opening folder: {e}[/red]")


def open_chats_folder():
    """Opens the chats directory in the file manager."""
    chats_path = os.path.join(get_base_path(), "chats")
    os.makedirs(chats_path, exist_ok=True)
    try:
        if os.path.exists(chats_path):
            os.startfile(chats_path)
            console.print(f"[green]Opening chats folder: {chats_path}[/green]")
        else:
            console.print(f"[red]Chats folder not found at: {chats_path}[/red]")
    except Exception as e:
        console.print(f"[red]Error opening folder: {e}[/red]")


def command_list_function():
    """Main menu command loop that handles all primary user commands."""
    console.print(
        Panel(
            "[cyan]More[/cyan] - view more commands.\n"
            "[green]Run[/green] - initialize ollama and start the chat.\n"
            "[red]Exit[/red] - close the app.",
            title="Main Command",
            border_style="yellow"
        )
    )
    console.print(Rule(style="white"))

    while True:
        command = console.input("[cyan]Command > [/cyan]").strip().lower()

        if command == "run":
            load_function()

        elif command == "exit":
            shutdown_ollama_everywhere()
            sys.exit()

        elif command == "":
            ensure_ollama_or_warn()

        elif command in ("more", "more commands"):
            console.print("[bold white]Models Edit[/bold white]")
            console.print(" • [cyan]Edit Base Prompt[/cyan] - modify the base prompt used by the AI.")
            console.print(" • [cyan]Change Parameters[/cyan] - modify model parameters (tokens, temp, etc.)")
            console.print()
            console.print("[bold white]Models Management[/bold white]")
            console.print(" • [cyan]Download[/cyan] - download models.")
            console.print(" • [cyan]Delete[/cyan] - remove a model.")
            console.print(" • [cyan]List[/cyan] - view installed models.")
            console.print()
            console.print("[bold white]Tavily Web search Commands[/bold white]")
            console.print(" • [cyan]API Config[/cyan] - configure the Tavily API key.")
            console.print(" • [cyan]API Clear[/cyan] - remove the saved Tavily API key.")
            console.print()
            console.print("[bold white]Chats Commands[/bold white]")
            console.print(" • [cyan]Chats List[/cyan] - list all saved chat files.")
            console.print(" • [cyan]Open Chat[/cyan] - display a saved chat in the terminal.")
            console.print(" • [cyan]Remove Chat[/cyan] - delete a saved chat file.")
            console.print()
            console.print("[bold white]Memory Management[/bold white]")
            console.print(" • [cyan]Memory Add[/cyan] - add a memory for the AI.")
            console.print(" • [cyan]Memory View[/cyan] - view all saved memories.")
            console.print(" • [cyan]Memory Remove[/cyan] - remove a specific memory.")
            console.print(" • [cyan]Memory Clear[/cyan] - clear all memories.")
            console.print()
            console.print("[bold white]App Commands[/bold white]")
            console.print(" • [cyan]Help[/cyan] - open the help file.")
            console.print(" • [cyan]License[/cyan] - view the license.")
            console.print(" • [cyan]Info[/cyan] - view app information.")
            continue

        elif command == "download":
            model_to_download = console.input("[cyan]Enter model name to download > [/cyan]").strip()
            if model_to_download:
                result = download_model_with_progress(model_to_download)
                if result:
                    console.print(f"[green]Model {model_to_download} downloaded[/green]")
            else:
                console.print("[yellow]Cancelled.[/yellow]")

        elif command == "delete":
            delete_model_cmd()

        elif command == "list":
            list_models_cmd()

        elif command == "info":
            ollama_version = get_ollama_version()
            info_text = (
                "Developer: LDM Dev\n"
                "App Version: 2.0\n"
                f"{ollama_version}\n"
                "Repository GitHub: https://github.com/Lorydima/MindCLI\n"
                "Website: https://Lorydima.github.io/MindCLI/\n"
                "License: GPL "
            )
            console.print(Panel(info_text, title="App Information", border_style="cyan"))

        elif command in ("folder", "models folder"):
            open_models_folder()

        elif command == "models folder":
            open_models_folder_content()

        elif command == "chats list":
            list_chats_cmd()

        elif command == "open chat":
            open_chat_cmd()

        elif command == "remove chat":
            remove_chat_cmd()

        elif command == "memory add":
            memory_add()

        elif command == "memory view":
            memory_view()

        elif command == "memory remove":
            memory_remove()

        elif command == "memory clear":
            memory_clear()

        elif command == "api config":
            open_tavily_site()
            key = prompt_masked_windows("[cyan]Enter Tavily API key > [/cyan]")
            if key:
                state.config_tavily_api_key = key
                save_config_to_file(state.config_model_path or "", state.config_base_prompt or state.DEFAULT_BASE_PROMPT)
                console.print("[green]Tavily API key saved.[/green]")
            else:
                console.print("[yellow]Operation cancelled.[/yellow]")

        elif command == "api clear":
            state.config_tavily_api_key = ""
            save_config_to_file(state.config_model_path or "", state.config_base_prompt or state.DEFAULT_BASE_PROMPT)
            console.print("[yellow]Tavily API key cleared.[/yellow]")

        elif command == "help":
            project_root = os.path.dirname(os.path.dirname(get_base_path()))
            help_path = os.path.join(project_root, "MindCLI_UserGuide.pdf")
            try:
                if os.path.exists(help_path):
                    os.startfile(help_path)
                    console.print("[green]Opening MindCLI_UserGuide.pdf[/green]")
                else:
                    console.print(f"[red]MindCLI_UserGuide.pdf not found at project root[/red]")
            except Exception as e:
                console.print(f"[red]Error opening help file: {e}[/red]")

        elif command == "license":
            project_root = os.path.dirname(os.path.dirname(get_base_path()))
            license_path = os.path.join(project_root, "LICENSE.txt")
            try:
                if os.path.exists(license_path):
                    open_path_with_default_app(license_path)
                    console.print("[green]Opening LICENSE.txt[/green]")
                else:
                    console.print(f"[red]LICENSE.txt not found at project root[/red]")
            except Exception as e:
                console.print(f"[red]Error opening license: {e}[/red]")

        elif command == "edit base prompt":
            model_name = console.input("[cyan]Enter model name to edit base prompt > [/cyan]").strip()
            if not model_name:
                console.print("[yellow]Operation cancelled.[/yellow]")
                continue
            models_dir = get_models_dir()
            model_cfg_filename = sanitize_model_filename(model_name)
            model_cfg_path = os.path.join(models_dir, model_cfg_filename)

            current_prompt = "You are a helpful coding assistant. Answer the user's questions clearly and provide code blocks when necessary."
            if os.path.exists(model_cfg_path):
                try:
                    with open(model_cfg_path, "r", encoding="utf-8") as f:
                        m_cfg = json.load(f)
                        current_prompt = m_cfg.get("base_prompt", current_prompt)
                except Exception:
                    pass

            console.print(f"[cyan]Current prompt: {current_prompt}[/cyan]")
            new_prompt = console.input("[cyan]Enter new base prompt > [/cyan]").strip()
            if new_prompt:
                current_params = state.DEFAULT_PARAMS.copy()
                current_device = "cpu"
                if os.path.exists(model_cfg_path):
                    try:
                        with open(model_cfg_path, "r", encoding="utf-8") as f:
                            m_cfg = json.load(f)
                            current_params = m_cfg.get("parameters", current_params)
                            current_device = m_cfg.get("device", current_device)
                    except Exception:
                        pass

                if save_config_to_file(model_name, new_prompt, current_params, device=current_device):
                    console.print("[green]Base prompt updated![/green]")
            else:
                console.print("[yellow]Operation cancelled.[/yellow]")

        elif command == "change parameters":
            model_name = console.input("[cyan]Enter model name to change parameters > [/cyan]").strip()
            if not model_name:
                console.print("[yellow]Operation cancelled.[/yellow]")
                continue
            models_dir = get_models_dir()
            model_cfg_filename = sanitize_model_filename(model_name)
            model_cfg_path = os.path.join(models_dir, model_cfg_filename)

            current_params = state.DEFAULT_PARAMS.copy()
            if os.path.exists(model_cfg_path):
                try:
                    with open(model_cfg_path, "r", encoding="utf-8") as f:
                        m_cfg = json.load(f)
                        current_params = m_cfg.get("parameters", current_params)
                except Exception:
                    pass

            console.print("[cyan]Enter new parameters (press Enter for current/default values):[/cyan]")
            params = current_params.copy()
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

                current_device = "cpu"
                if os.path.exists(model_cfg_path):
                    try:
                        with open(model_cfg_path, "r", encoding="utf-8") as f:
                            m_cfg = json.load(f)
                            current_device = m_cfg.get("device", current_device)
                    except Exception:
                        pass

                if save_config_to_file(model_name, state.config_base_prompt, params, device=current_device):
                    console.print("[green]Parameters updated successfully![/green]")
            except ValueError:
                console.print("[red]Invalid input. Operation cancelled.[/red]")

        else:
            console.print("[white]-[white] [red]Unknown command[/red]")


def introduction():
    """Displays the main banner and introduction of the app, then starts the command loop."""
    banner = pyfiglet.figlet_format("MindCLI")
    version_text = Text("\nVersion 2.0", style="bold", justify="center")
    banner_content = Group(
        banner.rstrip(),
        version_text
    )

    banner_panel = Panel(banner_content, style="red", expand=False)

    console.print(Align.center(banner_panel))
    console.print(Rule(style="white"))

    start_ollama_process()
    if not ollama_is_available():
        console.print(
            "[red]Ollama not detected.[/red]\n"
            "[yellow]Download it here:[/yellow] https://ollama.com/download\n"
            "[yellow]Main site:[/yellow] https://ollama.com/"
        )
    load_config()
    command_list_function()
