# Chat management — main chat loop, agent mode, chat file operations, and typing effects.

import os
import time
from datetime import datetime
from rich.text import Text
from rich.panel import Panel
from rich.align import Align
from rich.rule import Rule
from rich.live import Live
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.table import Table
from mindcli import state
from mindcli.state import console
from mindcli.utils import copy_to_clipboard, sanitize_response
from mindcli.ollama_utils import generate_ai_response
from mindcli.file_handler import read_file_content
from mindcli.config_manager import get_chats_dir
from mindcli.web_search import tavily_search, format_tavily_context


def typing_effect(text: str, model_name: str):
    """Displays a typing effect with Rich while preserving code fences and markdown."""
    if not text:
        return

    console.print(Text(f"{model_name} >", style="bold cyan"))

    parts = text.split("```")
    for index, part in enumerate(parts):
        if index % 2 == 0:
            cleaned = part.strip()
            if not cleaned:
                continue

            buffer = ""
            with Live(Markdown(""), console=console, refresh_per_second=30) as live:
                for ch in cleaned:
                    buffer += ch
                    try:
                        live.update(Markdown(buffer))
                    except Exception:
                        live.update(Text(buffer))
                    time.sleep(0.006)
            console.print()
        else:
            lines = part.splitlines()
            language = lines[0].strip() if lines else ""
            code = "\n".join(lines[1:]) if len(lines) > 1 else ""
            if code.strip():
                console.print(Syntax(code, language or "text", theme="monokai", line_numbers=False))


def save_chat():
    """Saves the current chat history to a text file in the chats directory."""
    if not state.chat_history:
        console.print("[red]No chat history to save.[/red]")
        return

    title = console.input("[cyan]Chat Title > [/cyan]").strip()
    if not title:
        console.print("[red]Title not valid.[/red]")
        return

    safe = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    if not safe:
        safe = "chat"

    chats_dir = get_chats_dir()
    filename = f"{safe}.txt"
    path = os.path.join(chats_dir, filename)

    try:
        with open(path, "w", encoding="utf-8") as f:
            now = datetime.now().strftime("%d/%m/%Y at %H:%M:%S")
            f.write(f"Chat saved on: {now}")
            f.write("\n")
            f.write("=" * 50)
            f.write("\n")
            for line in state.chat_history:
                f.write(line + "\n")
                f.write("\n")

        console.print(f"[green]Chat saved to '{path}'[/green]")
    except Exception as e:
        console.print(f"[red]Error saving chat: {e}[/red]")


def list_chats_cmd():
    """Lists all saved chat files in the chats directory."""
    chats_dir = get_chats_dir()
    try:
        chat_files = [f for f in os.listdir(chats_dir) if f.endswith(".txt")]
        if not chat_files:
            console.print("[yellow]No saved chats found.[/yellow]")
            return

        table = Table(title="Saved Chats", border_style="cyan")
        table.add_column("#", style="white bold")
        table.add_column("Filename", style="yellow")

        for i, fname in enumerate(sorted(chat_files), 1):
            table.add_row(str(i), fname)

        console.print(Align.center(table))
    except Exception as e:
        console.print(f"[red]Error listing chats: {e}[/red]")


def open_chat_cmd():
    """Displays a saved chat file in the terminal."""
    chats_dir = get_chats_dir()
    chat_name = console.input("[cyan]Enter chat filename (e.g., mychat_01-01-25.txt) > [/cyan]").strip()
    if not chat_name:
        console.print("[yellow]Cancelled.[/yellow]")
        return

    chat_path = os.path.join(chats_dir, chat_name)
    if not os.path.exists(chat_path):
        console.print(f"[red]Chat file '{chat_name}' not found.[/red]")
        return

    try:
        with open(chat_path, "r", encoding="utf-8") as f:
            content = f.read()
        console.print(Panel(content, title=chat_name, border_style="cyan"))
    except Exception as e:
        console.print(f"[red]Error reading chat: {e}[/red]")


def remove_chat_cmd():
    """Deletes a saved chat file after user confirmation."""
    chats_dir = get_chats_dir()
    chat_name = console.input("[cyan]Enter chat filename to delete (e.g., mychat_01-01-25.txt) > [/cyan]").strip()
    if not chat_name:
        console.print("[yellow]Cancelled.[/yellow]")
        return

    chat_path = os.path.join(chats_dir, chat_name)
    if not os.path.exists(chat_path):
        console.print(f"[red]Chat file '{chat_name}' not found.[/red]")
        return

    confirm = console.input(f"[red]Are you sure you want to delete '[bold]{chat_name}[/bold]'? (y/n) > [/red]").strip().lower()
    if confirm == 'y':
        try:
            os.remove(chat_path)
            console.print(f"[green]Chat '[bold]{chat_name}[/bold]' deleted successfully.[/green]")
        except Exception as e:
            console.print(f"[red]Error deleting chat: {e}[/red]")
    else:
        console.print("[yellow]Cancelled.[/yellow]")


def agent_mode_function():
    """Agent mode for creating and editing files on the PC using AI assistance."""
    state.agent_temp_content = None
    warning_agent = Text("WARNING: Review AI-generated file content carefully. If executing code, verify it is safe before use.", style="red bold")
    console.print(Align.center("[bold cyan]Agent Mode[/bold cyan]"))
    console.print(Align.center("[yellow]In this mode, the AI can work directly with files on your PC.[/yellow]"))
    state.chat_history.append("USER: Agent mode activated")

    supported_extensions = [".txt", ".md", ".py", ".cpp", ".c", ".java", ".js", ".html", ".css", ".json", ".xml"]

    while True:
        console.print("[cyan]Do you want to [bold]create[/bold] a new file or [bold]edit[/bold] an existing one?[/cyan]")
        agent_input = console.input("[magenta]Agent (create/edit/exit) > [/magenta]").strip().lower()

        if agent_input == "exit":
            console.print("[bold cyan]Exiting Agent Mode[/bold cyan]")
            break

        # Create new file flow
        if agent_input in ("create", "new"):
            state.chat_history.append("Agent: Create File")
            filename = console.input("[cyan]Enter filename with extension (e.g., script.py, document.txt) > [/cyan]").strip()
            if not filename:
                console.print("[red]Filename cannot be empty.[/red]")
                continue

            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext not in supported_extensions:
                console.print(f"[red]File type not supported. Supported types: {', '.join(supported_extensions)}[/red]")
                continue

            prompt = console.input("[cyan]Enter prompt for the AI > [/cyan]").strip()
            if not prompt:
                console.print("[red]Prompt cannot be empty.[/red]")
                continue

            state.chat_history.append(f"User: {filename}")
            state.chat_history.append(f"{state.active_model} prompt > {prompt}")

            # Include previous unsaved content for refinement
            refinement_context = ""
            if state.agent_temp_content:
                refinement_context = f"\n\nPrevious unsaved version to refine:\n{state.agent_temp_content}\n\nRefine it based on the new request."
                console.print("[yellow]Including previous unsaved content for refinement.[/yellow]")

            ai_prompt = f"Create content for a file named '{filename}' based on this request: {prompt}{refinement_context}\n\nRespond ONLY with the file content, without any additional text, explanations, or formatting."
            ai_response = generate_ai_response(ai_prompt)

            if ai_response:
                cleaned = ai_response
                prefixes = ["ecco", "certo", "ecco qui", "certo ecco", "ecco il file", "certo, ecco", "certo! ecco"]
                for p in prefixes:
                    if cleaned.lower().startswith(p):
                        cleaned = cleaned[len(p):].strip().lstrip(":,!.- ")
                        break

                state.chat_history.append(f"{state.active_model} agent response > {cleaned}")

                console.print(Align.center(Text("AI Generated Content", style="bold yellow")))
                console.print(Panel(cleaned, title=filename, border_style="yellow"))

                approval = console.input("[cyan]Do you want to save this content? (y/n) > [/cyan]").strip().lower()
                if approval == 'y':
                    state.chat_history.append("User: Content accepted and saved")
                    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
                    file_path = os.path.join(desktop_path, filename)

                    try:
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(cleaned)
                        console.print(f"[green]File '[bold]{filename}[/bold]' created successfully on Desktop![/green]")
                        state.agent_temp_content = None
                    except Exception as e:
                        console.print(f"[red]Error creating file: {e}[/red]")
                else:
                    state.chat_history.append("User: Content not accepted")
                    console.print("[yellow]Content not saved. It will be included in the next prompt for refinement.[/yellow]")
                    state.agent_temp_content = cleaned
            continue

        # Edit existing file flow
        if agent_input == "edit":
            state.chat_history.append("Agent: Edit File")
            file_path = console.input("[cyan]Enter the full path of the file to edit > [/cyan]").strip()
            if not file_path:
                console.print("[red]File path cannot be empty.[/red]")
                continue

            if not os.path.exists(file_path):
                console.print("[red]File not found.[/red]")
                continue

            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in supported_extensions:
                console.print(f"[red]File type not supported for editing. Supported types: {', '.join(supported_extensions)}[/red]")
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    current_content = f.read()
            except Exception as e:
                console.print(f"[red]Error reading file: {e}[/red]")
                continue

            console.print(Align.center(Text(f"Current File Content: {os.path.basename(file_path)}", style="bold white")))

            prompt = console.input("[cyan]Enter prompt for the AI (describe what changes to make) > [/cyan]").strip()
            if not prompt:
                console.print("[red]Prompt cannot be empty.[/red]")
                continue

            state.chat_history.append(f"User: {file_path}")
            state.chat_history.append(f"{state.active_model} prompt > {prompt}")

            refinement_context = ""
            if state.agent_temp_content:
                refinement_context = f"\n\nPrevious unsaved version to refine:\n{state.agent_temp_content}\n\nRefine it based on the new request."
                console.print("[yellow]Including previous unsaved content for refinement.[/yellow]")

            ai_prompt = f"Current content of {os.path.basename(file_path)}:\n{current_content}\n\nRequest: {prompt}{refinement_context}\n\nRespond ONLY with the modified file content, without any additional text, explanations, or formatting."
            ai_response = generate_ai_response(ai_prompt)

            if ai_response:
                cleaned = ai_response
                prefixes = ["ecco", "certo", "ecco qui", "certo ecco", "ecco il file", "certo, ecco", "certo! ecco", "ecco il contenuto"]
                for p in prefixes:
                    if cleaned.lower().startswith(p):
                        cleaned = cleaned[len(p):].strip().lstrip(":,!.- ")
                        break

                state.chat_history.append(f"{state.active_model} agent response > {cleaned}")

                console.print(Align.center(Text("AI Generated Content", style="bold yellow")))
                console.print(Panel(cleaned, title=os.path.basename(file_path), border_style="yellow"))

                approval = console.input("[cyan]Do you want to save these changes? (y/n) > [/cyan]").strip().lower()
                if approval == 'y':
                    state.chat_history.append("User: Changes accepted and saved")
                    try:
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(cleaned)
                        console.print(f"[green]File '[bold]{os.path.basename(file_path)}[/bold]' updated successfully![/green]")
                        state.agent_temp_content = None
                    except Exception as e:
                        console.print(f"[red]Error updating file: {e}[/red]")
                else:
                    state.chat_history.append("User: Changes not accepted")
                    console.print("[yellow]Changes not saved. They will be included in the next prompt for refinement.[/yellow]")
                    state.agent_temp_content = cleaned
            continue

        console.print("[yellow]Unknown command. Type 'create', 'edit', or 'exit'.[/yellow]")


def chat_command_list_function():
    """Displays commands available in the chat session."""
    console.print(Rule("Chat", style="cyan"))
    console.print(
        Panel(
            "[bold white]Chat Commands[/bold white]\n"
            "[cyan]Save[/cyan] - save the current chat session.\n"
            "[cyan]Copy[/cyan] - copy the last AI response to clipboard.\n"
            "[cyan]Change[/cyan] - change the current AI model.\n"
            "[red]Exit[/red] - exit the chat session and return to the main command menu.\n"
            "\n"
            "[bold white]Files Commands[/bold white]\n"
            "[cyan]Add[/cyan] - attach a file (.txt, .pdf, .docx, .xlsx, .md, .py, .cpp, img, etc.) for context.\n"
            "[cyan]Remove[/cyan] - remove the attached file.\n"
            "\n"
            "[bold white]Advanced Commands[/bold white]\n"
            "[cyan]Search[/cyan] - search the web with Tavily and send results to the AI.\n"
            "[cyan]Agent[/cyan] - work directly with files using AI.\n",
            border_style="yellow"
        )
    )

    warning = Text("WARNING: AI models can produce incorrect or misleading responses due to BIAS or Allucinations. For thi reason always check AI repsonse", style="red bold")
    console.print(Align.center(warning))


def chat_loop():
    """The main interaction loop for user and AI conversations."""
    while True:
        user_input = console.input("[cyan]You > [/cyan]").strip()

        # Save chat history to file
        if user_input.lower() == "save":
            save_chat()

        # Copy last AI response to clipboard
        elif user_input.lower() == "copy":
            last_msg = None
            for msg in reversed(state.chat_history):
                if " > " in msg and not msg.startswith("USER:"):
                    last_msg = msg.split(" > ", 1)[1] if " > " in msg else msg
                    break
            if last_msg:
                try:
                    if not copy_to_clipboard(last_msg):
                        raise RuntimeError(
                            "Clipboard not available on Windows. Make sure Windows clipboard services are working."
                        )
                    console.print("[green]Response copied to clipboard[/green]")
                except Exception as e:
                    console.print(f"[red]Error copying: {e}[/red]")
            else:
                console.print("[yellow]No AI response found to copy.[/yellow]")

        # Attach a file for context
        elif user_input.lower() == "add":
            file_path = console.input("[cyan]Insert file path (.txt, .pdf, .docx, .xlsx, .md, .py, .cpp, img, etc.) > [/cyan]").strip()
            content = read_file_content(file_path)
            if content is not None:
                state.attached_file_content = content
                state.attached_filename = os.path.basename(file_path)
                console.print(Align.center(Text(f"File attached: {state.attached_filename}", style="bold yellow")))
                state.chat_history.append(f"User ADD: {state.attached_filename}")

        # Switch to a different AI model
        elif user_input.lower() == "change":
            from mindcli.model_manager import change_model_function
            change_model_function()

        # Remove the currently attached file
        elif user_input.lower() == "remove":
            if state.attached_file_content:
                fname = state.attached_filename or "file"
                state.attached_file_content = None
                state.attached_filename = None
                console.print(Align.center(Text(f"File {fname} removed", style="bold yellow")))
                state.chat_history.append(f"User REMOVE: {fname}")
            else:
                console.print("[red]No file attached to remove.[/red]")

        # Enter agent mode
        elif user_input.lower() == "agent":
            agent_mode_function()
            continue

        # Perform web search with Tavily
        elif user_input.lower() == "search":
            if not state.config_tavily_api_key:
                console.print("[red]Tavily API key not configured. Use More > API Config first.[/red]")
                continue

            search_target = console.input("[cyan]Enter a website, link, or topic to search > [/cyan]").strip()
            if not search_target:
                console.print("[yellow]Cancelled.[/yellow]")
                continue

            user_task = console.input("[cyan]What should the AI do with these results? > [/cyan]").strip()
            if not user_task:
                console.print("[yellow]Cancelled.[/yellow]")
                continue

            try:
                with console.status("[yellow]Searching Tavily web...[/yellow]", spinner="dots"):
                    tavily_payload = tavily_search(search_target, state.config_tavily_api_key)
                tavily_context = format_tavily_context(tavily_payload)
            except Exception as e:
                console.print(f"[red]Error searching web: {e}[/red]")
                continue

            state.chat_history.append(f"USER: Command Search\nTarget: {search_target}\nRequest: {user_task}")
            web_prompt = (
                f"{state.active_base_prompt or state.DEFAULT_BASE_PROMPT}\n\n"
                "You are given Tavily web search results. Use them to complete the user's request.\n\n"
                f"Search target: {search_target}\n"
                f"User request: {user_task}\n\n"
                f"Tavily context:\n{tavily_context}\n\n"
                "Answer:"
            )

            ai_response = generate_ai_response(web_prompt)
            if ai_response:
                state.chat_history.append(f"AI respond to search request: {ai_response}")
                typing_effect(ai_response, state.active_model)

        # Exit chat and return to main menu
        elif user_input.lower() == "exit":
            console.print(Rule("Chat Terminated", style="cyan"))
            from mindcli.ollama_utils import shutdown_ollama_everywhere
            shutdown_ollama_everywhere()
            return

        # Send user message to the AI
        else:
            if not state.ollama_ready:
                console.print("[red]Ollama model not loaded[/red]")
                continue

            state.chat_history.append(f"User: {user_input}")
            memory_block = ""
            if state.config_memories:
                memory_lines = "\n".join(f"- {m}" for m in state.config_memories)
                memory_block = f"\n\nMemory context:\n{memory_lines}"
            if state.attached_file_content:
                full_prompt = f"{state.active_base_prompt or state.DEFAULT_BASE_PROMPT}{memory_block}\n\nAttached file content:\n{state.attached_file_content}\n\nUser: {user_input}\nAI:"
            else:
                full_prompt = f"{state.active_base_prompt or state.DEFAULT_BASE_PROMPT}{memory_block}\n\nUser: {user_input}\nAI:"

            ai_response = generate_ai_response(full_prompt)
            if ai_response:
                typing_effect(ai_response, state.active_model)
