# Memory management — save, view, remove, and clear persistent AI memories.

import os
import json
from mindcli import state
from mindcli.utils import get_base_path


def get_memory_path():
    """Returns the path to memory.json in configs."""
    return os.path.join(get_base_path(), "configs", "memory.json")


def load_memories():
    """Loads memories from configs/memory.json into global state."""
    path = get_memory_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                state.config_memories = json.load(f)
        except Exception:
            state.config_memories = []
    else:
        state.config_memories = []


def save_memories():
    """Saves current memories to configs/memory.json."""
    path = get_memory_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state.config_memories, f, ensure_ascii=False, indent=2)
    except Exception as e:
        state.console.print(f"[red]Error saving memories: {e}[/red]")


def memory_add():
    """Prompts the user for a new memory and saves it."""
    memory = state.console.input("[cyan]Enter memory (what the AI should remember) > [/cyan]").strip()
    if not memory:
        state.console.print("[yellow]Cancelled.[/yellow]")
        return
    state.config_memories.append(memory)
    save_memories()
    state.console.print("[green]Memory saved![/green]")


def memory_view():
    """Displays all saved memories in a Rich table."""
    if not state.config_memories:
        state.console.print("[yellow]No memories saved.[/yellow]")
        return
    from rich.table import Table
    from rich.align import Align
    table = Table(title="Saved Memories", border_style="cyan")
    table.add_column("#", style="white bold")
    table.add_column("Memory", style="yellow")
    for i, mem in enumerate(state.config_memories, 1):
        table.add_row(str(i), mem)
    state.console.print(Align.center(table))


def memory_remove():
    """Removes a specific memory by index chosen by the user."""
    if not state.config_memories:
        state.console.print("[yellow]No memories to remove.[/yellow]")
        return
    memory_view()
    choice = state.console.input("[cyan]Enter the number of the memory to remove > [/cyan]").strip()
    if not choice.isdigit():
        state.console.print("[red]Invalid number.[/red]")
        return
    idx = int(choice) - 1
    if 0 <= idx < len(state.config_memories):
        removed = state.config_memories.pop(idx)
        save_memories()
        state.console.print(f"[green]Memory removed: {removed}[/green]")
    else:
        state.console.print("[red]Invalid memory number.[/red]")


def memory_clear():
    """Clears all memories after user confirmation."""
    if not state.config_memories:
        state.console.print("[yellow]No memories to clear.[/yellow]")
        return
    confirm = state.console.input("[red]Are you sure you want to clear all memories? (y/n) > [/red]").strip().lower()
    if confirm == "y":
        state.config_memories = []
        save_memories()
        state.console.print("[green]All memories cleared.[/green]")
    else:
        state.console.print("[yellow]Cancelled.[/yellow]")
