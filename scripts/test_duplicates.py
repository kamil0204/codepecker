"""
Test script to simulate app.py duplicate data scenario
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.graph_db_factory import CallStackGraphDB
from src.core.config import Config

def test_duplicate_handling():
    """Test handling of duplicate data like app.py might generate"""
    
    print("=== DUPLICATE DATA HANDLING TEST ===\n")
    
    # Create test data that simulates what app.py might send multiple times
    duplicate_data = {
        "csharp": {
            "Controllers/ProjectController.cs": {
                "classes": [
                    {
                        "name": "ProjectController",
                        "visibility": "public",
                        "methods": [
                            {
                                "name": "GetProjectsAsync",
                                "visibility": "public",
                                "method_calls": ["ValidateUser", "FetchFromDatabase"]
                            },
                            {
                                "name": "CreateProjectAsync", 
                                "visibility": "public",
                                "method_calls": ["ValidateInput", "SaveToDatabase"]
                            }
                        ]
                    }
                ]
            }
        }
    }
    
    try:
        # Create database instance (with clear_db=True initially)
        db_config = Config.get_database_config()
        graph_db = CallStackGraphDB(db_type=Config.DATABASE_TYPE, clear_db=True, **db_config)
        print("✅ Created database instance")
        
        # Store data first time
        print("Storing data first time...")
        graph_db.store_parsing_results(duplicate_data)
        print("✅ First storage successful")
        
        # Close and recreate with clear_db=False to simulate app.py behavior
        graph_db.close()
        graph_db = CallStackGraphDB(db_type=Config.DATABASE_TYPE, clear_db=False, **db_config)
        
        # Store same data again (this should handle duplicates gracefully)
        print("Storing same data again...")
        graph_db.store_parsing_results(duplicate_data)
        print("✅ Duplicate storage handled successfully")
        
        # Print result
        print("\nFinal Graph Structure:")
        print("=" * 40)
        graph_db.print_graph()
        
        graph_db.close()
        print("✅ Duplicate handling test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in duplicate handling test: {e}")

if __name__ == "__main__":
    test_duplicate_handling()
