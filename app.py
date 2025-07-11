"""
Codebase analyzer that generates directory trees and AI-powered review plans
"""
import os
from datetime import datetime
from directory_scanner import get_directory_tree, generate_text_tree
from llm_client import generate_codebase_review_plan


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
    
    # Generate AI review plan
    review_plan = generate_codebase_review_plan(text_tree, project_path)
    
    if review_plan:
        # Save the review plan
        with open("codebase_review_plan.md", 'w', encoding='utf-8') as f:
            f.write(f"# Codebase Review Plan\n\n")
            f.write(f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Project Path:** {project_path}\n")
            f.write(f"**Total Files/Folders:** {len(tree_items)}\n\n")
            f.write("---\n\n")
            f.write(review_plan)
        
        # Display the review plan
        print(review_plan)
    else:
        print("Review plan generation failed. Check your API credentials and network connection.")


if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
