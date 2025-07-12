"""
Graph database module for storing static call stack
"""
import sqlite3
import os
from typing import List, Dict, Any


class CallStackGraphDB:
    """Database for storing static call stack graph"""
    
    def __init__(self, db_path: str = "call_stack_graph.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database schema"""
        # Remove existing database to start fresh
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create nodes table for classes and methods
        cursor.execute('''
            CREATE TABLE nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,  -- 'Class' or 'Method'
                file_path TEXT,
                visibility TEXT,
                parent_id INTEGER,
                FOREIGN KEY (parent_id) REFERENCES nodes (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_class(self, class_name: str, file_path: str, visibility: str = "Private") -> int:
        """Add a class node to the graph"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Normalize the file path to use OS-appropriate separators
        normalized_path = os.path.normpath(file_path) if file_path else None
        
        cursor.execute('''
            INSERT INTO nodes (name, type, file_path, visibility, parent_id)
            VALUES (?, ?, ?, ?, NULL)
        ''', (class_name, "Class", normalized_path, visibility))
        
        class_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return class_id
    
    def add_method(self, method_name: str, visibility: str, parent_class_id: int) -> int:
        """Add a method node to the graph under a class"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO nodes (name, type, file_path, visibility, parent_id)
            VALUES (?, ?, NULL, ?, ?)
        ''', (method_name, "Method", visibility, parent_class_id))
        
        method_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return method_id
    
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
                            self.add_method(
                                method_name=method_info['name'],
                                visibility=method_info.get('visibility', 'private').title(),
                                parent_class_id=class_id
                            )
    
    def print_graph(self):
        """Print the graph in the specified format"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all classes
        cursor.execute('''
            SELECT id, name, file_path, visibility
            FROM nodes
            WHERE type = 'Class'
            ORDER BY name
        ''')
        
        classes = cursor.fetchall()
        
        for class_id, class_name, file_path, visibility in classes:
            # Print class with properties
            print(f"{class_name} (Properties - Type:Class,FilePath:{file_path},Visibility:{visibility})")
            
            # Get methods for this class
            cursor.execute('''
                SELECT name, visibility
                FROM nodes
                WHERE type = 'Method' AND parent_id = ?
                ORDER BY name
            ''', (class_id,))
            
            methods = cursor.fetchall()
            
            for method_name, method_visibility in methods:
                print(f"                   |____> {method_name}  (Properties - Type:Method,Visibility:{method_visibility})")
            
            print()  # Empty line between classes
        
        conn.close()
    
    def close(self):
        """Clean up database connection"""
        # SQLite connections are closed automatically in this implementation
        pass
