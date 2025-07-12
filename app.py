"""
Codebase analyzer that generates directory trees and AI-powered review plans
"""
import os
import json
from datetime import datetime
from directory_scanner import get_directory_tree, generate_text_tree
from llm_client import generate_entrypoints_list


def main():
    project_path = "C:\\repos\\applications.web.intel-foundry.ifs3.api-project"
    
    if not os.path.exists(project_path):
        print(f"Error: Path does not exist: {project_path}")
        return
    
    # Generate directory tree
    tree_items = get_directory_tree(project_path)
    root_name = os.path.basename(project_path) or "Root"
    text_tree = generate_text_tree(tree_items, root_name)
    
    # Save directory tree
    with open("directory_tree.txt", 'w', encoding='utf-8') as f:
        f.write(text_tree)
    
    # Generate AI entrypoints list
    entrypoints_json = generate_entrypoints_list(text_tree, project_path)
    
    if entrypoints_json:
        try:
            # Parse the JSON response
            entrypoints_list = json.loads(entrypoints_json)
            
            # Display summary
            print(f"Found {len(entrypoints_list)} entry points:")
            for entry in entrypoints_list:
                print(f"  - {entry['entrypoint']} ({entry['type']}) in {entry['file']}")
            
            # The entrypoints_list variable now contains the parsed JSON data
            # that can be used for further processing
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response: {e}")
            print(f"Raw response: {entrypoints_json}")
    else:
        print("Entrypoints list generation failed. Check your API credentials and network connection.")


if __name__ == "__main__":
    main()
