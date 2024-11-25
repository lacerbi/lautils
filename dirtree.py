#!/usr/bin/env python3
"""
Generate a tree-like representation of a directory structure.

This script creates a visual tree representation of a directory structure,
similar to the Unix 'tree' command, but with built-in exclusion of common
development directories like 'node_modules' and '.git'.

Features:
- Excludes specified directories by default (node_modules, .git)
- Customizable directory exclusion
- Optional output to file
- Shows the root directory name
- Handles permission errors gracefully
- Sorts entries (directories first, then case-insensitive)

Example outputs:
my-project/
├── src
│   ├── components
│   │   ├── Button.js
│   │   └── Header.js
│   └── index.js
└── package.json
"""

import os
import argparse
import sys

def get_directory_name(path):
    """
    Get the name of the directory from a path.
    For current directory ('.'), gets the actual folder name.
    
    Args:
        path (str): Path to the directory
        
    Returns:
        str: Name of the directory
    """
    if path == '.' or path == './':
        # Get the absolute path, then get the name of the current directory
        return os.path.basename(os.path.abspath(path))
    else:
        # For other paths, just get the last part
        return os.path.basename(path)

def generate_tree(startpath, exclude_dirs=['node_modules', '.git']):
    """
    Generate a tree representation of the directory structure.
    
    Args:
        startpath (str): Root directory to start from
        exclude_dirs (list): List of directory names to exclude
        
    Returns:
        str: Tree representation of the directory structure
    """
    tree = []
    root_name = get_directory_name(startpath)
    tree.append(f"{root_name}/")  # Add root directory name
    
    def add_tree_level(path, prefix=''):
        try:
            entries = os.listdir(path)
        except PermissionError:
            tree.append(f"{prefix}!── Access Denied")
            return
        except Exception as e:
            tree.append(f"{prefix}!── Error: {str(e)}")
            return
            
        # Sort directories first, then files, both case-insensitive
        entries = sorted(entries, key=lambda x: (
            not os.path.isdir(os.path.join(path, x)),
            x.lower()
        ))
        
        # Filter out excluded entries
        filtered_entries = [
            entry for entry in entries 
            if not any(excluded in os.path.join(path, entry) for excluded in exclude_dirs)
        ]
        
        for idx, entry in enumerate(filtered_entries, 1):
            entry_path = os.path.join(path, entry)
            is_last = idx == len(filtered_entries)
            
            if is_last:
                tree.append(f"{prefix}└── {entry}")
                new_prefix = prefix + "    "
            else:
                tree.append(f"{prefix}├── {entry}")
                new_prefix = prefix + "│   "
            
            if os.path.isdir(entry_path):
                add_tree_level(entry_path, new_prefix)
    
    add_tree_level(startpath)
    return '\n'.join(tree)

def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'path', 
        nargs='?', 
        default='.', 
        help='Path to the directory (default: current directory)'
    )
    parser.add_argument(
        '-o', 
        '--output', 
        help='Output file (default: print to console)'
    )
    parser.add_argument(
        '-e', 
        '--exclude', 
        nargs='+', 
        default=['node_modules', '.git'],
        help='Folders to exclude (default: node_modules .git)'
    )
    parser.add_argument(
        '-v', 
        '--version', 
        action='version', 
        version='%(prog)s 1.0'
    )

    args = parser.parse_args()

    # Convert path to absolute path
    repo_path = os.path.abspath(args.path)
    
    if not os.path.exists(repo_path):
        print(f"Error: Path '{repo_path}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    if not os.path.isdir(repo_path):
        print(f"Error: Path '{repo_path}' is not a directory", file=sys.stderr)
        sys.exit(1)
    
    try:
        tree_output = generate_tree(repo_path, args.exclude)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(tree_output)
            print(f"Tree structure has been saved to '{args.output}'")
        else:
            print(tree_output)
            
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()