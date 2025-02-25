import os
import json
from datetime import datetime
import argparse

def get_file_type(filename):
    """
    Get the file type identifier based on file extension.
    Returns a standardized identifier suitable for display in the prompt.
    """
    # Handle files without extensions (like Dockerfile)
    if '.' not in filename:
        lower_name = filename.lower()
        if lower_name in ['dockerfile', 'makefile']:
            return lower_name.upper()
        return 'UNKNOWN'
        
    # Get extension and convert to lowercase
    ext = filename.lower().split('.')[-1]
    
    # Common file types - focused on the most frequently used
    file_types = {
        # Web Development
        'html': 'HTML', 'htm': 'HTML',
        'css': 'CSS', 'scss': 'SCSS', 'sass': 'SASS',
        'js': 'JAVASCRIPT', 'jsx': 'JSX', 'ts': 'TYPESCRIPT', 'tsx': 'TSX',
        
        # Programming Languages
        'py': 'PYTHON', 'pyw': 'PYTHON',
        'java': 'JAVA', 'kt': 'KOTLIN',
        'c': 'C', 'h': 'C_HEADER', 'cpp': 'CPP', 'hpp': 'CPP_HEADER',
        'cs': 'CSHARP', 'go': 'GO', 'rs': 'RUST', 'rb': 'RUBY', 'php': 'PHP',
        
        # Data Formats
        'json': 'JSON', 'yaml': 'YAML', 'yml': 'YAML', 'xml': 'XML', 'csv': 'CSV',
        
        # Documentation
        'md': 'MARKDOWN', 'txt': 'TEXT',
        
        # Shell/Scripts
        'sh': 'SHELL', 'bash': 'BASH', 'bat': 'BATCH', 'ps1': 'POWERSHELL'
    }
    
    # Return the mapped type or uppercase extension if not found
    return file_types.get(ext, ext.upper())

def format_file_size(size_in_bytes):
    """
    Format file size from bytes to human-readable format (KB, MB).
    """
    if size_in_bytes < 1024:
        return f"{size_in_bytes} bytes"
    elif size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.1f} KB"
    else:
        return f"{size_in_bytes / (1024 * 1024):.2f} MB"

def is_binary_file(file_path, sample_size=1024):
    """
    Simple check if a file is binary by testing if it can be decoded as UTF-8.
    A more straightforward approach focused on the primary use case of identifying
    text files that can be meaningfully read.
    
    Args:
        file_path: Path to the file to check
        sample_size: Number of bytes to read for detection
        
    Returns:
        bool: True if the file appears to be binary, False otherwise
    """
    try:
        # Read the first part of the file
        with open(file_path, 'rb') as f:
            sample = f.read(sample_size)
            
        # Empty files are considered text
        if not sample:
            return False
            
        # Quick check: if there are null bytes, it's almost certainly binary
        if b'\x00' in sample:
            return True
            
        # Try to decode as utf-8 - if it works, it's probably text
        try:
            sample.decode('utf-8')
            return False
        except UnicodeDecodeError:
            return True
            
    except IOError:
        # If we can't read the file, skip it
        return True

def load_config():
    """
    Load config from file or create default if not exists.
    Returns the config dictionary.
    """
    # Define the settings file path relative to the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(script_dir, "code_prompt_builder_config.json")
    
    defaults = {
        "extensions": [".html", ".css", ".js", ".py", ".md", ".json"],
        "exclude_files": [],
        "exclude_dirs": [".git", ".venv", "venv", "node_modules", "__pycache__", 
                       ".idea", ".vscode", "dist", "build", "env", ".pytest_cache"]
    }
    
    if not os.path.exists(config_file):
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(defaults, f, indent=4)
            print(f"Created default '{config_file}'.")
        except PermissionError:
            print(f"Error: No permission to create '{config_file}'. Using defaults.")
            return defaults
        except OSError as e:
            print(f"Error: Failed to create '{config_file}' ({str(e)}). Using defaults.")
            return defaults
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Validate config structure
        if "extensions" not in config or not isinstance(config["extensions"], list):
            raise ValueError("'extensions' must be a list.")
        if "exclude_files" not in config or not isinstance(config["exclude_files"], list):
            raise ValueError("'exclude_files' must be a list.")
        if "exclude_dirs" not in config or not isinstance(config["exclude_dirs"], list):
            raise ValueError("'exclude_dirs' must be a list.")
        
        return config
    except PermissionError:
        print(f"Error: No permission to read '{config_file}'. Using defaults.")
        return defaults
    except json.JSONDecodeError:
        print(f"Error: '{config_file}' is corrupted or invalid JSON. Using defaults.")
        return defaults
    except (OSError, ValueError) as e:
        print(f"Error: Failed to load '{config_file}' ({str(e)}). Using defaults.")
        return defaults

def merge_config_with_args(config, args):
    """
    Merge config with command line arguments, prioritizing command line arguments
    while preserving defaults for exclusions.
    """
    merged_config = config.copy()
    
    # For extensions, if specified in args, completely override config
    if args.extensions:
        merged_config["extensions"] = args.extensions
    
    # For exclude_files and exclude_dirs, we want to ADD command line exclusions
    # to the defaults from config, not replace them
    # This ensures we keep excluding important directories like .git, node_modules, etc.
    if args.exclude_files:
        merged_config["exclude_files"] = list(set(merged_config["exclude_files"]) | set(args.exclude_files))
    
    if args.exclude_dirs:
        merged_config["exclude_dirs"] = list(set(merged_config["exclude_dirs"]) | set(args.exclude_dirs))
    
    # If --no-default-excludes flag is set, remove default exclusions and only use provided ones
    if args.no_default_excludes:
        if args.exclude_files:
            merged_config["exclude_files"] = list(set(args.exclude_files))
        else:
            merged_config["exclude_files"] = []
            
        if args.exclude_dirs:
            merged_config["exclude_dirs"] = list(set(args.exclude_dirs))
        else:
            merged_config["exclude_dirs"] = []
    
    return merged_config

def build_code_prompt(target_dir=".", output_dir=".", config=None):
    """
    Build code prompt using the provided configuration.
    """
    if config is None:
        config = load_config()
    
    # Normalize paths and get folder name from target_dir
    target_dir = os.path.abspath(target_dir)
    folder_name = os.path.basename(target_dir)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    output_file = os.path.join(output_dir, f"{folder_name}-code-prompt-{timestamp}.txt")
    
    exclude_dirs_set = set(config["exclude_dirs"])
    exclude_files_set = set(config["exclude_files"])
    
    errors = []
    file_count = 0
    total_lines = 0
    total_size = 0
    binary_count = 0
    
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as outfile:
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            outfile.write(f"{folder_name} Code Export ({current_date})\n###\n")
            
            # Process files based on configuration
            extensions = tuple(config["extensions"])
            
            for root, dirs, files in os.walk(target_dir):
                # Filter directories based on our exclude list
                dirs[:] = [d for d in dirs if d not in exclude_dirs_set]
                
                try:
                    project_files = sorted([
                        f for f in files 
                        if f.lower().endswith(extensions) and 
                        not f.lower().endswith(tuple(f".min{e}" for e in extensions)) and 
                        f not in exclude_files_set
                    ])
                except TypeError as e:
                    errors.append(f"Error processing directory '{root}': Invalid extension type ({str(e)}).")
                    continue
                
                for filename in project_files:
                    file_path = os.path.join(root, filename)
                    # Display path relative to target_dir root
                    relative_path = os.path.relpath(file_path, target_dir)
                    display_path = os.path.join(folder_name, relative_path)
                    
                    # Check if file is binary before attempting to read as text
                    if is_binary_file(file_path):
                        binary_count += 1
                        continue
                    
                    file_count += 1
                    
                    # Use our file type detection function
                    file_type = get_file_type(filename)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as infile:
                            content = infile.read()
                            line_count = len(content.splitlines())
                            total_lines += line_count
                            file_size = os.path.getsize(file_path)
                            total_size += file_size
                        
                        # Format file size to be human-readable
                        formatted_size = format_file_size(file_size)
                        
                        mod_time = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M")
                        outfile.write(f"[{file_type}] {display_path} ({line_count}L, {formatted_size}, Mod: {mod_time})\n")
                        outfile.write(content)
                        outfile.write("\n###\n")
                    except PermissionError:
                        errors.append(f"{file_path}: No permission to read file.")
                    except UnicodeDecodeError:
                        errors.append(f"{file_path}: File is not UTF-8 encoded.")
                    except (OSError, ValueError) as e:
                        errors.append(f"{file_path}: Failed to process ({str(e)}).")
            
            # Add summary information at the end with totals
            summary = f"Files: {file_count}, Lines: {total_lines}, Size: {format_file_size(total_size)}"
            if binary_count > 0:
                summary += f" (Skipped {binary_count} binary files)"
            outfile.write(summary)
            
            if errors:
                outfile.write("\nErrors:\n" + "\n".join([f"- {e}" for e in errors]))
            outfile.write("\nEND\n")
        
        return True, file_count, total_lines, total_size, binary_count, errors, output_file
        
    except PermissionError:
        print(f"Error: No permission to write '{output_file}'. Aborting.")
        return False, file_count, total_lines, total_size, binary_count, errors + [f"No permission to write '{output_file}'"], None
    except OSError as e:
        print(f"Error: Failed to write '{output_file}' ({str(e)}). Aborting.")
        return False, file_count, total_lines, total_size, binary_count, errors + [f"Failed to write '{output_file}' ({str(e)})"], None
    except Exception as e:
        print(f"Critical error during file collection: {str(e)}. Aborting.")
        return False, file_count, total_lines, total_size, binary_count, errors + [f"Critical error: {str(e)}"], None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build a code prompt from project files.")
    parser.add_argument("--target-dir", default=".", help="Directory to scan for code files (default: current directory)")
    parser.add_argument("--output-dir", default=".", help="Directory to save the output file (default: current directory)")
    
    # Align argument names with config file structure
    parser.add_argument("--exclude-dir", action="append", dest="exclude_dirs", default=[], 
                      help="Additional directory to exclude (can be used multiple times)")
    parser.add_argument("--exclude-file", action="append", dest="exclude_files", default=[], 
                      help="Additional file to exclude (can be used multiple times)")
    parser.add_argument("--extensions", nargs="+", default=None,
                      help="File extensions to include (overrides config file)")
    parser.add_argument("--no-default-excludes", action="store_true", 
                      help="Ignore default exclude dirs/files from config and only use command line excludes")
    
    args = parser.parse_args()
    
    # Get absolute path for target directory
    target_dir_abs = os.path.abspath(args.target_dir)
    
    # Load config and merge with command line arguments
    config = load_config()
    merged_config = merge_config_with_args(config, args)
    
    print("Building code prompt...")
    success, file_count, total_lines, total_size, binary_count, errors, output_file = build_code_prompt(
        target_dir=args.target_dir,
        output_dir=args.output_dir,
        config=merged_config
    )
    
    if success:
        formatted_size = format_file_size(total_size)
        binary_msg = f" (Skipped {binary_count} binary files)" if binary_count > 0 else ""
        
        if not errors:
            print(f"Done! Successfully processed {file_count} files with {total_lines} lines ({formatted_size}) from '{target_dir_abs}'{binary_msg}.")
            print(f"Output written to '{os.path.abspath(output_file)}'.")
        else:
            print(f"Completed with warnings! Processed {file_count} files with {total_lines} lines ({formatted_size}) from '{target_dir_abs}'{binary_msg}.")
            print(f"Encountered {len(errors)} errors. See '{os.path.abspath(output_file)}' for details.")
    else:
        print(f"Failed to complete the code prompt generation. Encountered {len(errors)} errors.")