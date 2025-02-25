# Code Prompt Builder

A Python script to build a consolidated code prompt from development files (e.g., HTML, CSS, JS, Python, Markdown, JSON) for LLM analysis or project review.

## Features
* Collects files based on configurable extensions from the current directory and subdirectories.
* Excludes minified files and user-defined exclusions.
* Outputs file contents with metadata (line count, size, last modified time).
* Generates a timestamped `<folder>-code-prompt-YYYY-MM-DD_HHMM.txt` with token-efficient formatting for LLM prompts.
* Creates a default `code_prompt_builder_config.json` if none exists.
* Command-line arguments that override or extend configuration file settings.
* Robust error handling for permissions, encoding, and file system issues.
* **NEW**: Project summary generation with file type statistics, directory structure, and largest files.
* **NEW**: Focus on specific directories to process only relevant parts of a codebase.
* **NEW**: Automatic token counting for better LLM context management.
* **NEW**: File chunking for large projects that exceed LLM token limits.

## Usage
Run the script in your project directory:
```
python code_prompt_builder.py
```
Output: `"Done! Successfully processed X files with Y lines, Z estimated tokens (size) from 'path'. Output written to '<folder>-code-prompt-YYYY-MM-DD_HHMM.txt'."`

To scan a specific target directory and output to a custom directory:
```
python code_prompt_builder.py --target-dir "../my_project" --output-dir "./exports"
```

## Command-line Arguments
The script offers several command-line arguments for flexible usage:

### Basic Options
- `--target-dir <path>`: Directory to scan for code files (default: current directory)
- `--output-dir <path>`: Directory to save the output file (default: current directory)
- `--extensions <ext1> <ext2> ...`: File extensions to include (overrides config file)

### Inclusion/Exclusion Options
- `--exclude-dir <dirname>`: Additional directory to exclude (can be used multiple times)
- `--exclude-file <filename>`: Additional file to exclude (can be used multiple times)
- `--no-default-excludes`: Ignore default exclude dirs/files from config and only use command line excludes
- `--focus-dir <dirname>`: Only process files in these directories (can be used multiple times)

### Output Formatting Options
- `--chunk-size <size>`: Maximum token size for each output chunk (approximately)
- `--no-summary`: Disable project summary generation (enabled by default)

## Examples

```bash
# Process only HTML and CSS files
python code_prompt_builder.py --extensions .html .css

# Add a specific directory to exclude list
python code_prompt_builder.py --exclude-dir "test_data"

# Only focus on a specific directory and its subdirectories
python code_prompt_builder.py --focus-dir src/components

# Generate chunks with approximately 4000 tokens each
python code_prompt_builder.py --chunk-size 4000

# Disable the project summary
python code_prompt_builder.py --no-summary

# Use only command-line exclusions, ignoring defaults
python code_prompt_builder.py --no-default-excludes --exclude-dir "temp_files"
```

## Configuration
The script uses a config file located in the same directory as `code_prompt_builder.py`. It defines which files to include or exclude. If missing, it creates one with defaults:
```json
{
    "extensions": [".html", ".css", ".js", ".py", ".md", ".json"],
    "exclude_files": [],
    "exclude_dirs": [".git", ".venv", "venv", "node_modules", "__pycache__", 
                    ".idea", ".vscode", "dist", "build", "env", ".pytest_cache"],
    "focus_dirs": [],
    "chunk_size": null,
    "include_summary": true
}
```

### Configuration Priority
The script prioritizes settings in the following order:
1. Command-line arguments override config file settings for specific options (e.g., `--extensions`)
2. Command-line exclusions (files/directories) are added to config file exclusions by default
3. When using `--no-default-excludes`, only command-line exclusions are used

This approach ensures that important exclusions (like `.git`) are maintained by default while allowing for flexibility.

## Project Summary
By default, the script generates a comprehensive summary of your project at the beginning of the output file, including:

* File counts, line counts, and sizes by file type
* Token count estimation (useful for LLM context planning)
* Directory structure with file distribution
* Largest files by line count
* Recently modified files

This summary provides valuable context for LLMs analyzing your codebase.

## File Chunking
For large projects that exceed LLM token limits, the script can automatically split output into multiple files:

```bash
python code_prompt_builder.py --chunk-size 4000
```

This will create multiple files (e.g., `project-code-prompt-date_part1.txt`, `project-code-prompt-date_part2.txt`) with appropriate overlaps at logical file boundaries. Each file will contain approximately the specified number of tokens.

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