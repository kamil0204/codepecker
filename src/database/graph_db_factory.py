"""
Factory for creating graph database instances
"""
from typing import Dict, Any
from .graph_db_interface import GraphDatabaseInterface
from .sqlite_graph_db import SQLiteGraphDB


class GraphDatabaseFactory:
    """Factory class for creating graph database instances"""
    
    @staticmethod
    def create_database(db_type: str = "sqlite", **kwargs) -> GraphDatabaseInterface:
        """
        Create a graph database instance based on the specified type
        
        Args:
            db_type: Type of database ("sqlite", "neo4j", "memgraph", etc.)
            **kwargs: Additional arguments specific to the database type
            
        Returns:
            GraphDatabaseInterface implementation
        """
        db_type = db_type.lower()
        
        if db_type == "sqlite":
            db_path = kwargs.get("db_path", "call_stack_graph.db")
            return SQLiteGraphDB(db_path=db_path)
        
        # Future implementations can be added here:
        # elif db_type == "neo4j":
        #     return Neo4jGraphDB(**kwargs)
        # elif db_type == "memgraph":
        #     return MemgraphGraphDB(**kwargs)
        # elif db_type == "arangodb":
        #     return ArangoDBGraphDB(**kwargs)
        
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    @staticmethod
    def get_supported_databases() -> list:
        """Get list of supported database types"""
        return ["sqlite"]  # Add more as they're implemented


# Backward compatibility wrapper
class CallStackGraphDB:
    """
    Backward compatibility wrapper for the original CallStackGraphDB class
    """
    
    def __init__(self, db_type: str = "sqlite", **kwargs):
        """
        Initialize with specified database type
        
        Args:
            db_type: Type of database to use ("sqlite", "neo4j", etc.)
            **kwargs: Database-specific configuration parameters
        """
        self.db = GraphDatabaseFactory.create_database(db_type, **kwargs)
    
    def init_database(self):
        """Initialize the database schema (for backward compatibility)"""
        self.db.initialize()
    
    def add_class(self, class_name: str, file_path: str, visibility: str = "Private") -> int:
        """Add a class node to the graph"""
        return self.db.add_class(class_name, file_path, visibility)
    
    def add_method(self, method_name: str, visibility: str, parent_class_id: int) -> int:
        """Add a method node to the graph under a class"""
        return self.db.add_method(method_name, visibility, parent_class_id)
    
    def store_parsing_results(self, parsing_results: Dict[str, Dict[str, Any]]):
        """Store the parsing results in the graph database"""
        self.db.store_parsing_results(parsing_results)
    
    def print_graph(self):
        """Print the graph in the specified format"""
        self.db.print_graph()
    
    def close(self):
        """Clean up database connections"""
        self.db.close()
