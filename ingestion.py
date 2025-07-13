"""
Data Ingestion Tool - Codebase Analysis Pipeline

This script performs the complete data ingestion process:
1. Scans project directory structure
2. Uses LLM to identify entry points
3. Parses code files using tree-sitter
4. Stores parsed data in graph database (Neo4j/SQLite)

Usage: python ingestion.py
Configure the target project path in the main() function.
"""
import os
import json
from src.utils.directory_scanner import get_directory_tree, generate_text_tree
from src.llm.llm_client import generate_entrypoints_list
from src.parsers.parser_manager import ParserManager
from src.database.graph_db_factory import CallStackGraphDB
from src.core.config import Config


def main():
    """
    Main ingestion pipeline function
    
    Processes a codebase through the complete ingestion pipeline:
    1. Directory scanning and tree generation
    2. LLM-based entry point identification  
    3. Code parsing using tree-sitter
    4. Graph database storage and visualization
    """
    # Configure the target project path here
    project_path = "C:\\repos\\applications.web.intel-foundry.ifs3.api-project"
    
    print("="*60)
    print("CODEBASE INGESTION PIPELINE")
    print("="*60)
    print(f"📁 Target Project: {project_path}")
    print()
    
    if not os.path.exists(project_path):
        print(f"❌ Error: Path does not exist: {project_path}")
        return
    
    # Generate directory tree for LLM analysis (not saved to file)
    print("📋 Step 1: Scanning project directory structure...")
    tree_items = get_directory_tree(project_path)
    root_name = os.path.basename(project_path) or "Root"
    text_tree = generate_text_tree(tree_items, root_name)
    print(f"✅ Found {len(tree_items)} items in project structure")
    
    # Generate AI entrypoints list
    print("\n🧠 Step 2: Analyzing codebase structure with LLM...")
    entrypoints_json = generate_entrypoints_list(text_tree, project_path)
    
    if entrypoints_json:
        try:
            # Parse the JSON response
            entrypoints_list = json.loads(entrypoints_json)
            
            # Display summary
            print(f"✅ Identified {len(entrypoints_list)} entry points:")
            for entry in entrypoints_list:
                print(f"   • {entry['entrypoint']} ({entry['type']}) in {entry['file']}")
            
            # Initialize parser manager
            print("\n🔍 Step 3: Parsing code files...")
            parser_manager = ParserManager()
            
            # Extract file paths from entrypoints
            file_paths = parser_manager.extract_files_from_entrypoints(entrypoints_list, project_path)
            print(f"   • Extracted {len(file_paths)} unique files from entrypoints")
            
            # Group files by language
            grouped_files = parser_manager.group_files_by_language(file_paths)
            print(f"   • Grouped files by language: {list(grouped_files.keys())}")
            
            # Parse files using appropriate parsers
            parsing_results = parser_manager.parse_files_by_language(grouped_files)
            print("✅ Code parsing completed")
            
            # Create and populate graph database
            print("\n📊 Step 4: Storing data in graph database...")
            
            # Initialize graph database using configuration
            db_config = Config.get_database_config()
            graph_db = CallStackGraphDB(db_type=Config.DATABASE_TYPE, **db_config)
            print(f"   • Using {Config.DATABASE_TYPE.upper()} database")
            
            graph_db.store_parsing_results(parsing_results)
            print("   • Data ingestion completed")
            
            print(f"\n📈 Generated Code Structure Visualization:")
            print("="*60)
            graph_db.print_graph()
            graph_db.close()
            
            print("="*60)
            print("✅ INGESTION PIPELINE COMPLETED SUCCESSFULLY")
            print("="*60)
            print(f"📊 Data stored in {Config.DATABASE_TYPE.upper()} database")
            if Config.DATABASE_TYPE == "neo4j":
                print("🌐 View in Neo4j Browser: http://localhost:7474")
            print()
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON response: {e}")
            print(f"Raw response: {entrypoints_json}")
    else:
        print("❌ Entrypoints list generation failed. Check your API credentials and network connection.")


if __name__ == "__main__":
    main()
