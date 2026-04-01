import os
import sys
import pyperclip
import pypdf
from datetime import datetime

def open_models_folder(base_path):
    """Opens the local Models directory."""
    curr = os.path.abspath(base_path)
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
        project_root = os.path.abspath(os.path.join(base_path, ".."))
    
    models_path = os.path.join(project_root, "Models")
    if not os.path.exists(models_path):
        models_path = os.path.join(project_root, "models")
        
    try:
        if os.path.exists(models_path):
            os.startfile(models_path)
            return True, f"Opening Models folder"
        else:
            return False, f"Models folder not found at: {models_path}"
    except Exception as e:
        return False, f"Error opening folder: {e}"

def read_attached_file(file_path):
    """Reads the content of .txt or .pdf files."""
    try:
        if file_path.lower().endswith(".pdf"):
            reader = pypdf.PdfReader(file_path)
            text_list = []
            for page in reader.pages:
                text_list.append(page.extract_text())
            return "\n".join(text_list)
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
    except Exception as e:
        raise Exception(f"Error reading file: {e}")

def save_chat_to_desktop(chat_history, active_model):
    """Saves the current chat history to a file on Desktop."""
    if not chat_history:
        return False, "No chat history to save."

    title = input("Chat Title > ").strip()
    if not title:
        return False, "Title not valid."

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
            return True, "Chat saved to your desktop"
    except Exception as e:
        return False, f"Error saving chat: {e}"

def copy_to_clipboard(text):
    """Copies text to the system clipboard."""
    try:
        pyperclip.copy(text)
        return True, "Response copied to clipboard"
    except Exception as e:
        return False, f"Error copying: {e}"
