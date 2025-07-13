"""
Neo4j implementation of the graph database interface
"""
import os
from typing import Dict, Any
from neo4j import GraphDatabase
from .graph_db_interface import GraphDatabaseInterface


class Neo4jGraphDB(GraphDatabaseInterface):
    """Neo4j implementation for storing static call stack graph"""
    
    def __init__(self, uri: str = "bolt://localhost:7687", username: str = "neo4j", password: str = "password", clear_db: bool = True):
        """
        Initialize Neo4j connection
        
        Args:
            uri: Neo4j database URI
            username: Database username
            password: Database password
            clear_db: Whether to clear existing data on initialization (default: True)
        """
        self.uri = uri
        self.username = username
        self.password = password
        self.clear_db = clear_db
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.initialize()
    
    def initialize(self):
        """Initialize the Neo4j database schema"""
        with self.driver.session() as session:
            # Clear existing data only if requested
            if self.clear_db:
                session.run("MATCH (n) DETACH DELETE n")
            
            # Create constraints for better performance and data integrity
            try:
                # Create unique constraint on class name and file_path combination
                session.run("CREATE CONSTRAINT class_unique IF NOT EXISTS FOR (c:Class) REQUIRE (c.name, c.file_path) IS UNIQUE")
            except:
                pass  # Constraint might already exist
            
            try:
                # Create unique constraint on method name and parent class combination
                session.run("CREATE CONSTRAINT method_unique IF NOT EXISTS FOR (m:Method) REQUIRE (m.name, m.parent_class_name) IS UNIQUE")
            except:
                pass  # Constraint might already exist
    
    def add_class(self, class_name: str, file_path: str, visibility: str = "Private") -> str:
        """Add a class node to the graph"""
        query = """
        MERGE (c:Class {name: $name, file_path: $file_path})
        ON CREATE SET 
            c.visibility = $visibility,
            c.type = 'Class'
        ON MATCH SET
            c.visibility = $visibility,
            c.file_path = $file_path,
            c.type = 'Class'
        RETURN elementId(c) as class_id
        """
        
        # Normalize the file path to use OS-appropriate separators
        normalized_path = os.path.normpath(file_path) if file_path else None
        
        with self.driver.session() as session:
            result = session.run(query, name=class_name, file_path=normalized_path, visibility=visibility)
            return result.single()["class_id"]
    
    def add_method(self, method_name: str, visibility: str, parent_class_id: str) -> str:
        """Add a method node to the graph under a class"""
        query = """
        MATCH (c:Class) WHERE elementId(c) = $parent_class_id
        MERGE (m:Method {name: $name, parent_class_name: c.name})
        ON CREATE SET 
            m.visibility = $visibility,
            m.type = 'Method'
        ON MATCH SET
            m.visibility = $visibility,
            m.type = 'Method'
        MERGE (c)-[:HAS_METHOD]->(m)
        RETURN elementId(m) as method_id
        """
        
        with self.driver.session() as session:
            result = session.run(query, name=method_name, visibility=visibility, parent_class_id=parent_class_id)
            return result.single()["method_id"]
    
    def add_method_call(self, method_id: str, called_method_name: str):
        """Add a method call relationship"""
        query = """
        MATCH (m:Method) WHERE elementId(m) = $method_id
        MERGE (m)-[:CALLS {method_name: $called_method_name}]->(m)
        """
        
        with self.driver.session() as session:
            session.run(query, method_id=method_id, called_method_name=called_method_name)
    
    def store_parsing_results(self, parsing_results: Dict[str, Dict[str, Any]]):
        """Store the parsing results in the graph database"""
        for language, language_results in parsing_results.items():
            for file_path, file_result in language_results.items():
                if 'error' in file_result:
                    continue
                
                if 'classes' in file_result:
                    for class_info in file_result['classes']:
                        # Add class to database
                        class_visibility = class_info.get('visibility', 'private').title()
                        class_id = self.add_class(
                            class_name=class_info['name'],
                            file_path=file_path,
                            visibility=class_visibility
                        )
                        
                        # Add methods under the class
                        for method_info in class_info['methods']:
                            method_id = self.add_method(
                                method_name=method_info['name'],
                                visibility=method_info.get('visibility', 'private').title(),
                                parent_class_id=class_id
                            )
                            
                            # Add method calls if they exist
                            if 'method_calls' in method_info:
                                for called_method in method_info['method_calls']:
                                    self.add_method_call(method_id, called_method)
    
    def print_graph(self):
        """Print the graph in the specified format"""
        # First get all classes
        class_query = """
        MATCH (c:Class)
        RETURN c.name as class_name, 
               c.file_path as file_path, 
               c.visibility as class_visibility
        ORDER BY c.name
        """
        
        with self.driver.session() as session:
            class_results = session.run(class_query)
            
            for class_record in class_results:
                class_name = class_record["class_name"]
                file_path = class_record["file_path"]
                class_visibility = class_record["class_visibility"]
                
                # Print class with properties
                print(f"{class_name} (Properties - Type:Class,FilePath:{file_path},Visibility:{class_visibility})")
                
                # Get methods for this class
                method_query = """
                MATCH (c:Class {name: $class_name})-[:HAS_METHOD]->(m:Method)
                RETURN m.name as method_name, 
                       m.visibility as method_visibility
                ORDER BY m.name
                """
                
                method_results = session.run(method_query, class_name=class_name)
                
                for method_record in method_results:
                    method_name = method_record["method_name"]
                    method_visibility = method_record["method_visibility"]
                    
                    # Get method calls for this method
                    calls_query = """
                    MATCH (m:Method {name: $method_name, parent_class_name: $class_name})-[call:CALLS]->()
                    RETURN call.method_name as called_method
                    ORDER BY call.method_name
                    """
                    
                    calls_results = session.run(calls_query, method_name=method_name, class_name=class_name)
                    method_calls = [record["called_method"] for record in calls_results if record["called_method"]]
                    
                    # Format method calls as part of properties, limit length for readability
                    if method_calls:
                        calls_str = ','.join(method_calls)
                        # Truncate if too long to avoid display issues
                        if len(calls_str) > 50:
                            calls_str = calls_str[:47] + "..."
                        calls_property = f",Calls:[{calls_str}]"
                    else:
                        calls_property = ",Calls:[]"
                    
                    print(f"                   |____> {method_name}  (Properties - Type:Method,Visibility:{method_visibility}{calls_property})")
                
                print()  # Empty line between classes
    
    def close(self):
        """Clean up database connection"""
        if self.driver:
            self.driver.close()
