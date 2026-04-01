# MindCLI V1.0
<div align="center">
  <img src="https://lorydima.github.io/MindCLI/MindCLI_README.png" alt="MindCLI_V1.0_README_Img" width="800">
</div>

# ℹ️ Repository Info 
![GitHub stars](https://img.shields.io/github/stars/Lorydima/MindCLI?color=gold)
![GitHub repo size](https://img.shields.io/github/repo-size/Lorydima/MindCLI?color=red)
![Platform: Windows](https://img.shields.io/badge/platform-windows-blue)
![Platform: Linux via Wine](https://img.shields.io/badge/linux%20via%20wine-red?)
![macOS Support](https://img.shields.io/badge/macos%20via%20main.py-lightblue?)

![GitHub last commit](https://img.shields.io/github/last-commit/Lorydima/MindCLI?color=lightblue)
![GitHub version](https://img.shields.io/github/v/release/Lorydima/MindCLI?color=blueviolet)
![GitHub Pull Requests](https://img.shields.io/github/issues-pr/Lorydima/MindCLI?color=purple)
![GitHub Issues](https://img.shields.io/github/issues/Lorydima/MindCLI?color=purple)

![Contributions welcome](https://img.shields.io/badge/contributions-welcome-green)
![License: GPL-3.0](https://img.shields.io/badge/license-GPL--3.0-blue)

# 🎲 Features

| Img | Feature Description |
|:---:|-------------------|
| <img src="https://lorydima.github.io/MindCLI/MindCli_README_1.png" width="600"> | **Powerful Chat Mode:** Easy and useful commands with text formatting that improve interaction with AI models. |
| <img src="https://github.com/Lorydima/MindCLI/blob/main/docs/MindCLI_README_2.png" width="600"> | **Easy Commands:** Simple commands which allow for much simpler use and control of AI in a CLI. |
| <img src="https://api.iconify.design/fa-solid:file-code.svg?color=%23ffffff" width="40"> | **GGUF Compatibility:** Supports all AI models in .gguf format from Hugging Face. |
| <img src="https://api.iconify.design/fa-solid:user-shield.svg?color=%23ffffff" width="40"> | **Privacy & Productivity:** Runs AI models offline, ensuring a privacy-first experience. |
| <img src="https://api.iconify.design/fa-solid:sliders-h.svg?color=%23ffffff" width="40"> | **Complete Model Control:** Control over basic prompts, parameters, and hardware modes. |
| <img src="https://api.iconify.design/fa-solid:balance-scale.svg?color=%23ffffff" width="40"> | **Ethical AI Usage:** The developer encourages everyone to use AI models responsibly and ethically. |

# 📁 Project Structure

```
MindCLI/
├── src/                               # Application source code
│   └── mindcli/                       # Main application package
│       ├── main.py                    # Application entry point
│       ├── config.py                  # Configuration management
│       ├── ai_engine.py               # AI model interaction
│       ├── ui.py                      # Terminal UI components
│       ├── utils.py                   # Helper functions
│       │
│       └── assets/                    # Application assets
│           ├── MindCLI.ico            # Application icon
│           ├── MindCLI.png            # Application logo
│           └── MindCLI_HELP.txt       # Help documentation
│
├── docs/                              # Website Source Code
│   ├── index.html                     # Website main page
│   ├── style.css                      # Website styling
│   └── ...                            # Website assets (images, ico)
│
├── LICENSE.txt                        # GNU GPL v3 License
├── README.md                          # Project overview 
├── CHANGELOG.md                       # Version history
├── CONTRIBUTING.md                    # Contribution guidelines
├── pyproject.toml                     # Project metadata and build config
├── SECURITY.md                        # Security Policy
└── requirements.txt                   # External dependencies
```

**About assets:**  
Assets (icons and help files) are stored inside the package so the application can find them when run from source or packaged.

**About the docs/ folder:**  
The `docs/` folder contains the source code for the project's website. It is **not required to run the application** locally.


# 🌐 MindCLI Website
<img src="https://lorydima.github.io/MindCLI/MindCLI_README.png" alt="MindCLI_Website_Img" width="1200">
You can access the MindCLI Website from this link: <a href="https://lorydima.github.io/MindCLI/" target="_blank">MindCLI Website</a>

# 💾 Download MindCLI
To download MindCLI v1.0 follow this link, the software is for **Windows OS, for linux use Wine:**
<a href="https://github.com/Lorydima/MindCLI/releases/download/MindCLI/MindCLI_V1.0.zip" download>Download MindCLI v1.0</a>

**For macOS**  
The EXE file is not available. However, the application can be run from source by executing the `main.py` file, provided that Python and the required dependencies are installed.

> [!WARNING]
> **For proper program execution, please read the notes below**
> 
> **Do not delete the `.json`, `.txt` files or the `Models` folder** in the program directory; they are required for the program to function correctly.

# 🔗 Clone Repository
Follow these steps:
```bash
git clone https://github.com/Lorydima/MindCLI.git
```

```bash
pip install -r requirements.txt
```

```bash
run main.py
```

# 🛠️ Bug reports and issues
I do my best to keep this project stable and reliable, but bugs can still happen.
If you spot any issues or errors, feel free to open a GitHub issue.
Your feedback really helps me improve the project.

# 📄 License
Before you use the software please read the GNU GPL v3 license at this link: [License](https://github.com/Lorydima/MindCLI?tab=License-1-ov-file)
