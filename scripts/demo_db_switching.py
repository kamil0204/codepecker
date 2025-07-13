"""
Demo script showing how to switch between different graph databases
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.graph_db_factory import GraphDatabaseFactory, CallStackGraphDB

def demo_database_switching():
    """Demonstrate switching between different database implementations"""
    
    print("=== GRAPH DATABASE SWITCHING DEMO ===\n")
    
    # Demo 1: Using factory directly
    print("1. Using GraphDatabaseFactory directly:")
    
    # Create Neo4j database (now default)
    neo4j_db = GraphDatabaseFactory.create_database("neo4j", 
        uri="bolt://localhost:7687", 
        username="neo4j", 
        password="your_password"
    )
    print(f"   Created Neo4j database: {type(neo4j_db).__name__}")
    
    # Create SQLite database
    sqlite_db = GraphDatabaseFactory.create_database("sqlite", db_path="demo_sqlite.db")
    print(f"   Created SQLite database: {type(sqlite_db).__name__}")
    
    # Show supported databases
    supported = GraphDatabaseFactory.get_supported_databases()
    print(f"   Supported databases: {supported}")
    
    # Demo 2: Using wrapper with configuration
    print("\n2. Using CallStackGraphDB wrapper:")
    
    # Neo4j (now default)
    db1 = CallStackGraphDB(db_type="neo4j", 
        uri="bolt://localhost:7687", 
        username="neo4j", 
        password="your_password"
    )
    print(f"   Created: {type(db1.db).__name__}")
    
    # SQLite (alternative)
    db2 = CallStackGraphDB(db_type="sqlite", db_path="demo1.db")
    print(f"   Created: {type(db2.db).__name__}")
    
    # Demo 3: Using environment variables
    print("\n3. Environment variable configuration:")
    print("   Set CODEPECKER_DB_TYPE=neo4j (current default)")
    print("   Set NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD in .env file")
    print("\n   Alternative examples:")
    print("   Set CODEPECKER_DB_TYPE=sqlite (to switch to SQLite)")
    print("   Set CODEPECKER_DB_TYPE=memgraph (to switch to Memgraph)")
    print("   Set CODEPECKER_DB_TYPE=arangodb (to switch to ArangoDB)")
    
    # Demo 4: Show how easy it is to add a new database
    print("\n4. Adding new database implementations:")
    print("   To add a new database:")
    print("   a) Implement GraphDatabaseInterface")
    print("   b) Add to GraphDatabaseFactory.create_database()")
    print("   c) Add configuration in Config class")
    print("   d) No changes needed in main application code!")
    
    # Cleanup
    neo4j_db.close()
    sqlite_db.close()
    db1.close()
    db2.close()
    
    # Remove demo files
    for file in ["demo_sqlite.db", "demo1.db"]:
        if os.path.exists(file):
            os.remove(file)
    
    print("\n=== Demo completed successfully! ===")

if __name__ == "__main__":
    demo_database_switching()
