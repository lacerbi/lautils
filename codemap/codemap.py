#!/usr/bin/env python3
# AI Summary: Python script that generates a single markdown document mapping a codebase's 
# structure and content. Creates a comprehensive view of source files with syntax highlighting 
# and directory tree visualization. Supports configuration via _aiconfig.yml for customization
# of project info, exclusions, output file name, and LLM prompts.

"""
Codemap: Generate markdown documentation of a codebase for LLM context.

This tool creates a single markdown document that captures both the structure and content
of a codebase, making it ideal for providing context to Large Language Models (LLMs) for
coding assistance tasks.

Key Features:
- Creates a single markdown file containing:
  - File contents with appropriate syntax highlighting
  - Visual directory tree structure
  - Optional project information and LLM instructions
- Configurable via _aiconfig.yml for:
  - Project name and description
  - Exclusions (files and directories)
  - Output file name
  - Custom LLM prompts
- Supports both CLI arguments and YAML configuration

Usage:
    codemap                         # Map current directory with default output file
    codemap /path/to/project        # Map specific directory with default output file
    codemap -e logs temp README.md  # Exclude files or directories
    codemap -e *.log *.tmp -o docs.md  # Exclude using patterns and specify output file
    codemap -o custom_output.md     # Specify a different output file
    codemap -f src/utils.py src/helpers/  # Focus on specific files and directories

Configuration (_aiconfig.yml):
    project_name: "My Project"                # Custom project name
    project_info: "Project description..."    # Project documentation
    prompts: "Instructions for the LLM..."    # LLM-specific instructions
    exclude: [".git", "public", "codebase.md", "_aiconfig.yml"] # Files and dirs to exclude
    focus: ["src/utils.py"]                   # Files and dirs to focus
    output_file: "custom_codebase.md"         # Custom output file name

Output (codebase.md or specified output file):
    # Codebase Documentation `My Project`
    
    ## Project Information
    Project description...
    
    ## File Contents

    ### src/main.py
    ```python
    def main():
        print("Hello World")
    ```
    
    ## Directory Structure    
    my-project/
    └── src
        └── main.py
        └── utils.py *
        
    # Instructions
    
    Instructions for the LLM...
"""

import os
import argparse
import sys
from typing import List, Set, Tuple, Dict, Optional
import yaml

# Mapping of file extensions to their syntax highlighting identifiers
# Update the SYNTAX_HIGHLIGHTING dictionary to include additional text-like extensions
SYNTAX_HIGHLIGHTING = {
    # General-purpose languages
    '.py': 'python',
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.java': 'java',
    '.rb': 'ruby',
    '.php': 'php',
    '.c': 'c',
    '.cpp': 'cpp',
    '.hpp': 'cpp',
    '.h': 'c',
    '.cs': 'csharp',
    '.go': 'go',
    '.rs': 'rust',
    '.swift': 'swift',
    
    # Web technologies
    '.html': 'html',
    '.css': 'css',
    '.scss': 'scss',
    '.xml': 'xml',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    
    # Scripting/command-line
    '.sh': 'bash',
    '.bash': 'bash',
    '.zsh': 'bash',
    '.ps1': 'powershell',
    '.bat': 'text',
    '.cmd': 'text',
    
    # Data formats
    '.json': 'json',
    '.yaml': 'yaml',
    '.yml': 'yaml',
    '.toml': 'toml',
    '.ini': 'ini',
    '.properties': 'text',
    '.conf': 'text',
    '.config': 'text',
    '.env': 'text',
    
    # Query languages
    '.sql': 'sql',
    '.graphql': 'graphql',
    '.gql': 'graphql',
    
    # Documentation and text
    '.md': 'markdown',
    '.markdown': 'markdown',
    '.rst': 'text',
    '.txt': 'text',
    '.log': 'text',
    
    # Configuration files
    'Dockerfile': 'dockerfile',
    'dockerfile': 'dockerfile',
    'Makefile': 'makefile',
    'makefile': 'makefile',
    '.dockerignore': 'text',
    '.gitignore': 'text',
    '.editorconfig': 'text',
    
    # Other popular languages
    '.pl': 'perl',
    '.kt': 'kotlin',
    '.lua': 'lua',
    '.r': 'r',
    '.dart': 'dart',
    '.scala': 'scala',
    '.clj': 'clojure',
    '.ex': 'elixir',
    '.erl': 'erlang',
    '.hs': 'haskell',
    '.f90': 'fortran',
    '.m': 'matlab',
    '.ML': 'ocaml',
    '.vim': 'vim',
    '.gradle': 'gradle',
    
    # Generic fallback
    '.txt': 'text'
}

# File extensions to include when reading content
TEXT_EXTENSIONS = set(SYNTAX_HIGHLIGHTING.keys())

def find_config_file(start_path: str) -> Optional[str]:
    """
    Search for _aiconfig.yml file starting from the given path and moving up
    through parent directories until found or root is reached.
    
    Args:
        start_path: The directory path to start searching from
        
    Returns:
        Full path to the config file if found, None otherwise
    """
    current_path = os.path.abspath(start_path)
    config_filename = '_aiconfig.yml'
    
    while True:
        config_path = os.path.join(current_path, config_filename)
        if os.path.isfile(config_path):
            return config_path
            
        parent_path = os.path.dirname(current_path)
        if parent_path == current_path:  # Reached root directory
            return None
            
        current_path = parent_path

def load_config(config_path: str) -> Dict:
    """
    Load and parse the YAML configuration file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dictionary containing the configuration settings
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config if config else {}
    except Exception as e:
        print(f"Warning: Error reading config file {config_path}: {str(e)}", file=sys.stderr)
        return {}

def get_directory_name(path: str) -> str:
    """Get the name of the directory from a path."""
    if path == '.' or path == './':
        return os.path.basename(os.path.abspath(path))
    return os.path.basename(path)

def is_text_file(filename: str) -> bool:
    """Check if a file is a text file based on its extension."""
    ext = os.path.splitext(filename)[1].lower()
    return ext in TEXT_EXTENSIONS or filename in TEXT_EXTENSIONS

def get_syntax_highlighting(filename: str) -> str:
    """Get the appropriate syntax highlighting identifier for a file."""
    # Check for exact filename matches first (e.g., Dockerfile, Makefile)
    if filename in SYNTAX_HIGHLIGHTING:
        return SYNTAX_HIGHLIGHTING[filename]
    
    # Then check the file extension
    ext = os.path.splitext(filename)[1].lower()
    return SYNTAX_HIGHLIGHTING.get(ext, 'text')

def read_file_content(filepath: str, is_focused: bool) -> Tuple[bool, str]:
    """Read file content, return (success, content). Truncate if not focused."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if not is_focused and len(lines) > 10:
                content = ''.join(lines[:10]) + '\n... (content truncated)'
                return True, content
            else:
                return True, ''.join(lines)
    except (UnicodeDecodeError, PermissionError, IOError):
        return False, f"Error: Could not read file {filepath}"
        
def generate_codebase_doc(startpath: str, exclude: List[str], focus: List[str],
                         project_name: Optional[str] = None, project_info: Optional[str] = None,
                         prompts: Optional[str] = None) -> Tuple[str, List[str]]:
    """Generate documentation including file contents and directory structure."""
    file_contents = []
    tree = []
    root_name = get_directory_name(startpath)
    project_name = project_name or root_name
    tree.append(f"{root_name}/")
    
    # Normalize focus paths
    normalized_focus = set(os.path.normpath(os.path.join(startpath, f)) for f in focus)
    focus_found = False
    
    def is_focused_path(path: str) -> bool:
        """Determine if a path is focused or is within a focused directory."""
        normalized_path = os.path.normpath(path)
        for focus_path in normalized_focus:
            if normalized_path == focus_path or normalized_path.startswith(focus_path + os.sep):
                return True
        return False

    def process_directory(path: str, prefix: str = '') -> None:
        nonlocal focus_found
        
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
            if entry not in exclude
        ]        
        
        for idx, entry in enumerate(filtered_entries, 1):
            entry_path = os.path.join(path, entry)
            relative_path = os.path.relpath(entry_path, startpath)
            is_last = idx == len(filtered_entries)
            focused = is_focused_path(entry_path)
            marker = " *" if focused else ""
            if focused:
                focus_found = True
            
            if is_last:
                tree.append(f"{prefix}└── {entry}{marker}")
                new_prefix = prefix + "    "
            else:
                tree.append(f"{prefix}├── {entry}{marker}")
                new_prefix = prefix + "│   "
            
            if os.path.isdir(entry_path):
                process_directory(entry_path, new_prefix)
            elif is_text_file(entry):
                success, content = read_file_content(entry_path, focused)
                if success:
                    syntax = get_syntax_highlighting(entry)
                    lastline = '' if (content and content[-1] == '\n') else '\n'
                    file_contents.append(f"\n### {relative_path}{marker}\n\n```{syntax}\n{content}{lastline}```\n")

    process_directory(startpath)
    
    # Combine file contents and directory tree
    doc = f"# Codebase Documentation `{project_name}`\n\n"
    
    # Add project information if available
    if project_info:
        doc += f"## Project Information\n\n{project_info}\n\n"
    
    doc += "## File Contents\n"
    doc += "".join(file_contents)
    doc += "\n## Directory Structure\n\n```\n"
    doc += "\n".join(tree)
    doc += "\n```\n"

    if focus_found:
        doc += "\n**Note:** The `*` indicates a relevant file or folder for the current task.\n"
    
    # Add prompts if available
    if prompts:
        doc += f"\n# Instructions\n\n{prompts}\n"
    
    return doc, tree  # Return tree for printing

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
        default=[],
        help='Files and folders to exclude (in addition to those specified in _aiconfig.yml)'
    )
    parser.add_argument(
        '-o',
        '--output',
        type=str,
        default=None,
        help='Output file name (default: codebase.md)'
    )
    parser.add_argument(
        '-f',
        '--focus',
        nargs='+',
        default=[],
        help='Files and folders to focus on'
    )

    args = parser.parse_args()
    repo_path = os.path.abspath(args.path)
    
    if not os.path.exists(repo_path):
        print(f"Error: Path '{repo_path}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    if not os.path.isdir(repo_path):
        print(f"Error: Path '{repo_path}' is not a directory", file=sys.stderr)
        sys.exit(1)
    
    # Look for config file
    config_path = find_config_file(repo_path)
    config = {}
    
    if config_path:
        print(f"Found configuration file at: {config_path}")
        config = load_config(config_path)
        
        # Update exclusions from config if present
        if 'exclude' in config:
            args.exclude.extend(config['exclude'])
        
        # Update focus from config if present
        if 'focus' in config:
            args.focus.extend(config['focus'])
    
    # Determine the output file name
    output_file = args.output or config.get('output_file', 'codebase.md')
    
    # Determine the focus list
    focus_list = args.focus if args.focus else config.get('focus', [])
    
    try:
        documentation, tree = generate_codebase_doc(
            repo_path,
            args.exclude,
            focus=focus_list,
            project_name=config.get('project_name'),
            project_info=config.get('project_info'),
            prompts=config.get('prompts')
        )

        # Print the directory tree to the console
        for line in tree:
            print(line)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(documentation)
            
        print(f"Documentation has been saved to '{output_file}'")        
            
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()