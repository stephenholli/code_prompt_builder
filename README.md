# Code Prompt Builder

A Python script to build a consolidated code prompt from development files (e.g., HTML, CSS, JS, Python, Markdown) for LLM analysis or project review.

## Features
* Collects files based on configurable extensions from the current directory and subdirectories.
* Excludes minified files and user-defined exclusions.
* Outputs file contents with metadata (line count, size, last modified time).
* Generates a timestamped `<folder>-code-prompt-YYYY-MM-DD_HHMM.txt` with token-efficient formatting for LLM prompts.
* Creates a default `code_prompt_builder_config.json` if none exists.
* Robust error handling for permissions, encoding, and file system issues.

## Usage
Run the script in your project directory:
```
python code_prompt_builder.py
```
Output: `"Done! Scanned '.', output written to '<folder>-code-prompt-YYYY-MM-DD_HHMM.txt' if no errors occurred."`

For a self-run export of the script and README (from script directory):
```
python code_prompt_builder.py --self-run
```
Output: `"Done! Self-run output written to '<folder>-code-prompt-YYYY-MM-DD_HHMM.txt' if no errors occurred."`

To scan a specific target directory and output to a custom directory:
```
python code_prompt_builder.py --target-dir "../my_project" --output-dir "./exports"
```
Output: `"Done! Scanned '../my_project', output written to 'exports/my_project-code-prompt-YYYY-MM-DD_HHMM.txt' if no errors occurred."`

## Configuration
The script uses a config file located in the same directory as `code_prompt_builder.py` (e.g., `D:\code_prompt_builder\code_prompt_builder_config.json` if the script is at `D:\code_prompt_builder\`). It defines which files to include or exclude. If missing, it creates one with defaults:
```
{
    "extensions": [".html", ".css", ".js", ".py", ".md"],
    "exclude_files": ["code_prompt_builder.py"]
}
```
Edit this file to customize extensions (e.g., add ".json") or exclude additional files (e.g., "test.py").

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

## Example Output
Normal run (scanning "../my_project", Windows):
```
my_project Code Export (2025-02-24 14:07)
###

[HTML] my_project\src\index.html (20L, 512B, Mod: 2025-02-24 11:30)
<html>
  <body><script src="js/script.js"></script></body>
</html>
###

Files: 1
END
```
Normal run (scanning "../my_project", Linux):
```
my_project Code Export (2025-02-24 14:07)
###

[HTML] my_project/src/index.html (20L, 512B, Mod: 2025-02-24 11:30)
<html>
  <body><script src="js/script.js"></script></body>
</html>
###

Files: 1
END
```
Self-run (from script directory, Windows):
```
code_prompt_builder Code Export (2025-02-24 14:07)
###

[PYTHON] code_prompt_builder\code_prompt_builder.py (169L, 9065B, Mod: 2025-02-24 12:35)
<python code here>
###

[MARKDOWN] code_prompt_builder\README.md (123L, 3958B, Mod: 2025-02-24 12:35)
<readme content here>
###

Files: 2
END
```
Self-run (from script directory, Linux):
```
code_prompt_builder Code Export (2025-02-24 14:07)
###

[PYTHON] code_prompt_builder/code_prompt_builder.py (169L, 9065B, Mod: 2025-02-24 12:35)
<python code here>
###

[MARKDOWN] code_prompt_builder/README.md (123L, 3958B, Mod: 2025-02-24 12:35)
<readme content here>
###

Files: 2
END
```

## Notes
This tool is designed for development workflows and LLM co-design. It skips hidden directories (e.g., `.git`) and handles errors gracefully. Paths use platform-native separators (`\` on Windows, `/` on Linux).