import os
import json
from datetime import datetime
import argparse
import re

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
                       ".idea", ".vscode", "dist", "build", "env", ".pytest_cache"],
        "focus_dirs": [],
        "chunk_size": None,
        "include_summary": True
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
        
        # Validate config structure and add any missing defaults
        for key, value in defaults.items():
            if key not in config:
                config[key] = value
            elif not isinstance(config[key], type(value)):
                if value is None and config[key] is not None:
                    # Allow non-None values when default is None
                    pass
                else:
                    print(f"Warning: Config key '{key}' has incorrect type. Using default.")
                    config[key] = value
        
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
    
    # For focus_dirs, we also want to add to the config values
    if args.focus_dirs:
        merged_config["focus_dirs"] = list(set(merged_config.get("focus_dirs", [])) | set(args.focus_dirs))
    
    # Override chunk_size if specified
    if args.chunk_size is not None:
        merged_config["chunk_size"] = args.chunk_size
    
    # Override include_summary based on argument
    if args.no_summary:
        merged_config["include_summary"] = False
    
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

def generate_project_summary(file_stats, target_dir, total_size, binary_count):
    """
    Generate a project summary based on collected file statistics.
    
    Args:
        file_stats: Dictionary mapping file paths to their statistics
        target_dir: The root directory of the project
        total_size: Total size of all files in bytes
        binary_count: Number of binary files skipped
    
    Returns:
        String containing the project summary
    """
    folder_name = os.path.basename(target_dir)
    
    # Group files by extension
    files_by_ext = {}
    for file_path, stats in file_stats.items():
        ext = os.path.splitext(file_path)[1].lower() or "(no extension)"
        if ext not in files_by_ext:
            files_by_ext[ext] = []
        files_by_ext[ext].append((file_path, stats))
    
    # Generate summary
    summary = [f"## {folder_name} PROJECT SUMMARY", ""]
    summary.append(f"Root Directory: {target_dir}")
    summary.append(f"Total Files: {len(file_stats)}")
    summary.append(f"Total Size: {format_file_size(total_size)}")
    if binary_count > 0:
        summary.append(f"Binary Files Skipped: {binary_count}")
    summary.append("")
    
    # Files by type
    summary.append("### Files by Type")
    for ext, files in sorted(files_by_ext.items()):
        ext_total_lines = sum(stats['lines'] for _, stats in files)
        ext_total_size = sum(stats['size'] for _, stats in files)
        summary.append(f"- {ext}: {len(files)} files, {ext_total_lines} lines, {format_file_size(ext_total_size)}")
    
    # Directory structure
    summary.append("")
    summary.append("### Directory Structure")
    
    # Group files by directory
    dirs = {}
    for file_path, stats in file_stats.items():
        dir_path = os.path.dirname(file_path)
        if not dir_path:
            dir_path = "."
        if dir_path not in dirs:
            dirs[dir_path] = []
        dirs[dir_path].append((file_path, stats))
    
    # Sort directories by file count
    sorted_dirs = sorted(dirs.items(), key=lambda x: len(x[1]), reverse=True)
    for dir_path, files in sorted_dirs[:10]:  # Show top 10 directories
        dir_total_lines = sum(stats['lines'] for _, stats in files)
        summary.append(f"- {dir_path}: {len(files)} files, {dir_total_lines} lines")
    
    if len(sorted_dirs) > 10:
        summary.append(f"  ... and {len(sorted_dirs) - 10} more directories")
    
    # Largest files
    summary.append("")
    summary.append("### Largest Files (by line count)")
    largest_files = sorted(file_stats.items(), key=lambda x: x[1]['lines'], reverse=True)[:10]
    for file_path, stats in largest_files:
        summary.append(f"- {file_path}: {stats['lines']} lines, {format_file_size(stats['size'])}")
    
    # Recently modified files
    summary.append("")
    summary.append("### Recently Modified Files")
    recent_files = sorted(file_stats.items(), key=lambda x: x[1]['modified'], reverse=True)[:10]
    for file_path, stats in recent_files:
        mod_time = datetime.fromtimestamp(stats['modified']).strftime("%Y-%m-%d %H:%M")
        summary.append(f"- {file_path}: {mod_time}")
    
    return "\n".join(summary)

def chunk_output(content, max_tokens=4000, overlap=200):
    """
    Split content into chunks of approximately max_tokens with some overlap.
    
    Args:
        content: The full content string to split
        max_tokens: Maximum tokens per chunk (approximated as characters/4)
        overlap: Number of tokens to overlap between chunks
        
    Returns:
        A list of content chunks
    """
    # Simple approximation: a token is roughly ~4 characters
    chars_per_token = 4
    max_chars = max_tokens * chars_per_token
    overlap_chars = overlap * chars_per_token
    
    chunks = []
    start = 0
    
    while start < len(content):
        end = min(start + max_chars, len(content))
        
        # Try to end at a natural boundary (###)
        if end < len(content):
            # Look for ### marker
            boundary = content.rfind("\n###\n", start, end)
            if boundary != -1:
                end = boundary + 5  # Include the ### and newlines
        
        chunks.append(content[start:end])
        
        # Start next chunk with some overlap
        if end < len(content):
            # Find a good starting point in the overlap region
            overlap_start = max(start, end - overlap_chars)
            next_start = content.find("\n###\n", overlap_start)
            if next_start == -1:
                start = end
            else:
                start = next_start + 1  # Start after the newline
        else:
            break
    
    return chunks

def build_code_prompt(target_dir=".", output_dir=".", config=None):
    """
    Build code prompt using the provided configuration.
    
    Args:
        target_dir: Directory to scan for code files
        output_dir: Directory to save the output file(s)
        config: Configuration dictionary
        
    Returns:
        Tuple containing:
        - success: Boolean indicating if the operation was successful
        - file_count: Number of files processed
        - total_lines: Total number of lines processed
        - total_size: Total size of processed files in bytes
        - binary_count: Number of binary files skipped
        - errors: List of error messages
        - output_files: List of output file paths
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
    focus_dirs_set = set(config.get("focus_dirs", []))
    
    errors = []
    file_count = 0
    total_lines = 0
    total_size = 0
    binary_count = 0
    file_stats = {}  # For project summary
    
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Collect file content and stats
        full_content = []
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        full_content.append(f"{folder_name} Code Export ({current_date})")
        full_content.append("###")
        
        # Process files based on configuration
        extensions = tuple(config["extensions"])
        
        for root, dirs, files in os.walk(target_dir):
            # Filter directories based on our exclude list
            dirs[:] = [d for d in dirs if d not in exclude_dirs_set]
            
            # Skip directories not in focus (if focus is specified)
            if focus_dirs_set:
                rel_path = os.path.relpath(root, target_dir)
                if rel_path != '.':
                    # Check if this directory is in focus or is a parent of a focus dir
                    is_in_focus = any(fd == rel_path or 
                                     rel_path.startswith(fd + os.sep) or 
                                     fd.startswith(rel_path + os.sep) 
                                     for fd in focus_dirs_set)
                    if not is_in_focus:
                        continue
            
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
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as infile:
                        content = infile.read()
                        line_count = len(content.splitlines())
                        total_lines += line_count
                        file_size = os.path.getsize(file_path)
                        total_size += file_size
                    
                    # Store file stats for project summary
                    file_stats[relative_path] = {
                        'lines': line_count,
                        'size': file_size,
                        'modified': os.path.getmtime(file_path)
                    }
                    
                    # Format file size to be human-readable
                    formatted_size = format_file_size(file_size)
                    
                    mod_time = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M")
                    # Add file header and content
                    full_content.append(f"{display_path} ({line_count}L, {formatted_size}, Mod: {mod_time})")
                    full_content.append(content)
                    full_content.append("###")
                except PermissionError:
                    errors.append(f"{file_path}: No permission to read file.")
                except UnicodeDecodeError:
                    errors.append(f"{file_path}: File is not UTF-8 encoded.")
                    binary_count += 1
                except (OSError, ValueError) as e:
                    errors.append(f"{file_path}: Failed to process ({str(e)}).")
        
        # Add summary information 
        summary = f"Files: {file_count}, Lines: {total_lines}, Size: {format_file_size(total_size)}"
        if binary_count > 0:
            summary += f" (Skipped {binary_count} binary files)"
        full_content.append(summary)
        
        if errors:
            full_content.append("\nErrors:")
            for error in errors:
                full_content.append(f"- {error}")
        
        full_content.append("END")
        
        # Convert to a single string
        content_str = "\n".join(full_content)
        
        # Generate project summary if enabled
        if config.get("include_summary", True) and file_count > 0:
            project_summary = generate_project_summary(file_stats, target_dir, total_size, binary_count)
            # Insert summary after the title but before the first file
            summary_pos = content_str.find("\n###\n") + 5
            content_str = content_str[:summary_pos] + project_summary + "\n\n###\n" + content_str[summary_pos:]
        
        # Handle chunking if specified
        output_files = []
        chunk_size = config.get("chunk_size")
        
        if chunk_size and chunk_size > 0:
            chunks = chunk_output(content_str, max_tokens=chunk_size)
            for i, chunk in enumerate(chunks):
                # Create filename for this chunk
                if len(chunks) > 1:
                    chunk_file = f"{os.path.splitext(output_file)[0]}_part{i+1}.txt"
                else:
                    chunk_file = output_file
                
                with open(chunk_file, 'w', encoding='utf-8') as outfile:
                    outfile.write(chunk)
                
                output_files.append(chunk_file)
        else:
            # Single file output
            with open(output_file, 'w', encoding='utf-8') as outfile:
                outfile.write(content_str)
            output_files.append(output_file)
        
        return True, file_count, total_lines, total_size, binary_count, errors, output_files
        
    except PermissionError:
        print(f"Error: No permission to write '{output_file}'. Aborting.")
        return False, file_count, total_lines, total_size, binary_count, errors + [f"No permission to write '{output_file}'"], []
    except OSError as e:
        print(f"Error: Failed to write '{output_file}' ({str(e)}). Aborting.")
        return False, file_count, total_lines, total_size, binary_count, errors + [f"Failed to write '{output_file}' ({str(e)})"], []
    except Exception as e:
        print(f"Critical error during file collection: {str(e)}. Aborting.")
        return False, file_count, total_lines, total_size, binary_count, errors + [f"Critical error: {str(e)}"], []

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build a code prompt from project files.")
    parser.add_argument("--target-dir", default=".", help="Directory to scan for code files (default: current directory)")
    parser.add_argument("--output-dir", default=".", help="Directory to save the output file (default: current directory)")
    
    # Exclusion options
    parser.add_argument("--exclude-dir", action="append", dest="exclude_dirs", default=[], 
                      help="Additional directory to exclude (can be used multiple times)")
    parser.add_argument("--exclude-file", action="append", dest="exclude_files", default=[], 
                      help="Additional file to exclude (can be used multiple times)")
    parser.add_argument("--no-default-excludes", action="store_true", 
                      help="Ignore default exclude dirs/files from config and only use command line excludes")
    
    # File selection options
    parser.add_argument("--extensions", nargs="+", default=None,
                      help="File extensions to include (overrides config file)")
    parser.add_argument("--focus-dir", action="append", dest="focus_dirs", default=[],
                      help="Only process files in these directories (can be used multiple times)")
    
    # Output formatting options
    parser.add_argument("--chunk-size", type=int, default=None,
                      help="Maximum token size for each output chunk (approximately)")
    parser.add_argument("--no-summary", action="store_true", 
                      help="Disable project summary generation (enabled by default)")
    
    args = parser.parse_args()
    
    # Get absolute path for target directory
    target_dir_abs = os.path.abspath(args.target_dir)
    
    # Load config and merge with command line arguments
    config = load_config()
    merged_config = merge_config_with_args(config, args)
    
    print("Building code prompt...")
    success, file_count, total_lines, total_size, binary_count, errors, output_files = build_code_prompt(
        target_dir=args.target_dir,
        output_dir=args.output_dir,
        config=merged_config
    )
    
    if success:
        formatted_size = format_file_size(total_size)
        binary_msg = f" (Skipped {binary_count} binary files)" if binary_count > 0 else ""
        
        if not errors:
            print(f"Done! Successfully processed {file_count} files with {total_lines} lines ({formatted_size}) from '{target_dir_abs}'{binary_msg}.")
            if len(output_files) > 1:
                print(f"Output was split into {len(output_files)} files:")
                for file in output_files:
                    print(f"- {os.path.abspath(file)}")
            else:
                print(f"Output written to '{os.path.abspath(output_files[0])}'.")
        else:
            print(f"Completed with warnings! Processed {file_count} files with {total_lines} lines ({formatted_size}) from '{target_dir_abs}'{binary_msg}.")
            print(f"Encountered {len(errors)} errors. See output file(s) for details.")
    else:
        print(f"Failed to complete the code prompt generation. Encountered {len(errors)} errors.")