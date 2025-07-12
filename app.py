"""
Codebase analyzer that identifies entry points, parses code, and builds call stack graphs
"""
import os
import json
from src.utils.directory_scanner import get_directory_tree, generate_text_tree
from src.llm.llm_client import generate_entrypoints_list
from src.parsers.parser_manager import ParserManager
from src.database.graph_db_factory import CallStackGraphDB
from src.core.config import Config


def main():
    project_path = "C:\\repos\\applications.web.intel-foundry.ifs3.api-project"
    
    if not os.path.exists(project_path):
        print(f"Error: Path does not exist: {project_path}")
        return
    
    # Generate directory tree for LLM analysis (not saved to file)
    tree_items = get_directory_tree(project_path)
    root_name = os.path.basename(project_path) or "Root"
    text_tree = generate_text_tree(tree_items, root_name)
    
    # Generate AI entrypoints list
    print("🧠 Analyzing codebase structure with LLM...")
    entrypoints_json = generate_entrypoints_list(text_tree, project_path)
    
    if entrypoints_json:
        try:
            # Parse the JSON response
            entrypoints_list = json.loads(entrypoints_json)
            
            # Display summary
            print(f"✅ Found {len(entrypoints_list)} entry points:")
            for entry in entrypoints_list:
                print(f"  - {entry['entrypoint']} ({entry['type']}) in {entry['file']}")
            
            # Initialize parser manager
            print("\n🔍 Parsing code files...")
            parser_manager = ParserManager()
            
            # Extract file paths from entrypoints
            file_paths = parser_manager.extract_files_from_entrypoints(entrypoints_list, project_path)
            print(f"Extracted {len(file_paths)} unique files from entrypoints")
            
            # Group files by language
            grouped_files = parser_manager.group_files_by_language(file_paths)
            print(f"Grouped files by language: {list(grouped_files.keys())}")
            
            # Parse files using appropriate parsers
            parsing_results = parser_manager.parse_files_by_language(grouped_files)
            
            # Create and populate graph database
            print("\n📊 Building call stack graph...")
            print("="*60)
            print("STATIC CALL STACK GRAPH")
            print("="*60)
            
            # Initialize graph database using configuration
            db_config = Config.get_database_config()
            graph_db = CallStackGraphDB(db_type=Config.DATABASE_TYPE, **db_config)
            graph_db.store_parsing_results(parsing_results)
            graph_db.print_graph()
            graph_db.close()
            
            print(f"\n✅ Analysis complete! Graph stored in database.")
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON response: {e}")
            print(f"Raw response: {entrypoints_json}")
    else:
        print("❌ Entrypoints list generation failed. Check your API credentials and network connection.")


if __name__ == "__main__":
    main()
