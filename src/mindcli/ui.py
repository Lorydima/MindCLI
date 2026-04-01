import pyfiglet
import time
import os
from rich.console import Console, Group
from rich.panel import Panel
from rich.align import Align
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.syntax import Syntax

console = Console()

def display_banner():
    """Displays the main banner and introduction of the app."""
    banner = pyfiglet.figlet_format("MindCLI")
    console.print(Align.center(f"[red]{banner}[/red]"))
    console.print(Rule(style="white"))

def display_main_menu():
    """Main menu command loop."""
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

def display_more_commands():
    """Displays additional commands."""
    console.print(" • [cyan]Edit Base Prompt[/cyan] - modify the base prompt used by the AI.")
    console.print(" • [cyan]Change Model[/cyan] - switch to a different AI model.")
    console.print(" • [cyan]Change Parameters[/cyan] - modify model parameters (tokens, temp, etc.).")
    console.print(" • [cyan]Models Folder[/cyan] - open the models directory.")
    console.print(" • [cyan]Help[/cyan] - open the help file.")
    console.print(" • [cyan]License[/cyan] - view the license.")
    console.print(" • [cyan]Info[/cyan] - view app information.")

def display_app_info():
    """Displays information about the app."""
    info_text = (
        "Developer: LDM Dev\n"
        "App Version: 1.0\n"
        "Repository GitHub: https://github.com/Lorydima/MindCLI\n"
        "Website: https://Lorydima.github.io/MindCLI/"
    )
    console.print(Panel(info_text, title="App Information", border_style="cyan"))

def view_model_info(config, full_path, size_gb):
    """Displays information about the active model, parameters, and base prompt."""
    table = Table(title="Model Information", border_style="cyan")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Model File", os.path.basename(config['model_path']))
    table.add_row("File Size", size_gb)
    table.add_row("Model Path", full_path)
    table.add_row("Download Source", config['download_source'])
    
    console.print(Align.center(table))
    
    p_table = Table(title="AI Parameters", border_style="yellow")
    p_table.add_column("Parameter", style="cyan")
    p_table.add_column("Value", style="green")
    
    params = config.get("parameters", {})
    for k, v in params.items():
        p_table.add_row(k.replace("_", " ").title(), str(v))
    
    p_table.add_row("Hardware Mode", "NVIDIA GPU" if config['device'] == "gpu" else "CPU")
    
    console.print(Align.center(p_table))
    console.print(Panel(config['base_prompt'], title="Base Prompt", border_style="cyan"))

def display_chat_commands(active_model, attached_file="No"):
    """Displays commands available in the chat session."""
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
    
    console.print("\n")
    warning = Text("WARNING: AI models can produce incorrect responses, so verify the responses.", style="red bold underline")
    console.print(warning)
    console.print("\n")
    note = Text("Note: ", style="yellow bold underline")
    note.append("Response quality, speed, and language depend on ", style="white")
    note.append("the model chosen, your PC hardware, the base prompt and AI parameters.", style="yellow bold underline")
    console.print(note)
    
    console.print("\n")
    model_text = Text("Model active: ", style="yellow")
    model_text.append(active_model, style="green bold")
    console.print(model_text)
    
    console.print("\n")
    attached_text = Text("Attached File: ", style="yellow")
    if attached_file == "No":
        attached_text.append("No", style="red")
    else:
        attached_text.append(attached_file, style="green")
    console.print(attached_text)
    console.print("\n")

def typing_effect(text: str):
    """Effect for AI responses."""
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

def setup_wizard(default_params):
    """Setup wizard UI."""
    console.print(Align.center("[yellow]Setup Mode[/yellow]"))
    console.print("\n")
    console.print(Align.center("[yellow]For help with the setup, you can refer to the MindCLI_HELP.txt file in the program's folder.[/yellow]"))
    console.print("\n")
    
    model_path = console.input("[cyan]Insert Model file name (e.g. my-model.gguf) or path > [/cyan]").strip()
    console.print("\n")

    download_source = console.input("[cyan]Insert Download Source (URL or Name, optional) > [/cyan]").strip() or "N/A"
    console.print("\n")

    console.print("[cyan]Do you have an NVIDIA GPU? (y/n)[/cyan]")
    gpu_choice = console.input("> ").strip().lower()
    device = "gpu" if gpu_choice == 'y' else "cpu"
    console.print("\n")
    
    console.print("[cyan]Enter the base prompt. Finish with an empty line.[/cyan]")
    lines = []
    while True:
        l = console.input()
        if l == "":
            break
        lines.append(l)
    base_prompt = "\n".join(lines).strip()
    console.print("\n")
    
    console.print("[cyan]Do you want to modify AI parameters (max_tokens, temp, etc.)? (y/n)[/cyan]")
    choice = console.input("> ").strip().lower()
    console.print("\n")
    
    params = default_params.copy()
    if choice == 'y':
        try:
            mt = console.input(f"[cyan]Max Tokens (Default {params['max_tokens']}) > [/cyan]").strip()
            if mt: params['max_tokens'] = int(mt)
            console.print("\n")
            
            tmp = console.input(f"[cyan]Temperature (Default {params['temp']}) > [/cyan]").strip()
            if tmp: params['temp'] = float(tmp)
            console.print("\n")
            
            tp = console.input(f"[cyan]Top P (Default {params['top_p']}) > [/cyan]").strip()
            if tp: params['top_p'] = float(tp)
            console.print("\n")
            
            rp = console.input(f"[cyan]Repeat Penalty (Default {params['repeat_penalty']}) > [/cyan]").strip()
            if rp: params['repeat_penalty'] = float(rp)
            console.print("\n")
        except ValueError:
            console.print("[red]Invalid input, using defaults for remaining values.[/red]")
            console.print("\n")

    return model_path, base_prompt, params, download_source, device
