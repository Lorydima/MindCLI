# Changelog — MindCLI

All notable changes to this project will be documented in this file.  
This project uses semantic versioning.

## [2.0]

### Added

- Migrated from GPT4All (GGUF) to **Ollama** for AI model management
- Ollama model download directly from the application interface
- Ollama model delete with automatic fallback to another model
- Installed models list with file size display
- **Tavily web search integration** for real-time web context
- **Agent Mode** — create and edit files on your PC using AI
- **Memory Management** — add, view, remove, and clear AI memories
- **Chat Management** — list, open, and remove saved chat files
- Chats saved in a dedicated `chats/` directory instead of Desktop
- Per-model configuration (base prompt, parameters, device) stored in separate JSON files
- New configuration system with multiple files (`paths.json`, `hardware.json`, `tavily_API.json`, `memory.json`)
- GPU detection via `nvidia-smi` and per-model device selection (CPU/GPU)
- Support for additional file types: `.docx`, `.xlsx`, `.md`, `.py`, `.cpp`, images (`.png`, `.jpg`, `.gif`, etc.)
- Rich typing effect with Live rendering for markdown and code blocks
- Clipboard copy with error handling for Windows
- Windows-style masked input for API keys
- Signal handlers (`SIGINT`, `SIGTERM`, `SIGHUP`) for graceful Ollama shutdown
- `num_ctx` parameter support alongside standard AI parameters
- Model parameters normalization with backward compatibility for v1.0 key names (`max_tokens` → `num_predict`, `temp` → `temperature`)
- Code reorganization into modular package structure under `src/mindcli/`

### Changed

- **AI Engine**: Replaced GPT4All with Ollama API
- **Configuration**: Single `config.json` → multiple config files in `configs/` directory
- **Project Structure**: Reorganized from flat modules to a structured package with separate modules for state, utils, config, Ollama, file handling, web search, memory, chat, model management, and UI
- **Chat Save**: Now saves to `chats/` folder instead of Desktop
- **File Attachment**: Extended from `.txt`/`.pdf` only to 20+ file types including Office documents and images
- **Typing Effect**: Rewritten with Rich Live rendering for smoother markdown and code display
- **Command Interface**: Expanded main menu with additional subcommands for memory, chats, models, and Tavily API management
- **Requirements**: Replaced `gpt4all` dependency with `ollama`, added `tavily-python`, `python-docx`, `openpyxl`

### Fixed

- Model file path resolution — v2.0 uses Ollama model names directly instead of GGUF file paths
- Chat history management — history is now cleared when switching models
- Ollama process lifecycle — proper start, detection, and kill across platforms
- Better error handling for missing Ollama installation with download links displayed

## [1.0] -

### Added

- Initial release of MindCLI.
- Command-line interface for AI model interaction.
- Support for GGUF models via GPT4All.
- Rich terminal UI with typing effects and syntax highlighting.
- Built-in PDF and TXT file reader for context attachment.
- Model configuration system (parameters, base prompt, hardware mode).
- Chat history saving and response copying.
- Offline AI execution for privacy.
- Models folder management.
- Comprehensive documentation and website.
