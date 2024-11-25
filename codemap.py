#!/usr/bin/env python3
"""
Generate comprehensive documentation of a codebase.

This script creates a Markdown document containing both the contents of code files
and a visual tree representation of the directory structure. It's designed to help
developers quickly understand project layouts and review code without jumping
between files.

Features:
- Automatically detects and reads common code and text files
- Excludes specified directories by default (node_modules, .git, etc.)
- Generates a tree view of the directory structure
- Creates a single Markdown file with all contents
- Handles permission errors gracefully
- Sorts entries (directories first, then case-insensitive)
- Supports custom directory exclusion

Example usage:
    codemap                     # Document current directory
    codemap /path/to/project    # Document specific directory
    codemap -e logs temp        # Exclude additional directories

Example output (Codebase.md):
    # Codebase Documentation
    
    ## File Contents
    
    ### src/index.js
    ```javascript
    console.log('Hello World');
    ```
    
    ## Directory Structure
    my-project/
    ├── src
    │   └── index.js
    └── package.json
"""

import os
import argparse
import sys
from typing import List, Set, Tuple

# File extensions to include when reading content
TEXT_EXTENSIONS = {
    '.txt', '.md', '.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.css', 
    '.json', '.yaml', '.yml', '.toml', '.ini', '.conf', '.sh', '.bash',
    '.sql', '.cpp', '.c', '.h', '.hpp', '.java', '.rb', '.php', '.go',
    '.rs', '.dart', '.swift', '.kt', '.r', '.lua', '.pl', '.scala'
}

def get_directory_name(path: str) -> str:
    """Get the name of the directory from a path."""
    if path == '.' or path == './':
        return os.path.basename(os.path.abspath(path))
    return os.path.basename(path)

def is_text_file(filename: str) -> bool:
    """Check if a file is a text file based on its extension."""
    return any(filename.lower().endswith(ext) for ext in TEXT_EXTENSIONS)

def read_file_content(filepath: str) -> Tuple[bool, str]:
    """Read file content, return (success, content)."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return True, f.read()
    except (UnicodeDecodeError, PermissionError, IOError):
        return False, f"Error: Could not read file {filepath}"

def generate_codebase_doc(startpath: str, exclude_dirs: List[str]) -> str:
    """Generate documentation including file contents and directory structure."""
    file_contents = []
    tree = []
    root_name = get_directory_name(startpath)
    tree.append(f"{root_name}/")
    
    def process_directory(path: str, prefix: str = '') -> None:
        try:
            entries = os.listdir(path)
        except PermissionError:
            tree.append(f"{prefix}!── Access Denied")
            return
        except Exception as e:
            tree.append(f"{prefix}!── Error: {str(e)}")
            return
            
        entries = sorted(entries, key=lambda x: (
            not os.path.isdir(os.path.join(path, x)),
            x.lower()
        ))
        
        filtered_entries = [
            entry for entry in entries 
            if not any(excluded in os.path.join(path, entry) for excluded in exclude_dirs)
        ]
        
        for idx, entry in enumerate(filtered_entries, 1):
            entry_path = os.path.join(path, entry)
            relative_path = os.path.relpath(entry_path, startpath)
            is_last = idx == len(filtered_entries)
            
            if is_last:
                tree.append(f"{prefix}└── {entry}")
                new_prefix = prefix + "    "
            else:
                tree.append(f"{prefix}├── {entry}")
                new_prefix = prefix + "│   "
            
            if os.path.isdir(entry_path):
                process_directory(entry_path, new_prefix)
            elif is_text_file(entry):
                success, content = read_file_content(entry_path)
                if success:
                    file_contents.append(f"\n## {relative_path}\n\n```\n{content}\n```\n")
    
    process_directory(startpath)
    
    # Combine file contents and directory tree
    doc = "# Codebase Documentation\n\n"
    doc += "## File Contents\n\n"
    doc += "".join(file_contents)
    doc += "\n## Directory Structure\n\n```\n"
    doc += "\n".join(tree)
    doc += "\n```\n"
    
    return doc

def main():
    parser = argparse.ArgumentParser(
        description="Generate comprehensive codebase documentation including file contents and structure."
    )
    parser.add_argument(
        'path', 
        nargs='?', 
        default='.', 
        help='Path to the directory (default: current directory)'
    )
    parser.add_argument(
        '-e', 
        '--exclude', 
        nargs='+', 
        default=['node_modules', '.git', '__pycache__', 'venv', '.env'],
        help='Folders to exclude (default: node_modules .git __pycache__ venv .env)'
    )

    args = parser.parse_args()
    repo_path = os.path.abspath(args.path)
    
    if not os.path.exists(repo_path):
        print(f"Error: Path '{repo_path}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    if not os.path.isdir(repo_path):
        print(f"Error: Path '{repo_path}' is not a directory", file=sys.stderr)
        sys.exit(1)
    
    try:
        documentation = generate_codebase_doc(repo_path, args.exclude)
        output_file = "Codebase.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(documentation)
            
        print(f"Documentation has been saved to '{output_file}'")
            
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()