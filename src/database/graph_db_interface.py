"""
Abstract base interface for graph database implementations
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union


class GraphDatabaseInterface(ABC):
    """Abstract interface for graph database implementations"""
    
    @abstractmethod
    def initialize(self):
        """Initialize the database schema"""
        pass
    
    @abstractmethod
    def add_class(self, class_name: str, file_path: str, visibility: str = "Private") -> Union[int, str]:
        """Add a class node to the graph"""
        pass
    
    @abstractmethod
    def add_method(self, method_name: str, visibility: str, parent_class_id: Union[int, str]) -> Union[int, str]:
        """Add a method node to the graph under a class"""
        pass
    
    @abstractmethod
    def add_method_call(self, method_id: Union[int, str], called_method_name: str):
        """Add a method call relationship"""
        pass
    
    @abstractmethod
    def create_method_call_relationship(self, calling_class: str, calling_method: str, 
                                      target_class: str, target_method: str, call_type: str = "METHOD_CALL"):
        """Create a relationship between methods in different classes"""
        pass
    
    @abstractmethod
    def get_call_stack(self, class_name: str) -> Dict[str, Any]:
        """Get the complete call stack for a specific class"""
        pass
    
    @abstractmethod
    def get_method_call_stack(self, class_name: str, method_name: str) -> Dict[str, Any]:
        """Get the call stack for a specific method in a class"""
        pass
    
    @abstractmethod
    def store_parsing_results(self, parsing_results: Dict[str, Dict[str, Any]]):
        """Store the parsing results in the graph database"""
        pass
    
    @abstractmethod
    def print_graph(self):
        """Print the graph in the specified format"""
        pass
    
    @abstractmethod
    def close(self):
        """Clean up database connections"""
        pass
