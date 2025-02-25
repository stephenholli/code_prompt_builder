import os
import json
from datetime import datetime
import argparse

def load_or_create_settings():
    # Define the settings file path relative to the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    settings_file = os.path.join(script_dir, "code_prompt_builder_config.json")
    
    defaults = {
        "extensions": [".html", ".css", ".js", ".py", ".md", ".json"],
        "exclude_files": [],
        "ignore_dirs": [".git", ".venv", "venv", "node_modules", "__pycache__", 
                       ".idea", ".vscode", "dist", "build", "env", ".pytest_cache"]
    }
    
    if not os.path.exists(settings_file):
        try:
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(defaults, f, indent=4)
            print(f"Created default '{settings_file}'.")
        except PermissionError:
            print(f"Error: No permission to create '{settings_file}'. Using defaults.")
            return defaults
        except OSError as e:
            print(f"Error: Failed to create '{settings_file}' ({str(e)}). Using defaults.")
            return defaults
    
    try:
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        if "extensions" not in settings or not isinstance(settings["extensions"], list):
            raise ValueError("'extensions' must be a list.")
        if "exclude_files" not in settings or not isinstance(settings["exclude_files"], list):
            raise ValueError("'exclude_files' must be a list.")
        if "ignore_dirs" not in settings or not isinstance(settings["ignore_dirs"], list):
            raise ValueError("'ignore_dirs' must be a list.")
        
        return settings
    except PermissionError:
        print(f"Error: No permission to read '{settings_file}'. Using defaults.")
        return defaults
    except json.JSONDecodeError:
        print(f"Error: '{settings_file}' is corrupted or invalid JSON. Using defaults.")
        return defaults
    except (OSError, ValueError) as e:
        print(f"Error: Failed to load '{settings_file}' ({str(e)}). Using defaults.")
        return defaults

def build_code_prompt(target_dir=".", output_dir=".", ignore_dirs=None, ignore_files=None):
    # Normalize paths and get folder name from target_dir
    target_dir = os.path.abspath(target_dir)
    folder_name = os.path.basename(target_dir)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    output_file = os.path.join(output_dir, f"{folder_name}-code-prompt-{timestamp}.txt")
    
    try:
        settings = load_or_create_settings()
    except Exception as e:
        print(f"Critical error in settings: {str(e)}. Exiting.")
        return
    
    # Initialize ignore lists with defaults from settings, then add command-line args
    ignore_dirs_set = set(settings["ignore_dirs"])
    if ignore_dirs:
        ignore_dirs_set.update(ignore_dirs)
    
    exclude_files_set = set(settings["exclude_files"])
    if ignore_files:
        exclude_files_set.update(ignore_files)
    
    errors = []
    file_count = 0
    
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as outfile:
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            outfile.write(f"{folder_name} Code Export ({current_date})\n###\n")
            
            # Process based on settings in target_dir
            extensions = tuple(settings["extensions"])
            
            for root, dirs, files in os.walk(target_dir):
                # Filter directories based on our ignore list
                dirs[:] = [d for d in dirs if d not in ignore_dirs_set]
                
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
                    file_count += 1
                    ext = filename.lower().split('.')[-1]
                    file_type = {'html': 'HTML', 'css': 'CSS', 'js': 'JS', 'py': 'PYTHON', 'md': 'MARKDOWN', 'json': 'JSON'}.get(ext, 'Unknown')
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as infile:
                            content = infile.read()
                            line_count = len(content.splitlines())
                            file_size = os.path.getsize(file_path)
                        
                        mod_time = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M")
                        outfile.write(f"[{file_type}] {display_path} ({line_count}L, {file_size}B, Mod: {mod_time})\n")
                        outfile.write(content)
                        outfile.write("\n###\n")
                    except PermissionError:
                        errors.append(f"{file_path}: No permission to read file.")
                    except UnicodeDecodeError:
                        errors.append(f"{file_path}: File is not UTF-8 encoded.")
                    except (OSError, ValueError) as e:
                        errors.append(f"{file_path}: Failed to process ({str(e)}).")
            
            outfile.write(f"Files: {file_count}")
            if errors:
                outfile.write("\nErrors:\n" + "\n".join([f"- {e}" for e in errors]))
            outfile.write("\nEND\n")
    except PermissionError:
        print(f"Error: No permission to write '{output_file}'. Aborting.")
        return
    except OSError as e:
        print(f"Error: Failed to write '{output_file}' ({str(e)}). Aborting.")
        return
    except Exception as e:
        print(f"Critical error during file collection: {str(e)}. Aborting.")
        return

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build a code prompt from project files.")
    parser.add_argument("--target-dir", default=".", help="Directory to scan for code files (default: current directory)")
    parser.add_argument("--output-dir", default=".", help="Directory to save the output file (default: script execution directory)")
    parser.add_argument("--ignore-dir", action="append", dest="ignore_dirs", default=[], 
                      help="Additional directory to ignore (can be used multiple times)")
    parser.add_argument("--ignore-file", action="append", dest="ignore_files", default=[], 
                      help="Additional file to ignore (can be used multiple times)")
    args = parser.parse_args()
    
    print("Building code prompt...")
    build_code_prompt(target_dir=args.target_dir, 
                     output_dir=args.output_dir, 
                     ignore_dirs=args.ignore_dirs,
                     ignore_files=args.ignore_files)
    
    folder_name = os.path.basename(os.path.abspath(args.target_dir))
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    output_file = os.path.join(args.output_dir, f"{folder_name}-code-prompt-{timestamp}.txt")
    print(f"Done! Scanned '{args.target_dir}', output written to '{output_file}' if no errors occurred.")