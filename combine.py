import os

# Set your base project directory
base_directory = r'C:\Users\guhan\chess-platform'  # Change this to your project root

# Set output file
output_file_path = 'Combined_chess-platform.txt'

# File types you want to include (extend as needed)
include_extensions = [
    '.py', '.html', '.css', '.js', '.ts', '.json',
    '.env', '.txt', '.md', '.yml', '.yaml'
]

# Optional folders to exclude (e.g., static/media/migrations/venv)
exclude_dirs = {'__pycache__', 'static', 'media', 'migrations', 'venv', '.venv', '.git', 'node_modules'}

with open(output_file_path, 'w', encoding='utf-8') as output_file:
    for root, dirs, files in os.walk(base_directory):
        # Exclude unwanted folders
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for filename in files:
            filepath = os.path.join(root, filename)
            if any(filename.endswith(ext) for ext in include_extensions):
                relative_path = os.path.relpath(filepath, base_directory)
                # Format path to start from chess-platform
                clean_path = f"chess-platform/{relative_path.replace(os.sep, '/')}"
                output_file.write(f"\n===== {clean_path} =====\n")
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        output_file.write(f.read())
                except Exception as e:
                    output_file.write(f"[Error reading file: {e}]\n")
