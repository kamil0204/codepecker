"""
Debug script to test C# parser with actual file content
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.parsers.csharp_parser import CSharpParser

def debug_parse_file():
    parser = CSharpParser()
    
    # Test with a simple C# file from the project
    test_file = "C:\\repos\\applications.web.intel-foundry.ifs3.api-project\\IFS.Project.API\\Controllers\\CompanyController.cs"
    
    try:
        result = parser.parse_file(test_file)
        print("Parse result:")
        print(result)
        
        # Also let's see the raw tree structure
        with open(test_file, 'r', encoding='utf-8-sig') as f:  # Use utf-8-sig to handle BOM
            content = f.read()
        
        tree = parser.parser.parse(content.encode('utf-8'))
        root_node = tree.root_node
        
        print("\nTree structure (first 20 nodes):")
        parser._debug_print_tree(root_node, content, depth=0, max_depth=3)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_parse_file()
