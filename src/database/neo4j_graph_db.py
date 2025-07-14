"""
Neo4j implementation of the graph database interface
"""
import os
from typing import Dict, Any, List
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
    
    def add_method(self, method_name: str, visibility: str, parent_class_id: str, method_calls: List[str] = None, definition: str = None) -> str:
        """Add a method node to the graph under a class"""
        if method_calls is None:
            method_calls = []
            
        query = """
        MATCH (c:Class) WHERE elementId(c) = $parent_class_id
        MERGE (m:Method {name: $name, parent_class_name: c.name})
        ON CREATE SET 
            m.visibility = $visibility,
            m.type = 'Method',
            m.method_calls = $method_calls,
            m.definition = $definition
        ON MATCH SET
            m.visibility = $visibility,
            m.type = 'Method',
            m.method_calls = $method_calls,
            m.definition = $definition
        MERGE (c)-[:HAS_METHOD]->(m)
        RETURN elementId(m) as method_id
        """
        
        with self.driver.session() as session:
            result = session.run(query, name=method_name, visibility=visibility, parent_class_id=parent_class_id, method_calls=method_calls, definition=definition)
            return result.single()["method_id"]
    
    def add_method_call(self, method_id: str, called_method_name: str):
        """Add a method call relationship - try to find actual target method, fallback to property-based"""
        query = """
        MATCH (m:Method) WHERE elementId(m) = $method_id
        OPTIONAL MATCH (target:Method {name: $called_method_name})
        WHERE target <> m
        FOREACH (t IN CASE WHEN target IS NOT NULL THEN [target] ELSE [] END |
            MERGE (m)-[:METHOD_CALL {type: "SIMPLE_CALL"}]->(t)
        )
        FOREACH (_ IN CASE WHEN target IS NULL THEN [1] ELSE [] END |
            MERGE (m)-[:METHOD_CALL {method_name: $called_method_name, type: "UNRESOLVED_CALL"}]->(m)
        )
        """
        
        with self.driver.session() as session:
            session.run(query, method_id=method_id, called_method_name=called_method_name)
    
    def create_method_call_relationship(self, calling_class: str, calling_method: str, 
                                      target_class: str, target_method: str, call_type: str = "METHOD_CALL"):
        """Create a relationship between methods in different classes"""
        query = """
        MATCH (calling_class:Class {name: $calling_class})
        MATCH (target_class:Class {name: $target_class})
        MATCH (calling_class)-[:HAS_METHOD]->(calling_method:Method {name: $calling_method})
        MATCH (target_class)-[:HAS_METHOD]->(target_method:Method {name: $target_method})
        MERGE (calling_method)-[:METHOD_CALL {type: $call_type}]->(target_method)
        """
        
        with self.driver.session() as session:
            session.run(query, 
                       calling_class=calling_class, 
                       calling_method=calling_method,
                       target_class=target_class, 
                       target_method=target_method,
                       call_type=call_type)

    def get_call_stack(self, class_name: str) -> Dict[str, Any]:
        """Get the complete call stack for a specific class"""
        query = """
        MATCH (c:Class {name: $class_name})-[:HAS_METHOD]->(m:Method)
        OPTIONAL MATCH (m)-[:METHOD_CALL]->(target_method:Method)<-[:HAS_METHOD]-(target_class:Class)
        RETURN c.name as class_name, c.file_path as class_file,
               m.name as method_name, m.visibility as method_visibility,
               target_class.name as target_class_name, 
               target_method.name as target_method_name
        ORDER BY method_name, target_class_name, target_method_name
        """
        
        call_stack = {}
        
        with self.driver.session() as session:
            result = session.run(query, class_name=class_name)
            
            for record in result:
                class_name = record["class_name"]
                method_name = record["method_name"]
                method_visibility = record["method_visibility"]
                target_class_name = record["target_class_name"]
                target_method_name = record["target_method_name"]
                
                # Initialize class structure
                if class_name not in call_stack:
                    call_stack[class_name] = {
                        "file_path": record["class_file"],
                        "methods": {}
                    }
                
                # Initialize method structure
                if method_name not in call_stack[class_name]["methods"]:
                    call_stack[class_name]["methods"][method_name] = {
                        "visibility": method_visibility,
                        "calls": {}
                    }
                
                # Add target method if it exists
                if target_class_name and target_method_name:
                    target_key = f"{target_class_name}.{target_method_name}"
                    call_stack[class_name]["methods"][method_name]["calls"][target_key] = {
                        "class": target_class_name,
                        "method": target_method_name
                    }
        
        return call_stack

    def get_method_call_stack(self, class_name: str, method_name: str) -> Dict[str, Any]:
        """Get the call stack for a specific method in a class"""
        query = """
        MATCH (c:Class {name: $class_name})-[:HAS_METHOD]->(m:Method {name: $method_name})
        OPTIONAL MATCH (m)-[:METHOD_CALL]->(target_method:Method)<-[:HAS_METHOD]-(target_class:Class)
        WITH target_class, target_method
        WHERE target_class IS NOT NULL AND target_method IS NOT NULL
        MATCH (target_class)-[:HAS_METHOD]->(all_methods:Method)
        OPTIONAL MATCH (all_methods)-[:METHOD_CALL]->(nested_method:Method)<-[:HAS_METHOD]-(nested_class:Class)
        RETURN target_class.name as class_name, target_class.file_path as class_file,
               all_methods.name as method_name, all_methods.visibility as method_visibility,
               nested_class.name as target_class_name, 
               nested_method.name as target_method_name
        ORDER BY class_name, method_name, target_class_name, target_method_name
        """
        
        call_stack = {}
        
        with self.driver.session() as session:
            result = session.run(query, class_name=class_name, method_name=method_name)
            
            for record in result:
                class_name = record["class_name"]
                method_name = record["method_name"]
                method_visibility = record["method_visibility"]
                target_class_name = record["target_class_name"]
                target_method_name = record["target_method_name"]
                
                # Initialize class structure
                if class_name not in call_stack:
                    call_stack[class_name] = {
                        "file_path": record["class_file"],
                        "methods": {}
                    }
                
                # Initialize method structure
                if method_name not in call_stack[class_name]["methods"]:
                    call_stack[class_name]["methods"][method_name] = {
                        "visibility": method_visibility,
                        "calls": {}
                    }
                
                # Add target method if it exists
                if target_class_name and target_method_name:
                    target_key = f"{target_class_name}.{target_method_name}"
                    call_stack[class_name]["methods"][method_name]["calls"][target_key] = {
                        "class": target_class_name,
                        "method": target_method_name
                    }
        
        return call_stack

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
                            # Extract method calls list
                            method_calls_list = method_info.get('method_calls', [])
                            
                            method_id = self.add_method(
                                method_name=method_info['name'],
                                visibility=method_info.get('visibility', 'private').title(),
                                parent_class_id=class_id,
                                method_calls=method_calls_list,
                                definition=method_info.get('definition')
                            )
                            
                            # Add method calls as relationships if they exist
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
                    MATCH (m:Method {name: $method_name, parent_class_name: $class_name})
                    OPTIONAL MATCH (m)-[call:METHOD_CALL]->(target:Method)
                    OPTIONAL MATCH (target)<-[:HAS_METHOD]-(target_class:Class)
                    RETURN CASE 
                        WHEN target_class IS NOT NULL THEN target_class.name + '.' + target.name
                        ELSE call.method_name 
                    END as called_method
                    ORDER BY called_method
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
    
    def get_recursive_call_stack(self, class_name: str, max_depth: int = 10) -> Dict[str, Any]:
        """Get complete call stack with configurable depth (all outgoing calls from class methods)"""
        call_stack = {}
        
        with self.driver.session() as session:
            # First, get basic class and method information
            base_query = """
            MATCH (c:Class {name: $class_name})-[:HAS_METHOD]->(m:Method)
            RETURN c.name as class_name, c.file_path as file_path,
                   m.name as method_name, m.visibility as method_visibility
            ORDER BY method_name
            """
            
            base_result = session.run(base_query, class_name=class_name)
            
            for record in base_result:
                cls_name = record["class_name"]
                file_path = record["file_path"]
                method_name = record["method_name"]
                method_visibility = record["method_visibility"]
                
                # Initialize class structure
                if cls_name not in call_stack:
                    call_stack[cls_name] = {
                        "file_path": file_path,
                        "methods": {}
                    }
                
                # Initialize method structure
                if method_name not in call_stack[cls_name]["methods"]:
                    call_stack[cls_name]["methods"][method_name] = {
                        "visibility": method_visibility,
                        "recursive_calls": {},
                        "max_depth_reached": max_depth
                    }
            
            # If no methods found, return the empty structure
            if not call_stack:
                return {}
            
            # Now get the call chains for each method
            calls_query = """
            MATCH (c:Class {name: $class_name})-[:HAS_METHOD]->(m:Method {name: $method_name})
            MATCH path = (m)-[:METHOD_CALL*1..$max_depth]->(target:Method)
            WITH nodes(path) as call_chain
            UNWIND range(0, size(call_chain)-1) as i
            WITH call_chain[i] as method_at_depth, i as depth
            MATCH (method_at_depth)<-[:HAS_METHOD]-(method_class:Class)
            RETURN method_at_depth.name as called_method,
                   method_class.name as called_class,
                   depth
            ORDER BY depth, called_class, called_method
            """
            
            # Get calls for each method
            for cls_name in call_stack:
                for method_name in call_stack[cls_name]["methods"]:
                    calls_result = session.run(calls_query, 
                                             class_name=class_name, 
                                             method_name=method_name, 
                                             max_depth=max_depth)
                    
                    for call_record in calls_result:
                        depth = call_record["depth"]
                        called_class = call_record["called_class"]
                        called_method = call_record["called_method"]
                        
                        call_key = f"depth_{depth}_{called_class}.{called_method}"
                        
                        call_stack[cls_name]["methods"][method_name]["recursive_calls"][call_key] = {
                            "caller_class": class_name,
                            "caller_method": method_name,
                            "callee_class": called_class,
                            "callee_method": called_method,
                            "depth": depth
                        }
        
        return call_stack
        
        return call_stack

    def get_method_call_tree(self, class_name: str, method_name: str, max_depth: int = 5) -> Dict[str, Any]:
        """Get hierarchical call tree for a specific method with cycle detection"""
        query = """
        MATCH (c:Class {name: $class_name})-[:HAS_METHOD]->(root:Method {name: $method_name})
        CALL {
            WITH root
            MATCH path = (root)-[:METHOD_CALL*0..$max_depth]->(target:Method)
            WHERE ALL(node IN nodes(path) WHERE single(x IN nodes(path) WHERE x = node))
            WITH nodes(path) as call_path, length(path) as path_depth
            UNWIND range(0, size(call_path)-1) as i
            WITH call_path[i] as method_node, i as depth, path_depth
            MATCH (method_node)<-[:HAS_METHOD]-(method_class:Class)
            OPTIONAL MATCH (method_node)-[:METHOD_CALL]->(next_method:Method)<-[:HAS_METHOD]-(next_class:Class)
            WHERE (depth < path_depth)
            RETURN method_class.name as class_name, method_class.file_path as class_file,
                   method_node.name as method_name, method_node.visibility as method_visibility,
                   next_class.name as next_class, next_method.name as next_method,
                   depth
        }
        RETURN class_name, class_file, method_name, method_visibility,
               next_class, next_method, depth
        ORDER BY depth, class_name, method_name
        """
        
        call_tree = {
            "root": {"class": class_name, "method": method_name},
            "tree": {},
            "max_depth": max_depth
        }
        
        with self.driver.session() as session:
            result = session.run(query, class_name=class_name, method_name=method_name, max_depth=max_depth)
            
            for record in result:
                depth = record["depth"]
                current_class = record["class_name"]
                current_method = record["method_name"]
                current_visibility = record["method_visibility"]
                next_class = record["next_class"]
                next_method = record["next_method"]
                
                # Build tree structure
                depth_key = f"depth_{depth}"
                if depth_key not in call_tree["tree"]:
                    call_tree["tree"][depth_key] = []
                
                node_info = {
                    "class": current_class,
                    "method": current_method,
                    "visibility": current_visibility,
                    "file_path": record["class_file"],
                    "calls": []
                }
                
                if next_class and next_method:
                    node_info["calls"].append({
                        "class": next_class,
                        "method": next_method
                    })
                
                call_tree["tree"][depth_key].append(node_info)
        
        return call_tree

    def get_method_call_path(self, from_class: str, from_method: str, to_class: str, to_method: str, max_depth: int = 10) -> List[Dict]:
        """Find all paths between two specific methods"""
        query = """
        MATCH (from_class:Class {name: $from_class})-[:HAS_METHOD]->(from_method:Method {name: $from_method})
        MATCH (to_class:Class {name: $to_class})-[:HAS_METHOD]->(to_method:Method {name: $to_method})
        MATCH path = shortestPath((from_method)-[:METHOD_CALL*1..$max_depth]->(to_method))
        WITH nodes(path) as call_path
        UNWIND range(0, size(call_path)-1) as i
        WITH call_path[i] as method_node, i as step
        MATCH (method_node)<-[:HAS_METHOD]-(method_class:Class)
        RETURN method_class.name as class_name, method_class.file_path as class_file,
               method_node.name as method_name, method_node.visibility as method_visibility,
               step
        ORDER BY step
        """
        
        paths = []
        
        with self.driver.session() as session:
            result = session.run(query, 
                               from_class=from_class, from_method=from_method,
                               to_class=to_class, to_method=to_method,
                               max_depth=max_depth)
            
            for record in result:
                paths.append({
                    "step": record["step"],
                    "class": record["class_name"],
                    "method": record["method_name"],
                    "visibility": record["method_visibility"],
                    "file_path": record["class_file"]
                })
        
        return paths

    def get_reverse_call_stack(self, class_name: str, method_name: str, max_depth: int = 5) -> Dict[str, Any]:
        """Find what methods call into this method (reverse lookup)"""
        query = """
        MATCH (target_class:Class {name: $class_name})-[:HAS_METHOD]->(target_method:Method {name: $method_name})
        CALL {
            WITH target_method
            MATCH path = (caller:Method)-[:METHOD_CALL*1..$max_depth]->(target_method)
            WHERE ALL(node IN nodes(path) WHERE single(x IN nodes(path) WHERE x = node))
            WITH nodes(path) as reverse_path
            UNWIND range(0, size(reverse_path)-1) as i
            WITH reverse_path[i] as method_node, i as depth
            MATCH (method_node)<-[:HAS_METHOD]-(method_class:Class)
            RETURN method_class.name as caller_class, method_class.file_path as caller_file,
                   method_node.name as caller_method, method_node.visibility as caller_visibility,
                   depth
        }
        RETURN caller_class, caller_file, caller_method, caller_visibility, depth
        ORDER BY depth, caller_class, caller_method
        """
        
        reverse_stack = {
            "target": {"class": class_name, "method": method_name},
            "callers": {},
            "max_depth": max_depth
        }
        
        with self.driver.session() as session:
            result = session.run(query, class_name=class_name, method_name=method_name, max_depth=max_depth)
            
            for record in result:
                depth = record["depth"]
                caller_class = record["caller_class"]
                caller_method = record["caller_method"]
                caller_visibility = record["caller_visibility"]
                caller_file = record["caller_file"]
                
                depth_key = f"depth_{depth}"
                if depth_key not in reverse_stack["callers"]:
                    reverse_stack["callers"][depth_key] = []
                
                reverse_stack["callers"][depth_key].append({
                    "class": caller_class,
                    "method": caller_method,
                    "visibility": caller_visibility,
                    "file_path": caller_file
                })
        
        return reverse_stack

    def get_call_statistics(self, class_name: str = None) -> Dict[str, Any]:
        """Get detailed call statistics for analysis"""
        if class_name:
            # Implementation for specific class statistics
            pass
        else:
            # Implementation for all classes statistics
            pass
        
        statistics = {
            "class_filter": class_name,
            "methods": [],
            "summary": {
                "total_methods": 0,
                "methods_with_calls": 0,
                "methods_called_by_others": 0,
                "total_call_relationships": 0
            }
        }
        
        with self.driver.session() as session:
            # Implementation details would go here
            pass
        
        return statistics

    def get_all_methods_for_review(self) -> List[Dict[str, Any]]:
        """Get all methods with their definitions for LLM review"""
        query = """
        MATCH (c:Class)-[:HAS_METHOD]->(m:Method)
        WHERE m.definition IS NOT NULL AND m.definition <> ''
        RETURN elementId(m) as method_id,
               m.name as method_name,
               m.definition as method_definition,
               m.visibility as method_visibility,
               c.name as class_name,
               c.file_path as file_path
        ORDER BY c.name, m.name
        """
        
        methods = []
        with self.driver.session() as session:
            result = session.run(query)
            for record in result:
                methods.append({
                    "method_id": record["method_id"],
                    "method_name": record["method_name"],
                    "definition": record["method_definition"],
                    "visibility": record["method_visibility"],
                    "class_name": record["class_name"],
                    "file_path": record["file_path"]
                })
        
        return methods

    def add_review(self, method_id: str, review_data: Dict[str, Any]) -> str:
        """Add a review node linked to a method"""
        query = """
        MATCH (m:Method) WHERE elementId(m) = $method_id
        CREATE (r:Review {
            method_name: $method_name,
            class_name: $class_name,
            severity: $severity,
            issue_type: $issue_type,
            description: $description,
            recommendation: $recommendation,
            line_reference: $line_reference,
            created_at: datetime()
        })
        CREATE (m)-[:HAS_REVIEW]->(r)
        RETURN elementId(r) as review_id
        """
        
        with self.driver.session() as session:
            result = session.run(query,
                method_id=method_id,
                method_name=review_data.get("method_name"),
                class_name=review_data.get("class_name"),
                severity=review_data.get("severity"),
                issue_type=review_data.get("issue_type"),
                description=review_data.get("description"),
                recommendation=review_data.get("recommendation"),
                line_reference=review_data.get("line_reference")
            )
            return result.single()["review_id"]

    def clear_existing_reviews(self):
        """Clear all existing review nodes"""
        query = """
        MATCH (r:Review)
        DETACH DELETE r
        """
        
        with self.driver.session() as session:
            session.run(query)
