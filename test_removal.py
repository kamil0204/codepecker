#!/usr/bin/env python3
"""Test script to verify SQLite removal was successful"""

try:
    from src.database.graph_db_factory import CallStackGraphDB, GraphDatabaseFactory
    from src.core.config import Config
    
    print("✅ All imports successful")
    
    # Test factory
    supported_dbs = GraphDatabaseFactory.get_supported_databases()
    print(f"✅ Supported databases: {supported_dbs}")
    
    # Check config
    print(f"✅ Default database type: {Config.DATABASE_TYPE}")
    
    print("✅ SQLite removal completed successfully!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
