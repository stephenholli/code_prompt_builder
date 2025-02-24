import os
import json
from datetime import datetime

def load_or_create_settings(settings_file="collect_files_config.json"):
    defaults = {
        "extensions": [".html", ".css", ".js", ".py"],
        "exclude_files": ["collect_files.py"]
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

def collect_project_files():
    output_file = "project_files.txt"
    try:
        settings = load_or_create_settings()
    except Exception as e:
        print(f"Critical error in settings: {str(e)}. Exiting.")
        return
    
    extensions = tuple(settings["extensions"])
    exclude_files = set(settings["exclude_files"])
    errors = []
    file_count = 0
    
    try:
        with open(output_file, 'w', encoding='utf-8') as outfile:
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            outfile.write(f"Project Files ({current_date}) for dev & LLM\n###\n")
            
            for root, dirs, files in os.walk('.'):
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                try:
                    project_files = sorted([
                        f for f in files 
                        if f.lower().endswith(extensions) and 
                        not f.lower().endswith(tuple(f".min{e}" for e in extensions)) and 
                        f not in exclude_files
                    ])
                except TypeError as e:
                    errors.append(f"Error processing directory '{root}': Invalid extension type ({str(e)}).")
                    continue
                
                for filename in project_files:
                    file_path = os.path.join(root, filename)
                    file_count += 1
                    ext = filename.lower().split('.')[-1]
                    file_type = {'html': 'HTML', 'css': 'CSS', 'js': 'JS', 'py': 'PYTHON'}.get(ext, 'Unknown')
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as infile:
                            content = infile.read()
                            line_count = len(content.splitlines())
                            file_size = os.path.getsize(file_path)
                        
                        mod_time = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M")
                        outfile.write(f"[{file_type}] {file_path} ({line_count}L, {file_size}B, Mod: {mod_time})\n")
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
    print("Collecting project files...")
    collect_project_files()
    print("Done! Check 'project_files.txt' for the collected files if no errors occurred.")