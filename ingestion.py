"""
Data Ingestion Tool - Codebase Analysis Pipeline

This script performs the complete data ingestion process:
1. Scans project directory structure
2. Uses LLM to identify entry points
3. Parses code files using tree-sitter
4. Stores parsed data in Neo4j graph database

Usage: python ingestion.py
Configure the target project path in the main() function.
"""
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from src.utils.directory_scanner import get_directory_tree, generate_text_tree
from src.llm.llm_client import generate_entrypoints_list
from src.parsers.parser_manager import ParserManager
from src.database.graph_db_factory import CallStackGraphDB
from src.core.config import Config


def parse_files_parallel(parser_manager, grouped_files, max_workers=4):
    """
    Parse files in parallel using ThreadPoolExecutor
    
    Args:
        parser_manager: ParserManager instance
        grouped_files: Dictionary of language -> list of file paths
        max_workers: Maximum number of threads to use
    
    Returns:
        Dictionary containing parsing results for all files
    """
    print(f"   • Using {max_workers} threads for parallel parsing")
    
    all_results = {}
    lock = threading.Lock()
    
    def parse_single_file(file_path, language):
        """Parse a single file and return results"""
        try:
            # Get the appropriate parser for the language
            if language in parser_manager.parsers:
                parser = parser_manager.parsers[language]
                result = parser.parse_file(file_path)
                return file_path, result
            else:
                print(f"   ⚠️  No parser available for language: {language}")
                return file_path, None
        except Exception as e:
            print(f"   ⚠️  Error parsing {file_path}: {e}")
            return file_path, None
    
    # Process each language group
    for language, file_paths in grouped_files.items():
        print(f"   • Processing {len(file_paths)} {language} files...")
        
        language_results = {}
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all files for parsing
            future_to_file = {
                executor.submit(parse_single_file, file_path, language): file_path 
                for file_path in file_paths
            }
            
            # Collect results as they complete
            completed = 0
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    parsed_file, result = future.result()
                    if result:
                        with lock:
                            language_results[parsed_file] = result
                    completed += 1
                    
                    # Progress indicator
                    if completed % 10 == 0 or completed == len(file_paths):
                        print(f"   • Completed {completed}/{len(file_paths)} {language} files")
                        
                except Exception as e:
                    print(f"   ⚠️  Failed to process {file_path}: {e}")
        
        all_results[language] = language_results
        print(f"   ✅ Completed {language}: {len(language_results)} files successfully parsed")
    
    return all_results


def establish_method_call_relationships(graph_db, entry_point_results, remaining_results):
    """
    Establish relationships between method calls and their actual target methods
    
    Args:
        graph_db: Graph database instance
        entry_point_results: Parsing results from entry point files
        remaining_results: Parsing results from remaining files
    """
    print("   • Building method index from all parsed classes...")
    
    # Combine all parsing results
    all_results = {}
    for lang_results in [entry_point_results, remaining_results]:
        for language, file_results in lang_results.items():
            if language not in all_results:
                all_results[language] = {}
            all_results[language].update(file_results)
    
    # Build a comprehensive method index: method_name -> [(class_name, file_path, method_info)]
    method_index = {}
    class_method_map = {}  # class_name -> {method_name: method_info}
    
    for language, file_results in all_results.items():
        for file_path, file_result in file_results.items():
            if 'error' in file_result or 'classes' not in file_result:
                continue
                
            for class_info in file_result['classes']:
                class_name = class_info['name']
                class_method_map[class_name] = {}
                
                for method_info in class_info.get('methods', []):
                    method_name = method_info['name']
                    
                    # Add to method index
                    if method_name not in method_index:
                        method_index[method_name] = []
                    method_index[method_name].append((class_name, file_path, method_info))
                    
                    # Add to class method map
                    class_method_map[class_name][method_name] = method_info
    
    print(f"   • Indexed {len(method_index)} unique method names across {len(class_method_map)} classes")
    
    # Process method calls and establish relationships
    relationships_created = 0
    
    for language, file_results in all_results.items():
        for file_path, file_result in file_results.items():
            if 'error' in file_result or 'classes' not in file_result:
                continue
                
            for class_info in file_result['classes']:
                calling_class = class_info['name']
                
                for method_info in class_info.get('methods', []):
                    calling_method = method_info['name']
                    method_calls = method_info.get('calls', [])
                    
                    for called_method_name in method_calls:
                        # Skip if calling itself (recursive calls are already handled)
                        if called_method_name == calling_method:
                            continue
                            
                        # Find potential target methods
                        target_methods = find_target_method(
                            called_method_name, 
                            calling_class, 
                            method_index, 
                            class_method_map
                        )
                        
                        # Create relationships for each target method found
                        for target_class, target_file, target_method_info in target_methods:
                            try:
                                graph_db.create_method_call_relationship(
                                    calling_class=calling_class,
                                    calling_method=calling_method,
                                    target_class=target_class,
                                    target_method=called_method_name,
                                    call_type="METHOD_CALL"
                                )
                                relationships_created += 1
                                
                                if relationships_created <= 10:  # Show first 10 for debugging
                                    print(f"   • Created: {calling_class}.{calling_method} -> {target_class}.{called_method_name}")
                                elif relationships_created == 11:
                                    print("   • (Additional relationships created...)")
                                    
                            except Exception as e:
                                print(f"   ⚠️  Error creating relationship {calling_class}.{calling_method} -> {target_class}.{called_method_name}: {e}")
    
    print(f"   • Total relationships created: {relationships_created}")


def find_target_method(called_method_name, calling_class, method_index, class_method_map):
    """
    Find potential target methods for a method call
    
    Args:
        called_method_name: Name of the called method
        calling_class: Name of the class making the call
        method_index: Dictionary of method_name -> [(class_name, file_path, method_info)]
        class_method_map: Dictionary of class_name -> {method_name: method_info}
    
    Returns:
        List of tuples: [(target_class, target_file, target_method_info)]
    """
    target_methods = []
    
    # Check if the method exists in the method index
    if called_method_name in method_index:
        potential_targets = method_index[called_method_name]
        
        # Filter out self-calls (same class)
        for class_name, file_path, method_info in potential_targets:
            if class_name != calling_class:  # Don't include calls within the same class
                target_methods.append((class_name, file_path, method_info))
    
    return target_methods


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
            
            # Additional step: Parse remaining files not identified as entry points
            print("\n🔄 Step 5: Processing remaining files with parallelized parsing...")
            
            # Get all C# files from the directory tree
            all_cs_files = []
            for item in tree_items:
                # tree_items contains tuples: (item_type, name, level, full_path)
                item_type, name, level, file_path = item
                if item_type == 'file' and file_path.endswith('.cs') and os.path.isfile(file_path):
                    all_cs_files.append(file_path)
            
            # Get entry point files for comparison
            entry_point_files = set(file_paths)  # These were already processed
            
            # Filter out entry point files to get remaining files
            remaining_files = [f for f in all_cs_files if f not in entry_point_files]
            
            print(f"   • Found {len(all_cs_files)} total C# files")
            print(f"   • Already processed {len(entry_point_files)} entry point files")
            print(f"   • Remaining {len(remaining_files)} files to process")
            
            if remaining_files:
                # Group remaining files by language (mostly C# in this case)
                remaining_grouped = parser_manager.group_files_by_language(remaining_files)
                print(f"   • Grouped remaining files by language: {list(remaining_grouped.keys())}")
                
                # Parse remaining files with parallelization
                print("   • Starting parallelized parsing of remaining files...")
                remaining_parsing_results = parse_files_parallel(parser_manager, remaining_grouped)
                print("✅ Parallelized parsing completed")
                
                # Store additional parsing results in the database
                print("   • Storing additional parsing results...")
                graph_db.store_parsing_results(remaining_parsing_results)
                print("   • Additional data ingestion completed")
            else:
                print("   • No additional files to process")

            # Additional step: Establish method call relationships
            print("\n🔗 Step 6: Establishing method call relationships...")
            establish_method_call_relationships(graph_db, parsing_results, remaining_parsing_results if remaining_files else {})
            print("✅ Method call relationships established")

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
