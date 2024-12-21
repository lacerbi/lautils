# Codebase Documentation `AI codemap`

## Project Information

Prepare a codebase documentation to feed as context to an LLM coder

## File Contents

### codemap.bat

```text
@echo off
python %~dp0\codemap.py %*
```

### codemap.py

```python
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

Configuration (_aiconfig.yml):
    project_name: "My Project"                # Custom project name
    project_info: "Project description..."    # Project documentation
    prompts: "Instructions for the LLM..."    # LLM-specific instructions
    exclude: [".git", "public", "codebase.md", "_aiconfig.yml"] # Files and dirs to exclude
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

def read_file_content(filepath: str) -> Tuple[bool, str]:
    """Read file content, return (success, content)."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return True, f.read()
    except (UnicodeDecodeError, PermissionError, IOError):
        return False, f"Error: Could not read file {filepath}"
    
def generate_codebase_doc(startpath: str, exclude: List[str], 
                         project_name: Optional[str] = None, project_info: Optional[str] = None,
                         prompts: Optional[str] = None) -> str:
    """Generate documentation including file contents and directory structure."""
    file_contents = []
    tree = []
    root_name = get_directory_name(startpath)
    project_name = project_name or root_name
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
            if entry not in exclude
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
                    syntax = get_syntax_highlighting(entry)
                    lastline = '' if (content and content[-1] == '\n') else '\n'
                    file_contents.append(f"\n### {relative_path}\n\n```{syntax}\n{content}{lastline}```\n")

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
    
    # Add prompts if available
    if prompts:
        doc += f"\n# Instructions\n\n{prompts}\n"
    
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
    
    # Determine the output file name
    output_file = args.output or config.get('output_file', 'codebase.md')
    
    try:
        documentation = generate_codebase_doc(
            repo_path,
            args.exclude,
            project_name=config.get('project_name'),
            project_info=config.get('project_info'),
            prompts=config.get('prompts')
        )
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(documentation)
            
        print(f"Documentation has been saved to '{output_file}'")
            
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## Directory Structure

```
codemap/
├── codemap.bat
└── codemap.py
```

# Instructions

## Coding Instructions

When coding a new file, always add on top a brief description of the content of the file
and its purpose, as a commented section (as appropriate for the file type).
Title this section "AI Summary: <summary here>".

If the content of the file changes, change the summary to reflect the actual content.

## General Instructions

You are an expert software engineer.

You are tasked with following my instructions.

Use the included project instructions as a general guide.

If asked to write code, you will respond with 2 sections: A summary section and an XML section.

Here are some notes on how you should respond in the summary section:

- Provide a brief overall summary
- Provide a 1-sentence summary for each file changed and why.
- Provide a 1-sentence summary for each file deleted and why.
- Format this section as markdown.

Here are some notes on how you should respond in the XML section:

- Respond with the XML and nothing else
- Include all of the changed files
- Specify each file operation with CREATE, UPDATE, or DELETE
- If it is a CREATE or UPDATE include the full file code. Do not get lazy.
- Each file should include a brief change summary.
- Include the full file path
- I am going to copy/paste that entire XML section into a parser to automatically apply the changes you made, so put the XML block inside a markdown codeblock.
- Make sure to enclose the code with ![CDATA[__CODE HERE__]]

Here is how you should structure the XML:

<code_changes>
<changed_files>
<file>
<file_summary>**BRIEF CHANGE SUMMARY HERE**</file_summary>
<file_operation>**FILE OPERATION HERE**</file_operation>
<file_path>**FILE PATH HERE**</file_path>
<file_code><![CDATA[
__FULL FILE CODE HERE__
]]></file_code>
</file>
**REMAINING FILES HERE**
</changed_files>
</code_changes>

So the XML section will be:

```xml
__XML HERE__
```

## **Your Current Task:**

Add a new command -focus or -f which takes as input folders and/or files. 
All files selected are in focus, as well as all files in the selected folders and their subfolders.
Mark focused files and folders with (*) in the file tree (this includes all files in a focus folder and all subfolders).
If a focus file or folder (or more than one) is specified, for all of the non-focused files show only the first ten lines (if the file has more than ten lines) and then say that the rest of the file is not shown.
Add the focus option to the YAML config. Elements in -f are added to the ones in the config.