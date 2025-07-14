#!/usr/bin/env python3
"""
Test script to verify ingestion components work
"""
import os
import sys

print("Starting test script...")

try:
    print("Testing imports...")
    from src.utils.directory_scanner import get_directory_tree, generate_text_tree
    print("✅ Directory scanner imported")
    
    from src.llm.llm_client import generate_entrypoints_list, review_csharp_methods
    print("✅ LLM client imported")
    
    from src.parsers.parser_manager import ParserManager
    print("✅ Parser manager imported")
    
    from src.database.graph_db_factory import CallStackGraphDB
    print("✅ Graph DB factory imported")
    
    from src.core.config import Config
    print("✅ Config imported")
    
    print("All imports successful!")
    
except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("Test completed successfully!")
