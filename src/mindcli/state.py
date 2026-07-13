# Global application state, console, and default constants.

from rich.console import Console

# Rich console instance for terminal output
console = Console()

# Active model configuration
config_model_path = None       # Currently selected model name
config_base_prompt = None      # Base prompt sent to the AI
config_user_name = None        # Unused, reserved for future use
config_parameters = {}         # AI generation parameters (temperature, top_p, etc.)

# Default AI parameters
DEFAULT_PARAMS = {
    "num_predict": 2048,       # Maximum tokens to generate
    "temperature": 0.5,        # Response creativity (0.0 - 1.0)
    "top_p": 0.9,              # Nucleus sampling threshold
    "repeat_penalty": 1.1,     # Penalty for repeating tokens
    "num_ctx": 4096            # Context window size
}

# Default base prompt used when no model-specific prompt is set
DEFAULT_BASE_PROMPT = "You are a helpful coding assistant. Answer the user's questions clearly and provide code blocks when necessary."

# Chat session state
chat_history = []              # Conversation history list
active_model = None            # Model currently loaded in chat
active_base_prompt = None      # Base prompt used in current chat session
ollama_ready = False           # Whether Ollama process is running

# File attachment state
attached_file_content = None   # Content of the attached file
attached_filename = None       # Name of the attached file

# Agent mode state
agent_temp_content = None      # Temporary unsaved agent content for refinement

# Persistent configuration
config_download_source = "N/A" # Source URL/name for model download
config_device = "cpu"          # Hardware device (cpu/gpu)
config_tavily_api_key = ""     # Tavily web search API key
config_memories = []           # List of saved AI memories
