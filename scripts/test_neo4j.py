"""
Test script for Neo4j implementation
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.graph_db_factory import CallStackGraphDB
from src.core.config import Config

def test_neo4j_implementation():
    """Test the Neo4j graph database implementation"""
    
    print("=== NEO4J IMPLEMENTATION TEST ===\n")
    
    try:
        # Create Neo4j database instance using config
        db_config = Config.get_database_config()
        print(f"Database type: {Config.DATABASE_TYPE}")
        print(f"Database config: {db_config}")
        
        graph_db = CallStackGraphDB(db_type=Config.DATABASE_TYPE, **db_config)
        print(f"Created database instance: {type(graph_db.db).__name__}\n")
        
        # Test data - sample parsing results
        test_data = {
            "csharp": {
                "Controllers/UserController.cs": {
                    "classes": [
                        {
                            "name": "UserController",
                            "visibility": "public",
                            "methods": [
                                {
                                    "name": "GetUser",
                                    "visibility": "public",
                                    "method_calls": ["ValidateUser", "FetchFromDatabase"]
                                },
                                {
                                    "name": "CreateUser",
                                    "visibility": "public",
                                    "method_calls": ["ValidateInput", "SaveToDatabase"]
                                },
                                {
                                    "name": "ValidateUser",
                                    "visibility": "private",
                                    "method_calls": []
                                }
                            ]
                        }
                    ]
                },
                "Models/User.cs": {
                    "classes": [
                        {
                            "name": "User",
                            "visibility": "public",
                            "methods": [
                                {
                                    "name": "GetFullName",
                                    "visibility": "public",
                                    "method_calls": []
                                },
                                {
                                    "name": "UpdateProfile",
                                    "visibility": "public",
                                    "method_calls": ["ValidateData"]
                                }
                            ]
                        }
                    ]
                }
            }
        }
        
        # Store test data
        print("Storing test data...")
        graph_db.store_parsing_results(test_data)
        print("Data stored successfully!\n")
        
        # Print the graph
        print("Generated Graph Structure:")
        print("=" * 60)
        graph_db.print_graph()
        
        # Cleanup
        graph_db.close()
        print("✅ Neo4j test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error testing Neo4j implementation: {e}")
        print("Make sure Neo4j is running and credentials in .env are correct")

if __name__ == "__main__":
    test_neo4j_implementation()
