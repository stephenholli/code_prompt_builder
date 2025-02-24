# Code Prompt Builder

A Python script to build a consolidated code prompt from development files (e.g., HTML, CSS, JS, Python) for LLM analysis or project review.

## Features
* Collects files based on configurable extensions from the current directory and subdirectories.
* Excludes minified files and user-defined exclusions.
* Outputs file contents with metadata (line count, size, last modified time).
* Generates a timestamped `code_prompt_YYYY-MM-DD_HHMM.txt` with token-efficient formatting for LLM prompts.
* Creates a default `code-prompt-builder-config.json` if none exists.
* Robust error handling for permissions, encoding, and file system issues.

## Usage
Run the script in your project directory:
```
python code-prompt-builder.py
```
Output will be written to a file like `code_prompt_2025-02-23_1845.txt`. Check the console for errors or status messages.

## Configuration
The script uses `code-prompt-builder-config.json` to define which files to include or exclude. If missing, it creates one with defaults:
```
{
    "extensions": [".html", ".css", ".js", ".py"],
    "exclude_files": ["code-prompt-builder.py"]
}
```
Edit this file to customize extensions (e.g., add ".json") or exclude additional files (e.g., "test.py").

## Requirements
* Python 3.x
* No external dependencies

## Git Ignore
This project includes a `.gitignore` file to exclude generated files and Python artifacts. Contents:
```
# Generated output files from Code Prompt Builder
code_prompt_*.txt

# Python artifacts
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
*.egg-info/

# Editor/IDE files
.vscode/
.idea/
*.swp
*~
.DS_Store

# Optional: Uncomment to ignore config file after initial creation
# code-prompt-builder-config.json
```
Note: Keep `code-prompt-builder-config.json` tracked in Git if you want to version-control your settings.

## Example Output
```
Code Prompt (2025-02-23 18:45) for dev & LLM
###

[HTML] ./index.html (20L, 512B, Mod: 2025-02-23 14:30)
<html>
  <body><script src="js/script.js"></script></body>
</html>
###

Files: 1
END
```

## Notes
This tool is designed for development workflows and LLM co-design. It skips hidden directories (e.g., `.git`) and handles errors gracefully.