"""
Factory for creating graph database instances
"""
from typing import Dict, Any, Union, List
from .graph_db_interface import GraphDatabaseInterface
from .neo4j_graph_db import Neo4jGraphDB


class GraphDatabaseFactory:
    """Factory class for creating graph database instances"""
    
    @staticmethod
    def create_database(db_type: str = "neo4j", **kwargs) -> GraphDatabaseInterface:
        """
        Create a graph database instance based on the specified type
        
        Args:
            db_type: Type of database ("neo4j", "memgraph", etc.)
            **kwargs: Additional arguments specific to the database type
            
        Returns:
            GraphDatabaseInterface implementation
        """
        db_type = db_type.lower()
        
        if db_type == "neo4j":
            uri = kwargs.get("uri", "bolt://localhost:7687")
            username = kwargs.get("username", "neo4j")
            password = kwargs.get("password", "password")
            clear_db = kwargs.get("clear_db", True)
            return Neo4jGraphDB(uri=uri, username=username, password=password, clear_db=clear_db)
        
        # Future implementations can be added here:
        # elif db_type == "memgraph":
        #     return MemgraphGraphDB(**kwargs)
        # elif db_type == "arangodb":
        #     return ArangoDBGraphDB(**kwargs)
        
        else:
            raise ValueError(f"Unsupported database type: {db_type}. Currently supported: neo4j")
    
    @staticmethod
    def get_supported_databases() -> list:
        """Get list of supported database types"""
        return ["neo4j"]  # Add more as they're implemented


# Backward compatibility wrapper
class CallStackGraphDB:
    """
    Backward compatibility wrapper for the original CallStackGraphDB class
    """
    
    def __init__(self, db_type: str = "neo4j", **kwargs):
        """
        Initialize with specified database type
        
        Args:
            db_type: Type of database to use ("neo4j", etc.)
            **kwargs: Database-specific configuration parameters
        """
        self.db = GraphDatabaseFactory.create_database(db_type, **kwargs)
    
    def init_database(self):
        """Initialize the database schema (for backward compatibility)"""
        self.db.initialize()
    
    def add_class(self, class_name: str, file_path: str, visibility: str = "Private") -> Union[int, str]:
        """Add a class node to the graph"""
        return self.db.add_class(class_name, file_path, visibility)
    
    def add_method(self, method_name: str, visibility: str, parent_class_id: Union[int, str], method_calls: List[str] = None, definition: str = None) -> Union[int, str]:
        """Add a method node to the graph under a class"""
        return self.db.add_method(method_name, visibility, parent_class_id, method_calls, definition)
    
    def add_method_call(self, method_id: Union[int, str], called_method_name: str):
        """Add a method call relationship"""
        return self.db.add_method_call(method_id, called_method_name)
    
    def create_method_call_relationship(self, calling_class: str, calling_method: str, 
                                      target_class: str, target_method: str, call_type: str = "METHOD_CALL"):
        """Create a relationship between methods in different classes"""
        return self.db.create_method_call_relationship(calling_class, calling_method, target_class, target_method, call_type)
    
    def get_call_stack(self, class_name: str) -> Dict[str, Any]:
        """Get the complete call stack for a specific class"""
        return self.db.get_call_stack(class_name)
    
    def get_method_call_stack(self, class_name: str, method_name: str) -> Dict[str, Any]:
        """Get the call stack for a specific method in a class"""
        return self.db.get_method_call_stack(class_name, method_name)
    
    def store_parsing_results(self, parsing_results: Dict[str, Dict[str, Any]]):
        """Store the parsing results in the graph database"""
        self.db.store_parsing_results(parsing_results)
    
    def print_graph(self):
        """Print the graph in the specified format"""
        self.db.print_graph()
    
    def close(self):
        """Clean up database connections"""
        self.db.close()

    def get_all_methods_for_review(self) -> List[Dict[str, Any]]:
        """Get all methods with their definitions for LLM review"""
        return self.db.get_all_methods_for_review()

    def add_review(self, method_id: str, review_data: Dict[str, Any]) -> str:
        """Add a review node linked to a method"""
        return self.db.add_review(method_id, review_data)

    def clear_existing_reviews(self):
        """Clear all existing review nodes"""
        return self.db.clear_existing_reviews()
