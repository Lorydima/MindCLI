# MindCLI V1.0 Source Code Date: 00/00/0000 Dev: LDM Dev.

'''
MindCLI is a command-line interface tool designed to facilitate interaction with AI models.
'''

# Suppress dependency warnings
import warnings
warnings.filterwarnings("ignore", message=".*doesn't match a supported version!.*")
warnings.filterwarnings("ignore", module=r"requests.*")

# Library for App Dev
from rich.console import Console, Group
from rich.panel import Panel
from rich.align import Align
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.syntax import Syntax
from gpt4all import GPT4All
from datetime import datetime
import time
import pyfiglet
import json
import os
import sys
import contextlib
import pyperclip
import pypdf

# Get base path
def get_base_path():
    """Returns the base path for config and resources, adjusting for PyInstaller."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

# Console Setup
console = Console()

# Global Config State
config_model_path = None
config_base_prompt = None
config_user_name = None
config_parameters = {}

# Default AI Parameters
DEFAULT_PARAMS = {
    "max_tokens": 2048,
    "temp": 0.4,
    "top_p": 0.9,
    "repeat_penalty": 1.1
}

# Chat history
chat_history = []

# Runtime State
active_model = None
active_base_prompt = None
gpt4all_model = None
attached_file_content = None
config_download_source = "N/A"
config_device = "cpu"

# suppress_stderr_fd
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

# load_config
def load_config():
    """Loads config settings like model_path and base_prompt."""
    global config_model_path, config_base_prompt, config_user_name, config_parameters, config_download_source, config_device
    config_path = os.path.join(get_base_path(), "config.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            try:
                config = json.load(f)
            except json.JSONDecodeError:
                config = {}
    except FileNotFoundError:
        config = {}

    config_model_path = config.get("model_path")
    config_base_prompt = config.get("base_prompt")
    config_download_source = config.get("download_source", "N/A")
    config_device = config.get("device", "cpu")
    config_parameters = config.get("parameters", DEFAULT_PARAMS.copy())

    if not (config_model_path and config_base_prompt):
        setup()

# save_config_to_file
def save_config_to_file(model_path, base_prompt, parameters=None, download_source=None, device=None):
    """Saves the given values to config.json."""
    global config_parameters, config_download_source, config_device
    if parameters is None:
        parameters = config_parameters
    if download_source is None:
        download_source = config_download_source
    if device is None:
        device = config_device
        
    config_path = os.path.join(get_base_path(), "config.json")
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
        config_parameters = parameters
        config_download_source = download_source
        config_device = device
        return True
    except Exception as e:
        console.print(f"[red]Error saving config: {e}[/red]")
        return False


# view_model_info_function
def view_model_info_function():
    """Displays information about the active model, parameters, and base prompt."""
    try:
        config_path = os.path.join(get_base_path(), "config.json")
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        model_path = config.get("model_path", "N/A")
        base_prompt = config.get("base_prompt", "N/A")
        download_source = config.get("download_source", "N/A")
        device = config.get("device", "cpu")
        
        curr = os.path.abspath(get_base_path())
        project_root = None
        for _ in range(6):
            if os.path.isdir(os.path.join(curr, "Models")) or os.path.isdir(os.path.join(curr, "models")):
                project_root = curr
                break
            parent = os.path.dirname(curr)
            if parent == curr:
                break
            curr = parent
        
        if project_root is None:
            project_root = os.path.abspath(os.path.join(get_base_path(), ".."))
        
        if os.path.isabs(model_path):
            full_path = model_path
        else:
            full_path = os.path.join(project_root, "Models", model_path)
        
        size_gb = "N/A"
        if os.path.exists(full_path):
            size_bytes = os.path.getsize(full_path)
            size_gb = f"{size_bytes / (1024**3):.2f} GB"
        
        table = Table(title="Model Information", border_style="cyan")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Model File", os.path.basename(model_path))
        table.add_row("File Size", size_gb)
        table.add_row("Model Path", full_path)
        table.add_row("Download Source", download_source)
        
        console.print(Align.center(table))
        
        p_table = Table(title="AI Parameters", border_style="yellow")
        p_table.add_column("Parameter", style="cyan")
        p_table.add_column("Value", style="green")
        
        params = config.get("parameters", DEFAULT_PARAMS)
        for k, v in params.items():
            p_table.add_row(k.replace("_", " ").title(), str(v))
        
        p_table.add_row("Hardware Mode", "NVIDIA GPU" if device == "gpu" else "CPU")
        
        console.print(Align.center(p_table))
        
        console.print(Panel(base_prompt, title="Base Prompt", border_style="cyan"))
    except Exception as e:
        console.print(f"[red]Error reading model info: {e}[/red]")


# sanitize_response
def sanitize_response(text: str) -> str:
    """Sanitizes text output from the AI response."""
    if not text:
        return ""
    t = text.strip()
    return t.strip()

# typing_effect
def typing_effect(text: str):
    """Crea un effetto di digitazione e formatta correttamente i blocchi di codice Markdown."""
    if not text:
        return

    prefix = "[cyan]AI  >[/cyan]"
    segments = text.split("```")
    
    current_elements = []
    
    with Live(console=console, refresh_per_second=30) as live:
        for i, segment in enumerate(segments):
            if i % 2 == 0:
                current_text = ""
                for char in segment:
                    current_text += char
                    temp_group = Group(*current_elements, Text(current_text))
                    table = Table.grid(padding=(0, 1))
                    table.add_column(justify="left", width=5, no_wrap=True)
                    table.add_column(ratio=1)
                    table.add_row(prefix, temp_group)
                    live.update(table)
                    time.sleep(0.005)
                if segment:
                    current_elements.append(Text(segment))
            else:
                lines = segment.split("\n", 1)
                lang = lines[0].strip() or "python"
                code = lines[1] if len(lines) > 1 else ""
                
                current_code = ""
                for char in code:
                    current_code += char
                    syntax = Syntax(current_code, lang, theme="monokai", line_numbers=True, word_wrap=True)
                    temp_group = Group(*current_elements, syntax)
                    table = Table.grid(padding=(0, 1))
                    table.add_column(justify="left", width=5, no_wrap=True)
                    table.add_column(ratio=1)
                    table.add_row(prefix, temp_group)
                    live.update(table)
                    time.sleep(0.002)
                if code:
                    current_elements.append(Syntax(code, lang, theme="monokai", line_numbers=True, word_wrap=True))
    
    console.print()

# open_models_folder
def open_models_folder():
    """Opens the local Models directory."""
    curr = os.path.abspath(get_base_path())
    project_root = None
    for _ in range(6):
        if os.path.isdir(os.path.join(curr, "Models")) or os.path.isdir(os.path.join(curr, "models")):
            project_root = curr
            break
        parent = os.path.dirname(curr)
        if parent == curr:
            break
        curr = parent
    
    if project_root is None:
        project_root = os.path.abspath(os.path.join(get_base_path(), ".."))
    
    models_path = os.path.join(project_root, "Models")
    if not os.path.exists(models_path):
        models_path = os.path.join(project_root, "models")
        
    try:
        if os.path.exists(models_path):
            os.startfile(models_path)
            console.print(f"[green]Opening Models folder[/green]")
        else:
            console.print(f"[red]Models folder not found at: {models_path}[/red]")
    except Exception as e:
        console.print(f"[red]Error opening folder: {e}[/red]")


# introduction
def introduction():
    """Displays the main banner and introduction of the app."""
    banner = pyfiglet.figlet_format("MindCLI")

    console.print(Align.center(f"[red]{banner}[/red]"))
    console.print(Rule(style="white"))

    load_config()
    command_list_function()


# setup
def setup():
    """Guides the user through setting up model and base prompt."""
    global config_model_path, config_base_prompt, config_parameters, config_download_source, config_device

    console.print(Align.center("[yellow]Setup Mode[/yellow]"))
    print()
    console.print(Align.center("[yellow]For help with the setup, you can refer to the MindCLI_HELP.txt file in the program's folder.[/yellow]"))
    print()
    config_model_path = console.input("[cyan]Insert Model file name (e.g. my-model.gguf) or path > [/cyan]").strip()
    print()

    config_download_source = console.input("[cyan]Insert Download Source (URL or Name, optional) > [/cyan]").strip() or "N/A"
    print()

    console.print("[cyan]Do you have an NVIDIA GPU? (y/n)[/cyan]")
    gpu_choice = console.input("> ").strip().lower()
    config_device = "gpu" if gpu_choice == 'y' else "cpu"
    print()
    
    console.print("[cyan]Enter the base prompt. Finish with an empty line.[/cyan]")
    lines = []
    while True:
        l = console.input()
        if l == "":
            break
        lines.append(l)
    config_base_prompt = "\n".join(lines).strip()
    print()
    
    console.print("[cyan]Do you want to modify AI parameters (max_tokens, temp, etc.)? (y/n)[/cyan]")
    choice = console.input("> ").strip().lower()
    print()
    
    params = DEFAULT_PARAMS.copy()
    if choice == 'y':
        try:
            mt = console.input(f"[cyan]Max Tokens (Default {params['max_tokens']}) > [/cyan]").strip()
            if mt: params['max_tokens'] = int(mt)
            print()
            
            tmp = console.input(f"[cyan]Temperature (Default {params['temp']}) > [/cyan]").strip()
            if tmp: params['temp'] = float(tmp)
            print()
            
            tp = console.input(f"[cyan]Top P (Default {params['top_p']}) > [/cyan]").strip()
            if tp: params['top_p'] = float(tp)
            print()
            
            rp = console.input(f"[cyan]Repeat Penalty (Default {params['repeat_penalty']}) > [/cyan]").strip()
            if rp: params['repeat_penalty'] = float(rp)
            print()
        except ValueError:
            console.print("[red]Invalid input, using defaults for remaining values.[/red]")
            print()

    if save_config_to_file(config_model_path, config_base_prompt, params, config_download_source, config_device):
        console.print(f"[green]Config saved successfully![/green]")
        print()
        console.print(Align.center("[yellow]Setup Summary[/yellow]"))
        view_model_info_function()
        print()
        console.input("[green]Press Enter to close the program...[/green]")
        exit()
    else:
        console.print(f"[red]Failed to save config.[/red]")

# load_function
def load_function():
    """Loads the AI model and starts the chat loop."""
    global active_model, active_base_prompt, gpt4all_model, attached_file_content

    active_model = None
    active_base_prompt = None
    gpt4all_model = None
    attached_file_content = None

    model_path = config_model_path

    curr = os.path.abspath(get_base_path())
    project_root = None
    for _ in range(6):
        if os.path.isdir(os.path.join(curr, "Models")) or os.path.isdir(os.path.join(curr, "models")):
            project_root = curr
            break
        parent = os.path.dirname(curr)
        if parent == curr:
            break
        curr = parent

    if project_root is None:
        project_root = os.path.abspath(os.path.join(get_base_path(), ".."))

    tried = []

    if not model_path:
        console.print("[red]Error: model_path not set in config.json[/red]")
        return

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
        console.print(f"[red]Error loading model: Model file does not exist: {candidate}[/red]")
        console.print("[cyan]Tried these paths:[/cyan]")
        for p in tried:
            console.print(f" - {p}")
        return

    try:
        model_dir = os.path.dirname(candidate)
        model_file = os.path.basename(candidate)

        init_exc = {}

        def init_model():
            global gpt4all_model
            try:
                with suppress_stderr_fd():
                    gpt4all_model = GPT4All(
                        model_name=model_file,
                        model_path=model_dir,
                        allow_download=False,
                        device=config_device
                    )
            except Exception as e:
                init_exc['e'] = e

        with console.status("[green]starting AI[/green]", spinner="dots"):
            init_model()
            time.sleep(0.8)

        if 'e' in init_exc:
            raise init_exc['e']

        console.print("[green]AI started[/green]")
        
        model_file = os.path.basename(candidate)
        active_model = model_file
        active_base_prompt = config_base_prompt

        chat_command_list_function()
        chat_loop()

    except Exception as e:
        console.print(f"[red]Error loading model: {str(e)}[/red]")
        return


# command_list_function
def command_list_function():
    """Main menu command loop."""
    global config_model_path, config_base_prompt
    
    console.print(
        Panel(
            "[cyan]View Model Info[/cyan] - view model details, size, base prompt and AI parameters.\n"
            "[cyan]More Commands[/cyan] - view additional options.\n"
            "[green]Start AI[/green] - initialize the AI engine and start the chat.\n"
            "[red]Exit[/red] - close the application.",
            title="Main Command",
            border_style="yellow"
        )
    )
    console.print(Rule(style="white"))
    
    while True:
        print()
        command = console.input("[cyan]Command > [/cyan]").strip().lower()

        if command == "start ai":
            load_function()
            break

        elif command == "exit":
            exit()

        elif command == "more commands":
            print()
            console.print(" • [cyan]Edit Base Prompt[/cyan] - modify the base prompt used by the AI.")
            console.print(" • [cyan]Change Model[/cyan] - switch to a different AI model.")
            console.print(" • [cyan]Change Parameters[/cyan] - modify model parameters (tokens, temp, etc.).")
            console.print(" • [cyan]Models Folder[/cyan] - open the models directory.")
            console.print(" • [cyan]Help[/cyan] - open the help file.")
            console.print(" • [cyan]License[/cyan] - view the license.")
            console.print(" • [cyan]Info[/cyan] - view app information.")
            continue

        elif command == "info":
            info_text = (
                "Developer: LDM Dev\n"
                "App Version: 1.0\n"
                "Repository GitHub: https://github.com/Lorydima/MindCLI\n"
                "Website: https://Lorydima.github.io/MindCLI/"
            )
            console.print(Panel(info_text, title="App Information", border_style="cyan"))

        elif command == "view model info":
            view_model_info_function()

        elif command == "models folder":
            open_models_folder()

        elif command == "help":
            help_path = os.path.join(get_base_path(), "MindCLI_HELP.txt")
            try:
                if os.path.exists(help_path):
                    os.startfile(help_path)
                    console.print("[green]Opening MindCLI_HELP.txt[/green]")
                else:
                    console.print(f"[red]MindCLI_HELP.txt not found in the program folder[/red]")
            except Exception as e:
                console.print(f"[red]Error opening help file: {e}[/red]")

        elif command == "license":
            license_path = os.path.join(get_base_path(), "LICENSE.txt")
            try:
                if os.path.exists(license_path):
                    os.startfile(license_path)
                    console.print("[green]Opening LICENSE.txt[/green]")
                else:
                    console.print(f"[red]LICENSE.txt not found[/red]")
            except Exception as e:
                console.print(f"[red]Error opening license: {e}[/red]")

        elif command == "edit base prompt":
            new_prompt = console.input("[cyan]Enter new base prompt > [/cyan]").strip()
            if new_prompt:
                if save_config_to_file(config_model_path, new_prompt):
                    config_base_prompt = new_prompt
                    console.print("[green]Base prompt updated![/green]")
            else:
                console.print("[yellow]Operation cancelled.[/yellow]")

        elif command == "change model":
            new_model = console.input("[cyan]Enter new model name (GGUF format) > [/cyan]").strip()
            if new_model:
                if save_config_to_file(new_model, config_base_prompt):
                    config_model_path = new_model
                    console.print(f"[green]Model updated to: {new_model}[/green]")
            else:
                console.print("[yellow]Operation cancelled.[/yellow]")

        elif command == "change parameters":
            params = config_parameters.copy()
            try:
                mt = console.input(f"[cyan]Max Tokens (Current {params['max_tokens']}) > [/cyan]").strip()
                if mt: params['max_tokens'] = int(mt)
                
                tmp = console.input(f"[cyan]Temperature (Current {params['temp']}) > [/cyan]").strip()
                if tmp: params['temp'] = float(tmp)
                
                tp = console.input(f"[cyan]Top P (Current {params['top_p']}) > [/cyan]").strip()
                if tp: params['top_p'] = float(tp)
                
                rp = console.input(f"[cyan]Repeat Penalty (Current {params['repeat_penalty']}) > [/cyan]").strip()
                if rp: params['repeat_penalty'] = float(rp)
                
                if save_config_to_file(config_model_path, config_base_prompt, params):
                    console.print("[green]Parameters updated successfully![/green]")
            except ValueError:
                console.print("[red]Invalid input. Operation cancelled.[/red]")

        else:
            console.print("[white]-[white] [red]Unknown command[/red]")

# chat_command_list_function
def chat_command_list_function():
    """Displays commands available in the chat session."""
    print("\n")
    console.print(Rule("Chat", style="cyan"))
    console.print(
        Panel(
            "[cyan]Save[/cyan] - save the current chat session.\n"
            "[cyan]Copy[/cyan] - copy the last AI response to clipboard.\n"
            "[cyan]Add[/cyan] - attach a .txt or .pdf file for context.\n"
            "[cyan]Remove[/cyan] - remove the attached file.\n"
            "[red]Exit[/red] - exit the chat session and return to the main command menu.",
            title="Commands",
            border_style="yellow"
        )
    )
    
    print()
    
    warning = Text("WARNING: AI models can produce incorrect responses, so verify the responses.", style="red bold underline")
    console.print(warning)
    print()
    note = Text("Note: ", style="yellow bold underline")
    note.append("Response quality, speed, and language depend on ", style="white")
    note.append("the model chosen, your PC hardware, the base prompt and AI parameters", style="yellow bold underline")
    note.append(".", style="white")
    console.print(note)
    
    print()
    
    model_text = Text("Model active: ", style="yellow")
    model_text.append(active_model, style="green bold")
    console.print(model_text)
    
    print()
    
    attached_text = Text("Attached File: ", style="yellow")
    attached_text.append("No", style="red")
    console.print(attached_text)
    
    print()


# save_chat
def save_chat():
    """Saves the current chat history to a file on Desktop."""
    if not chat_history:
        console.print("[red]No chat history to save.[/red]")
        return

    title = console.input("[cyan]Chat Title > [/cyan]").strip()
    if not title:
        console.print("[red]Title not valid.[/red]")
        return

    safe = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    if not safe:
        safe = "chat"

    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    date_filename = datetime.now().strftime("%d-%m-%y")
    filename = f"{safe}_{date_filename}.txt"
    path = os.path.join(desktop, filename)

    try:
        with open(path, "w", encoding="utf-8") as f:
            date_content = datetime.now().strftime("%d/%m/%y %H:%M:%S")
            f.write(f"Date and time: {date_content} | Model: {active_model}\n\n")
            for line in chat_history:
                f.write(line + "\n")
                f.write("\n")

            console.print("[green]Chat saved to your desktop[/green]")
    except Exception as e:
        console.print(f"[red]Error saving chat: {e}[/red]")

# chat_loop
def chat_loop():
    """The main interacting loop for user and AI conversations."""
    global config_model_path, config_base_prompt, attached_file_content
    while True:
        print()
        user_input = console.input("[cyan]You > [/cyan]").strip()

        if user_input.lower() == "save":
            save_chat()
        elif user_input.lower() == "copy":
            last_msg = None
            for msg in reversed(chat_history):
                if msg.startswith("AI: "):
                    last_msg = msg[4:].strip()
                    break
            if last_msg:
                try:
                    pyperclip.copy(last_msg)
                    console.print("[green]Response copied to clipboard[/green]")
                except Exception as e:
                     console.print(f"[red]Error copying: {e}[/red]")
            else:
                console.print("[yellow]No AI response found to copy.[/yellow]")

        elif user_input.lower() == "add":
            file_path = console.input("[cyan]Insert .txt or .pdf file path > [/cyan]").strip()
            if not (file_path.lower().endswith(".txt") or file_path.lower().endswith(".pdf")):
                console.print("[red]Error: Only .txt and .pdf files are allowed.[/red]")
            elif not os.path.exists(file_path):
                console.print("[red]Error: File not found.[/red]")
            else:
                try:
                    if file_path.lower().endswith(".pdf"):
                        reader = pypdf.PdfReader(file_path)
                        text_list = []
                        for page in reader.pages:
                            text_list.append(page.extract_text())
                        attached_file_content = "\n".join(text_list)
                    else:
                        with open(file_path, "r", encoding="utf-8") as f:
                            attached_file_content = f.read()
                    console.print(f"[green]File '{os.path.basename(file_path)}' added successfully![/green]\n")
                    console.print("[yellow]To get the best results, please be more precise with your prompts. Note that processing the attached file may increase the response time.[/yellow]")
                except Exception as e:
                    console.print(f"[red]Error reading file: {e}[/red]")

        elif user_input.lower() == "remove":
            if attached_file_content:
                attached_file_content = None
                console.print("[yellow]Attached file removed.[/yellow]")
            else:
                console.print("[red]No file attached to remove.[/red]")

        elif user_input.lower() == "exit":
            console.print(Rule("Chat Terminated", style="cyan"))
            print()
            console.print(Rule(style="white"))
            while True:
                command = console.input("[cyan]Command > [/cyan]").strip().lower()

                if command == "start ai":
                    with console.status("[green]starting ai[/green]", spinner="dots"):
                        time.sleep(2)
                    load_function()
                    break

                elif command == "exit":
                    exit()

                elif command == "view model info":
                    view_model_info_function()

                elif command == "models folder":
                    open_models_folder()

                elif command == "help":
                    help_path = os.path.join(get_base_path(), "MindCLI_HELP.txt")
                    try:
                        if os.path.exists(help_path):
                            os.startfile(help_path)
                            console.print("[green]Opening MindCLI_HELP.txt[/green]")
                        else:
                            console.print(f"[red]MindCLI_HELP.txt not found in the program folder[/red]")
                    except Exception as e:
                        console.print(f"[red]Error opening help file: {e}[/red]")

                elif command == "license":
                    license_path = os.path.join(get_base_path(), "LICENSE.txt")
                    try:
                        if os.path.exists(license_path):
                            os.startfile(license_path)
                            console.print("[green]Opening LICENSE.txt[/green]")
                        else:
                            console.print(f"[red]LICENSE.txt not found[/red]")
                    except Exception as e:
                        console.print(f"[red]Error opening license: {e}[/red]")

                elif command == "info":
                    info_text = (
                        "Developer: LDM Dev\n"
                        "App Version: 1.0\n"
                        "Repository GitHub: https://github.com/Lorydima/MindCLI\n"
                        "Website: https://Lorydima.github.io/MindCLI-WebSite/"
                    )
                    console.print(Panel(info_text, title="App Information", border_style="cyan"))

                elif command == "edit base prompt":
                    new_prompt = console.input("[cyan]Enter new base prompt > [/cyan]").strip()
                    if new_prompt:
                        if save_config_to_file(config_model_path, new_prompt):
                            config_base_prompt = new_prompt
                            console.print("[green]Base prompt updated![/green]")
                    else:
                        console.print("[yellow]Operation cancelled.[/yellow]")

                elif command == "change parameters":
                    params = config_parameters.copy()
                    try:
                        mt = console.input(f"[cyan]Max Tokens (Current {params['max_tokens']}) > [/cyan]").strip()
                        if mt: params['max_tokens'] = int(mt)
                        
                        tmp = console.input(f"[cyan]Temperature (Current {params['temp']}) > [/cyan]").strip()
                        if tmp: params['temp'] = float(tmp)
                        
                        tp = console.input(f"[cyan]Top P (Current {params['top_p']}) > [/cyan]").strip()
                        if tp: params['top_p'] = float(tp)
                        
                        rp = console.input(f"[cyan]Repeat Penalty (Current {params['repeat_penalty']}) > [/cyan]").strip()
                        if rp: params['repeat_penalty'] = float(rp)
                        
                        if save_config_to_file(config_model_path, config_base_prompt, params):
                            console.print("[green]Parameters updated successfully![/green]")
                    except ValueError:
                        console.print("[red]Invalid input. Operation cancelled.[/red]")

                else:
                    console.print("[white]-[white] [red]Unknown command[/red]")
            break
        else:
            if gpt4all_model is None:
                console.print("[red]Model not loaded[/red]")
                continue
            chat_history.append(f"User: {user_input}")
            ai_response = None
            with console.status("[yellow]Thinking...[/yellow]", spinner="dots"):
                try:
                    if attached_file_content:
                        full_prompt = f"{active_base_prompt}\n\nAttached file content:\n{attached_file_content}\n\nUser: {user_input}\nAI:"
                    else:
                        full_prompt = f"{active_base_prompt}\n\nUser: {user_input}\nAI:"
                    
                    with suppress_stderr_fd():
                        response = gpt4all_model.generate(
                            full_prompt,
                            max_tokens=config_parameters.get("max_tokens", 2048),
                            temp=config_parameters.get("temp", 0.4),
                            top_p=config_parameters.get("top_p", 0.9),
                            repeat_penalty=config_parameters.get("repeat_penalty", 1.1),
                        )

                    text = sanitize_response(str(response or ""))
                    
                    prefixes_to_remove = ["AI:", "AI Assistant:", "Assistant:", "Response:"]
                    for prefix in prefixes_to_remove:
                        if text.startswith(prefix):
                            text = text[len(prefix):].strip()
                            break
                    
                    ai_response = text
                    chat_history.append(f"AI: {ai_response}")
                except Exception as e:
                    console.print(f"[red]Error generating response: {str(e)}[/red]")

            if ai_response:
                typing_effect(ai_response)

introduction()
