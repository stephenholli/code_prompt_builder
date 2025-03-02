import os
import json
from datetime import datetime
import argparse

def format_file_size(size_in_bytes):
    """Format file size from bytes to human-readable format (KB, MB)."""
    if size_in_bytes < 1024:
        return f"{size_in_bytes} bytes"
    elif size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.1f} KB"
    else:
        return f"{size_in_bytes / (1024 * 1024):.2f} MB"

def is_binary_file(file_path, sample_size=1024):
    """Check if a file is binary by testing UTF-8 decoding."""
    try:
        with open(file_path, 'rb') as f:
            sample = f.read(sample_size)
        if not sample:
            return False
        if b'\x00' in sample:
            return True
        sample.decode('utf-8')
        return False
    except IOError:
        return True

def load_config():
    """Load config from file or create default if not exists."""
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
        except (PermissionError, OSError) as e:
            print(f"Error creating '{config_file}' ({str(e)}). Using defaults.")
            return defaults
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        for key, value in defaults.items():
            if key not in config:
                config[key] = value
            elif not isinstance(config[key], type(value)):
                if value is None and config[key] is not None:
                    pass
                else:
                    print(f"Warning: Config key '{key}' type mismatch. Using default.")
                    config[key] = value
        return config
    except (json.JSONDecodeError, PermissionError, OSError) as e:
        print(f"Error loading '{config_file}' ({str(e)}). Using defaults.")
        return defaults

def merge_config_with_args(config, args):
    """Merge config with command-line args, normalizing exclusion paths."""
    merged_config = config.copy()
    if args.extensions:
        merged_config["extensions"] = args.extensions
    exclude_files = config["exclude_files"]
    if args.exclude_files:
        if args.no_default_excludes:
            exclude_files = args.exclude_files
        else:
            exclude_files = list(set(exclude_files) | set(args.exclude_files))
    merged_config["exclude_files"] = [os.path.normpath(f.lstrip('.\\' if os.sep == '\\' else './')) 
                                     for f in exclude_files]
    exclude_dirs = config["exclude_dirs"]
    if args.exclude_dirs:
        if args.no_default_excludes:
            exclude_dirs = args.exclude_dirs
        else:
            exclude_dirs = list(set(exclude_dirs) | set(args.exclude_dirs))
    merged_config["exclude_dirs"] = exclude_dirs
    if args.focus_dirs:
        merged_config["focus_dirs"] = list(set(config.get("focus_dirs", [])) | set(args.focus_dirs))
    if args.chunk_size is not None:
        merged_config["chunk_size"] = args.chunk_size
    if args.no_summary:
        merged_config["include_summary"] = False
    return merged_config

def build_tree(file_stats, target_dir):
    """Build a directory tree from file statistics."""
    tree = {}
    for relative_path, stats in file_stats.items():
        if not isinstance(stats, dict):
            print(f"Warning: Invalid stats for '{relative_path}': {stats}")
            continue
        parts = relative_path.split(os.sep)
        current = tree
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = stats
    return tree

def generate_tree_lines(tree, prefix=""):
    """Generate directory tree lines with file details."""
    lines = []
    sorted_keys = sorted(tree.keys())
    for i, key in enumerate(sorted_keys):
        is_last = i == len(sorted_keys) - 1
        if isinstance(tree[key], dict) and 'lines' not in tree[key]:
            # Directory: recurse into it
            lines.append(f"{prefix}{'└── ' if is_last else '├── '}{key}/")
            sub_prefix = prefix + ('    ' if is_last else '│   ')
            sub_lines = generate_tree_lines(tree[key], sub_prefix)
            lines.extend(sub_lines)
        elif isinstance(tree[key], dict) and 'lines' in tree[key]:
            # File: display stats
            stats = tree[key]
            formatted_size = format_file_size(stats['size'])
            mod_time = stats['modified']
            lines.append(f"{prefix}{'└── ' if is_last else '├── '}{key}: {stats['lines']} lines, "
                         f"{formatted_size}, Mod: {mod_time}")
        else:
            # Error case
            lines.append(f"{prefix}{'└── ' if is_last else '├── '}{key}: [Error: Invalid stats]")
    return lines

def generate_project_summary(file_stats, target_dir, total_size, total_tokens, binary_count):
    """Generate a project summary with a detailed directory structure."""
    folder_name = os.path.basename(target_dir)
    summary = [f"## {folder_name} PROJECT SUMMARY", ""]
    summary.append(f"Root Directory: {target_dir}")
    summary.append(f"Total Files: {len(file_stats)}")
    summary.append(f"Total Size: {format_file_size(total_size)}")
    summary.append(f"Estimated Code Tokens: {total_tokens:,}")
    if binary_count > 0:
        summary.append(f"Binary Files Skipped: {binary_count}")
    summary.append("")

    files_by_ext = {}
    for file_path, stats in file_stats.items():
        if not isinstance(stats, dict):
            continue
        ext = os.path.splitext(file_path)[1].lower() or "(no extension)"
        if ext not in files_by_ext:
            files_by_ext[ext] = []
        files_by_ext[ext].append((file_path, stats))
    
    summary.append("### Files by Type")
    for ext, files in sorted(files_by_ext.items()):
        ext_total_lines = sum(stats['lines'] for _, stats in files)
        ext_total_size = sum(stats['size'] for _, stats in files)
        summary.append(f"- {ext}: {len(files)} files, {ext_total_lines} lines, "
                       f"{format_file_size(ext_total_size)}")
    
    summary.append("")
    summary.append("### Directory Structure")
    tree = build_tree(file_stats, target_dir)
    tree_lines = generate_tree_lines(tree)
    summary.extend(tree_lines)
    
    return "\n".join(summary)

def chunk_output(content, max_tokens=4000, overlap=200):
    """Split content into chunks with specified token size and overlap."""
    chars_per_token = 4
    max_chars = max_tokens * chars_per_token
    overlap_chars = overlap * chars_per_token
    chunks = []
    start = 0
    while start < len(content):
        end = min(start + max_chars, len(content))
        if end < len(content):
            boundary = content.rfind("\n###\n", start, end)
            if boundary != -1:
                end = boundary + 5
        chunks.append(content[start:end])
        if end < len(content):
            overlap_start = max(start, end - overlap_chars)
            next_start = content.find("\n###\n", overlap_start)
            start = next_start + 1 if next_start != -1 else end
        else:
            break
    return chunks

def build_code_prompt(target_dir=".", output_dir=".", config=None, single_file=None):
    """Build code prompt using filesystem only, with optional single-file processing."""
    if config is None:
        config = load_config()
    
    target_dir = os.path.abspath(target_dir)
    folder_name = os.path.basename(target_dir)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    
    # Set output file name based on whether single_file is specified
    if single_file:
        # Normalize single_file by removing leading './' or '.\'
        base_name = single_file.strip()
        if base_name.startswith('./') or base_name.startswith('.\\'):
            base_name = base_name[2:]
        base_name = base_name.replace(os.sep, "_")
        base_name = os.path.splitext(base_name)[0]
        output_file = os.path.join(output_dir, f"{base_name}-code-prompt-{timestamp}.txt")
    else:
        output_file = os.path.join(output_dir, f"{folder_name}-code-prompt-{timestamp}.txt")
    
    exclude_dirs_set = set(config["exclude_dirs"])
    exclude_files_set = set(config["exclude_files"])
    focus_dirs_set = set(config.get("focus_dirs", []))
    
    errors = []
    file_count = 0
    total_lines = 0
    total_size = 0
    total_chars = 0
    binary_count = 0
    file_stats = {}
    
    try:
        os.makedirs(output_dir, exist_ok=True)
        full_content = [f"{folder_name} Code Export ({datetime.now().strftime('%Y-%m-%d %H:%M')})", "###"]
        extensions = tuple(config["extensions"])
        
        # Determine files to process
        if single_file:
            file_path = os.path.abspath(os.path.join(target_dir, single_file))
            if not os.path.exists(file_path):
                print(f"Error: Path '{file_path}' does not exist.")
                return False, 0, 0, 0, 0, 0, [f"Path '{file_path}' does not exist."], []
            if not os.path.isfile(file_path):
                print(f"Error: '{file_path}' is not a file.")
                return False, 0, 0, 0, 0, 0, [f"'{file_path}' is not a file."], []
            files_to_process = [file_path]
        else:
            files_to_process = []
            for root, dirs, files in os.walk(target_dir):
                dirs[:] = [d for d in dirs if d not in exclude_dirs_set]
                if focus_dirs_set:
                    rel_path = os.path.relpath(root, target_dir)
                    if rel_path != '.':
                        is_in_focus = any(fd == rel_path or 
                                         rel_path.startswith(fd + os.sep) or 
                                         fd.startswith(rel_path + os.sep) 
                                         for fd in focus_dirs_set)
                        if not is_in_focus:
                            continue
                project_files = sorted([
                    f for f in files 
                    if f.lower().endswith(extensions) and 
                    not f.lower().endswith(tuple(f".min{e}" for e in extensions)) and 
                    os.path.relpath(os.path.join(root, f), target_dir) not in exclude_files_set
                ])
                for filename in project_files:
                    file_path = os.path.join(root, filename)
                    files_to_process.append(file_path)
        
        # Process each file
        for file_path in files_to_process:
            try:
                relative_path = os.path.relpath(file_path, target_dir)
                if relative_path.startswith('..' + os.sep):
                    display_path = file_path  # Use full path if outside target_dir
                else:
                    display_path = os.path.join(folder_name, relative_path)  # Use relative path if inside
            except ValueError:
                display_path = file_path  # Use full path for edge cases (e.g., different drives on Windows)
            
            if is_binary_file(file_path):
                binary_count += 1
                errors.append(f"{file_path}: Skipped (binary file)")
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as infile:
                    content = infile.read()
                    line_count = len(content.splitlines())
                    file_size = os.path.getsize(file_path)
                    mod_time = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M")
                    
                    file_count += 1
                    total_lines += line_count
                    total_size += file_size
                    total_chars += len(content)
                    
                    full_content.append(f"{display_path} ({line_count}L, {format_file_size(file_size)}, Mod: {mod_time})")
                    full_content.append(content)
                    full_content.append("###")
                    file_stats[relative_path] = {'lines': line_count, 'size': file_size, 'modified': mod_time}
            except (PermissionError, UnicodeDecodeError, OSError) as e:
                errors.append(f"{file_path}: Failed to process ({str(e)})")
                if isinstance(e, UnicodeDecodeError):
                    binary_count += 1
        
        total_tokens = total_chars // 4
        summary = f"Files: {file_count}, Lines: {total_lines}, Size: {format_file_size(total_size)}"
        if binary_count > 0:
            summary += f" (Skipped {binary_count} binary files)"
        full_content.append(summary)
        
        if errors:
            full_content.append("\nErrors:")
            full_content.extend(f"- {error}" for error in errors)
        full_content.append("END")
        
        content_str = "\n".join(full_content)
        output_files = []
        
        if config.get("include_summary", True) and file_count > 0:
            project_summary = generate_project_summary(file_stats, target_dir, total_size, 
                                                      total_tokens, binary_count)
            summary_pos = content_str.find("\n###\n") + 5
            content_str = content_str[:summary_pos] + project_summary + "\n\n###\n" + content_str[summary_pos:]
        
        chunk_size = config.get("chunk_size")
        if chunk_size and chunk_size > 0:
            chunks = chunk_output(content_str, max_tokens=chunk_size)
            for i, chunk in enumerate(chunks):
                chunk_file = f"{os.path.splitext(output_file)[0]}_part{i+1}.txt" if len(chunks) > 1 else output_file
                with open(chunk_file, 'w', encoding='utf-8') as outfile:
                    outfile.write(chunk)
                output_files.append(chunk_file)
        else:
            with open(output_file, 'w', encoding='utf-8') as outfile:
                outfile.write(content_str)
            output_files.append(output_file)
        
        return True, file_count, total_lines, total_size, total_tokens, binary_count, errors, output_files
    
    except (PermissionError, OSError) as e:
        errors.append(f"Failed to write '{output_file}': {str(e)}")
        print(f"Error: {str(e)}")
        return False, file_count, total_lines, total_size, total_chars // 4, binary_count, errors, []

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build a code prompt from project files.")
    parser.add_argument("-t", "--target-dir", default=".", 
                        help="Directory to scan for code files (default: current directory)")
    parser.add_argument("-o", "--output-dir", default=".", 
                        help="Directory to save the output file (default: current directory)")
    parser.add_argument("-e", "--exclude-file", action="append", dest="exclude_files", default=[], 
                        help="Additional file to exclude (can be used multiple times)")
    parser.add_argument("-d", "--exclude-dir", action="append", dest="exclude_dirs", default=[], 
                        help="Additional directory to exclude (can be used multiple times)")
    parser.add_argument("-f", "--focus-dir", action="append", dest="focus_dirs", default=[], 
                        help="Only process files in these directories (can be used multiple times)")
    parser.add_argument("--no-default-excludes", action="store_true", 
                        help="Ignore default excludes and use only command-line excludes")
    parser.add_argument("--extensions", nargs="+", default=None, 
                        help="File extensions to include (overrides config file)")
    parser.add_argument("-c", "--chunk-size", type=int, default=None, 
                        help="Maximum token size for each output chunk")
    parser.add_argument("--no-summary", action="store_true", 
                        help="Disable project summary generation")
    parser.add_argument("-s", "--single-file", 
                        help="Process only this single file")
    
    args = parser.parse_args()
    config = load_config()
    merged_config = merge_config_with_args(config, args)
    
    print("Building code prompt...")
    success, file_count, total_lines, total_size, total_tokens, binary_count, errors, output_files = build_code_prompt(
        target_dir=args.target_dir, output_dir=args.output_dir, config=merged_config, single_file=args.single_file)
    
    if success:
        formatted_size = format_file_size(total_size)
        binary_msg = f" (Skipped {binary_count} binary files)" if binary_count > 0 else ""
        msg = (f"Done! Processed {file_count} files with {total_lines} lines, "
               f"{total_tokens:,} tokens ({formatted_size}) from '{os.path.abspath(args.target_dir)}'{binary_msg}.")
        if errors:
            msg = f"Completed with warnings! {msg} See {len(errors)} errors in output."
        print(msg)
        if len(output_files) > 1:
            print(f"Output split into {len(output_files)} files:")
        for file in output_files:
            print(f"- {os.path.abspath(file)}")
    else:
        print(f"Failed with {len(errors)} errors. Check output or logs.")