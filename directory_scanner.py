"""
Directory scanning utilities with .gitignore support
"""
import os
import pathspec
from pathlib import Path


def load_gitignore_spec(gitignore_path):
    """Load .gitignore file and return pathspec object"""
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r', encoding='utf-8', errors='ignore') as f:
            return pathspec.PathSpec.from_lines('gitwildmatch', f)
    return None


def get_directory_tree(root_path):
    """Get directory tree respecting .gitignore files"""
    root_path = Path(root_path)
    gitignore_spec = None
    
    # Look for .gitignore in root directory
    gitignore_path = root_path / '.gitignore'
    if gitignore_path.exists():
        gitignore_spec = load_gitignore_spec(gitignore_path)
    
    tree_items = []
    
    def scan_directory(current_path, level=0):
        try:
            items = sorted(os.listdir(current_path))
            for item in items:
                item_path = os.path.join(current_path, item)
                
                # Always skip .git directories
                if item == '.git':
                    continue
                
                # Skip if ignored by .gitignore
                if gitignore_spec:
                    rel_path = os.path.relpath(item_path, root_path).replace('\\', '/')
                    
                    # For directories, also check with trailing slash
                    if os.path.isdir(item_path):
                        if gitignore_spec.match_file(rel_path) or gitignore_spec.match_file(rel_path + '/'):
                            continue
                    else:
                        if gitignore_spec.match_file(rel_path):
                            continue
                
                if os.path.isdir(item_path):
                    tree_items.append(('folder', item, level, item_path))
                    scan_directory(item_path, level + 1)
                else:
                    tree_items.append(('file', item, level, item_path))
        except (PermissionError, Exception):
            pass  # Silently skip inaccessible directories
    
    scan_directory(root_path)
    return tree_items


def generate_text_tree(tree_items, root_name):
    """Generate text-based directory tree"""
    tree_lines = [root_name]
    
    for item_type, name, level, full_path in tree_items:
        # Create indentation based on level
        indent = "│   " * level
        
        # Use different symbols for folders and files
        if item_type == 'folder':
            symbol = "📁"
        else:
            symbol = "📄"
        
        # Add tree structure characters
        if level > 0:
            tree_char = "├── "
            # Check if this is the last item at this level
            is_last = True
            current_index = tree_items.index((item_type, name, level, full_path))
            for next_item in tree_items[current_index + 1:]:
                if next_item[2] <= level:  # next_item[2] is level
                    if next_item[2] == level:
                        is_last = False
                    break
            
            if is_last:
                tree_char = "└── "
            
            line = indent[:-4] + tree_char + f"{symbol} {name}"
        else:
            line = f"{symbol} {name}"
        
        tree_lines.append(line)
    
    return '\n'.join(tree_lines)
