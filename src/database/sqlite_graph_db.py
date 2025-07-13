"""
SQLite implementation of the graph database interface
"""
import sqlite3
import os
from typing import List, Dict, Any
from .graph_db_interface import GraphDatabaseInterface


class SQLiteGraphDB(GraphDatabaseInterface):
    """SQLite implementation for storing static call stack graph"""
    
    def __init__(self, db_path: str = "call_stack_graph.db"):
        self.db_path = db_path
        self.initialize()
    
    def initialize(self):
        """Initialize the SQLite database schema"""
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
        
        # Create method_calls table to store method calls within methods
        cursor.execute('''
            CREATE TABLE method_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                method_id INTEGER NOT NULL,
                called_method_name TEXT NOT NULL,
                FOREIGN KEY (method_id) REFERENCES nodes (id)
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
    
    def add_method_call(self, method_id: int, called_method_name: str):
        """Add a method call relationship"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO method_calls (method_id, called_method_name)
            VALUES (?, ?)
        ''', (method_id, called_method_name))
        
        conn.commit()
        conn.close()
    
    def create_method_call_relationship(self, calling_class: str, calling_method: str, 
                                      target_class: str, target_method: str, call_type: str = "METHOD_CALL"):
        """Create a relationship between methods in different classes"""
        # For SQLite, we can add this information to a new table or extend existing tables
        # For now, we'll add it to the method_calls table with additional context
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Find the calling method ID
        cursor.execute('''
            SELECT m.id FROM methods m
            JOIN classes c ON m.class_id = c.id
            WHERE c.name = ? AND m.name = ?
        ''', (calling_class, calling_method))
        
        calling_result = cursor.fetchone()
        if calling_result:
            calling_method_id = calling_result[0]
            
            # Create an enhanced method call entry with target class information
            cursor.execute('''
                INSERT OR IGNORE INTO method_calls (method_id, called_method_name)
                VALUES (?, ?)
            ''', (calling_method_id, f"{target_class}.{target_method}"))
            
        conn.commit()
        conn.close()
    
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
                SELECT id, name, visibility
                FROM nodes
                WHERE type = 'Method' AND parent_id = ?
                ORDER BY name
            ''', (class_id,))
            
            methods = cursor.fetchall()
            
            for method_id, method_name, method_visibility in methods:
                # Get method calls for this method
                cursor.execute('''
                    SELECT called_method_name
                    FROM method_calls
                    WHERE method_id = ?
                    ORDER BY called_method_name
                ''', (method_id,))
                
                method_calls = cursor.fetchall()
                method_calls_list = [call[0] for call in method_calls]
                
                # Format method calls as part of properties, limit length for readability
                if method_calls_list:
                    calls_str = ','.join(method_calls_list)
                    # Truncate if too long to avoid display issues
                    if len(calls_str) > 50:
                        calls_str = calls_str[:47] + "..."
                    calls_property = f",Calls:[{calls_str}]"
                else:
                    calls_property = ",Calls:[]"
                
                print(f"                   |____> {method_name}  (Properties - Type:Method,Visibility:{method_visibility}{calls_property})")
            
            print()  # Empty line between classes
        
        conn.close()
    
    def get_call_stack(self, class_name: str) -> Dict[str, Any]:
        """Get the complete call stack for a specific class"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get class info and all its methods with their calls
        cursor.execute('''
            SELECT n1.name as class_name, n1.file_path as class_file,
                   n2.name as method_name, n2.visibility as method_visibility,
                   mc.called_method_name
            FROM nodes n1
            JOIN nodes n2 ON n2.parent_id = n1.id AND n2.type = 'Method'
            LEFT JOIN method_calls mc ON n2.id = mc.method_id
            WHERE n1.type = 'Class' AND n1.name = ?
            ORDER BY n2.name, mc.called_method_name
        ''', (class_name,))
        
        results = cursor.fetchall()
        conn.close()
        
        call_stack = {}
        
        for record in results:
            class_name = record[0]
            class_file = record[1]
            method_name = record[2]
            method_visibility = record[3]
            called_method_name = record[4]
            
            # Initialize class structure
            if class_name not in call_stack:
                call_stack[class_name] = {
                    "file_path": class_file,
                    "methods": {}
                }
            
            # Initialize method structure
            if method_name not in call_stack[class_name]["methods"]:
                call_stack[class_name]["methods"][method_name] = {
                    "visibility": method_visibility,
                    "calls": {}
                }
            
            # Add called method if it exists and looks like a cross-class call
            if called_method_name and '.' in called_method_name:
                parts = called_method_name.split('.', 1)
                if len(parts) == 2:
                    target_class, target_method = parts
                    call_stack[class_name]["methods"][method_name]["calls"][called_method_name] = {
                        "class": target_class,
                        "method": target_method
                    }
        
        return call_stack
        
    def get_method_call_stack(self, class_name: str, method_name: str) -> Dict[str, Any]:
        """Get the call stack for a specific method in a class"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # First, get methods that are called by the specified method
        cursor.execute('''
            SELECT mc.called_method_name
            FROM nodes n1
            JOIN nodes n2 ON n2.parent_id = n1.id AND n2.type = 'Method'
            JOIN method_calls mc ON n2.id = mc.method_id
            WHERE n1.type = 'Class' AND n1.name = ? AND n2.name = ?
        ''', (class_name, method_name))
        
        called_methods = cursor.fetchall()
        target_classes = []
        
        # Extract target class names from the called methods
        for record in called_methods:
            called_method_name = record[0]
            if called_method_name and '.' in called_method_name:
                parts = called_method_name.split('.', 1)
                if len(parts) == 2:
                    target_class = parts[0]
                    target_classes.append(target_class)
        
        call_stack = {}
        
        # For each target class, get all its methods and their calls
        for target_class in target_classes:
            cursor.execute('''
                SELECT n1.name as class_name, n1.file_path as class_file,
                       n2.name as method_name, n2.visibility as method_visibility,
                       mc.called_method_name
                FROM nodes n1
                JOIN nodes n2 ON n2.parent_id = n1.id AND n2.type = 'Method'
                LEFT JOIN method_calls mc ON n2.id = mc.method_id
                WHERE n1.type = 'Class' AND n1.name = ?
                ORDER BY n2.name, mc.called_method_name
            ''', (target_class,))
            
            results = cursor.fetchall()
            
            for record in results:
                class_name = record[0]
                class_file = record[1]
                method_name = record[2]
                method_visibility = record[3]
                called_method_name = record[4]
                
                # Initialize class structure
                if class_name not in call_stack:
                    call_stack[class_name] = {
                        "file_path": class_file,
                        "methods": {}
                    }
                
                # Initialize method structure
                if method_name not in call_stack[class_name]["methods"]:
                    call_stack[class_name]["methods"][method_name] = {
                        "visibility": method_visibility,
                        "calls": {}
                    }
                
                # Add called method if it exists and looks like a cross-class call
                if called_method_name and '.' in called_method_name:
                    parts = called_method_name.split('.', 1)
                    if len(parts) == 2:
                        inner_target_class, inner_target_method = parts
                        call_stack[class_name]["methods"][method_name]["calls"][called_method_name] = {
                            "class": inner_target_class,
                            "method": inner_target_method
                        }
        
        conn.close()
        return call_stack

    def close(self):
        """Clean up database connection"""
        # SQLite connections are closed automatically in this implementation
        pass
