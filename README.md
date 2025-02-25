# Code Prompt Builder

A Python script to build a consolidated code prompt from development files (e.g., HTML, CSS, JS, Python, Markdown, JSON) for LLM analysis or project review.

## Features
* Collects files based on configurable extensions from the current directory and subdirectories.
* Excludes minified files and user-defined exclusions.
* Outputs file contents with metadata (line count, size, last modified time).
* Generates a timestamped `<folder>-code-prompt-YYYY-MM-DD_HHMM.txt` with token-efficient formatting for LLM prompts.
* Creates a default `code_prompt_builder_config.json` if none exists.
* Robust error handling for permissions, encoding, and file system issues.
* Ignores specified directories by default (e.g., `.git`, `.venv`, `node_modules`).

## Usage
Run the script in your project directory:
```
python code_prompt_builder.py
```
Output: `"Done! Scanned '.', output written to '<folder>-code-prompt-YYYY-MM-DD_HHMM.txt' if no errors occurred."`

To scan a specific target directory and output to a custom directory:
```
python code_prompt_builder.py --target-dir "../my_project" --output-dir "./exports"
```
Output: `"Done! Scanned '../my_project', output written to 'exports/my_project-code-prompt-YYYY-MM-DD_HHMM.txt' if no errors occurred."`

## Configuration
The script uses a config file located in the same directory as `code_prompt_builder.py` (e.g., `D:\code_prompt_builder\code_prompt_builder_config.json` if the script is at `D:\code_prompt_builder\`). It defines which files to include or exclude. If missing, it creates one with defaults:
```
{
    "extensions": [".html", ".css", ".js", ".py", ".md", ".json"],
    "exclude_files": [""],
    "ignore_dirs": [".git", ".venv", "venv", "node_modules", "__pycache__", ".idea", ".vscode", "dist", "build", "env", ".pytest_cache"]
}
```
Edit this file to customize extensions (e.g., add ".json"), exclude files (e.g., "test.py"), or ignore directories (e.g., "temp").

## Requirements
* Python 3.x
* No external dependencies

## Git Ignore
Add these lines to your `.gitignore` to exclude files generated by or related to Code Prompt Builder:
```
# Generated output files from Code Prompt Builder
*-code-prompt-*.txt

# The script itself
code_prompt_builder.py

# Optional: Uncomment to ignore config file after initial creation
# code_prompt_builder_config.json
```
Note: Keep `code_prompt_builder_config.json` tracked in Git if you want to version-control your settings. You may want to track `code_prompt_builder.py` in your repo if distributing it, but ignore it locally if modified.

## Dev Notes TO DO
* Review arguments vs config file. 
* Synchronize and refine argument variables.