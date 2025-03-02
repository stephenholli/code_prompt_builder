# Code Prompt Builder

A Python script that builds consolidated code prompts from your development files (HTML, CSS, JS, Python, Markdown, JSON, etc.) for LLM analysis and project reviews.

## Features
* Creates a single text file containing all your project's code with helpful metadata
* Generates a comprehensive project summary with file statistics and directory structure
* Automatically excludes minified files and common non-code directories (.git, node_modules, etc.)
* Supports custom file inclusion/exclusion patterns and directory focusing
* Estimates token count for LLM context management
* Splits large codebases into manageable chunks for LLM token limits
* Handles file path variations for exclusions (e.g., ".\file.txt" and ".\folder\file.txt")
* Provides abbreviated command options for faster workflow
* Supports processing a single file instead of a whole directory

## Usage
Run the script in your project directory:
```bash
python code_prompt_builder.py
```

The output will be saved as: `<folder>-code-prompt-YYYY-MM-DD_HHMM.txt`

To analyze a specific project and save to a custom location:
```bash
python code_prompt_builder.py --target-dir "../my_project" --output-dir "./exports"
```

To process a single file:
```bash
python code_prompt_builder.py --single-file "path/to/my_file.py"
```

## Command-line Arguments

### Basic Options
- `--target-dir <path>` or `-t <path>`: Directory to scan for code files (default: current directory)
- `--output-dir <path>` or `-o <path>`: Directory to save the output file (default: current directory)
- `--extensions <ext1> <ext2> ...`: File extensions to include (default: .html, .css, .js, .py, .md, .json)
- `--single-file <path>` or `-s <path>`: Process only a single specified file instead of a directory

### Inclusion/Exclusion Options
- `--exclude-dir <dirname>` or `-d <dirname>`: Additional directory to exclude (can be used multiple times)
- `--exclude-file <filename>` or `-e <filename>`: Additional file to exclude (can be used multiple times)
- `--no-default-excludes`: Ignore default exclude dirs/files and only use command line excludes
- `--focus-dir <dirname>` or `-f <dirname>`: Only process files in these directories and their subdirectories

### Output Formatting Options
- `--chunk-size <size>` or `-c <size>`: Maximum token size for each output chunk (default: no chunking)
- `--no-summary`: Disable project summary generation (summary is enabled by default)

## Common Examples

```bash
# Process only HTML and CSS files
python code_prompt_builder.py --extensions .html .css

# Exclude specific directories from analysis
python code_prompt_builder.py --exclude-dir "test_data" --exclude-dir "legacy_code"

# Focus only on specific parts of a codebase
python code_prompt_builder.py --focus-dir "src/components" --focus-dir "src/utils"

# Generate smaller chunks for large projects (approx. 4000 tokens each)
python code_prompt_builder.py --chunk-size 4000

# Process only a single file (output will be named based on the file name)
python code_prompt_builder.py --single-file "path/to/my_file.py"

# Use abbreviated options
python code_prompt_builder.py -t "../project" -o "./output" -d "node_modules" -e "config.json"

# Process a single file with abbreviated options
python code_prompt_builder.py -s "app.py" -o "./exports"
```

## Default Configuration
The script uses a config file (`code_prompt_builder_config.json`) located in the same directory as the script. If missing, it creates one with these defaults:

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
1. Command-line arguments override config file settings
2. Command-line exclusions are added to config file exclusions by default
3. With `--no-default-excludes`, only command-line exclusions are used

## Project Summary
The generated summary includes:

* **Project Overview**: Total files, lines, size, and estimated token count
* **Files by Type**: Breakdown of file extensions with counts, lines, and sizes
* **Directory Structure**: Complete file hierarchy with details for each file
* **File Details**: Each file's line count, size, and last modified date

## Output Format
The generated file follows this structure:
```
<folder_name> Code Export (YYYY-MM-DD HH:MM)
###
[Project Summary]
###
<file_path> (<line_count>L, <file_size>, Mod: <modified_date>)
[File Content]
###
<next_file>...
```

## File Chunking
For large projects, use the `--chunk-size` option to split output into multiple files, each containing approximately the specified number of tokens:

```bash
python code_prompt_builder.py --chunk-size 4000
```

This creates files like `project-code-prompt-date_part1.txt`, `project-code-prompt-date_part2.txt`, etc.

## Requirements
* Python 3.x
* No external dependencies

## To Do
* Implement generation of report from a specific git branch