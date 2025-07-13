"""
Web API server for CodePecker - serves data from Neo4j database
"""
import sys
import os
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from src.database.graph_db_factory import CallStackGraphDB
from src.core.config import Config

app = Flask(__name__, template_folder='web/templates', static_folder='web/static')
CORS(app)

# Global database instance
graph_db = None

def initialize_database():
    """Initialize the database connection"""
    global graph_db
    try:
        db_config = Config.get_database_config()
        
        # For the web server, we never want to clear the database
        # Override the clear_db setting if it exists
        if 'clear_db' in db_config:
            db_config['clear_db'] = False
        
        graph_db = CallStackGraphDB(
            db_type=Config.DATABASE_TYPE, 
            **db_config
        )
        print("✅ Database connection established")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

@app.route('/')
def index():
    """Serve the main UI page"""
    return render_template('index.html')

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "database_connected": graph_db is not None,
        "database_type": Config.DATABASE_TYPE
    })

@app.route('/api/classes')
def get_classes():
    """Get all classes (entry points) from the database"""
    if not graph_db:
        return jsonify({"error": "Database not connected"}), 500
    
    try:
        with graph_db.db.driver.session() as session:
            query = """
            MATCH (c:Class)
            RETURN c.name as name, 
                   c.file_path as file_path, 
                   c.visibility as visibility
            ORDER BY c.name
            """
            result = session.run(query)
            
            classes = []
            for record in result:
                classes.append({
                    "name": record["name"],
                    "file_path": record["file_path"],
                    "visibility": record["visibility"]
                })
            
            return jsonify({
                "classes": classes,
                "count": len(classes)
            })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/class/<class_name>/graph')
def get_class_graph(class_name):
    """Get the complete graph for a specific class"""
    if not graph_db:
        return jsonify({"error": "Database not connected"}), 500
    
    try:
        with graph_db.db.driver.session() as session:
            # Get class info
            class_query = """
            MATCH (c:Class {name: $class_name})
            RETURN c.name as name, 
                   c.file_path as file_path, 
                   c.visibility as visibility
            """
            class_result = session.run(class_query, class_name=class_name)
            class_record = class_result.single()
            
            if not class_record:
                return jsonify({"error": "Class not found"}), 404
            
            # Get methods and their calls
            methods_query = """
            MATCH (c:Class {name: $class_name})-[:HAS_METHOD]->(m:Method)
            OPTIONAL MATCH (m)-[call:CALLS]->()
            RETURN m.name as method_name, 
                   m.visibility as method_visibility,
                   collect(call.method_name) as method_calls
            ORDER BY m.name
            """
            methods_result = session.run(methods_query, class_name=class_name)
            
            methods = []
            for method_record in methods_result:
                # Filter out None values from method_calls
                method_calls = [call for call in method_record["method_calls"] if call is not None]
                
                methods.append({
                    "name": method_record["method_name"],
                    "visibility": method_record["method_visibility"],
                    "calls": method_calls
                })
            
            class_info = {
                "name": class_record["name"],
                "file_path": class_record["file_path"],
                "visibility": class_record["visibility"],
                "methods": methods
            }
            
            return jsonify(class_info)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/graph/full')
def get_full_graph():
    """Get the complete graph data for visualization"""
    if not graph_db:
        return jsonify({"error": "Database not connected"}), 500
    
    try:
        with graph_db.db.driver.session() as session:
            # Get all nodes and relationships
            query = """
            MATCH (c:Class)
            OPTIONAL MATCH (c)-[:HAS_METHOD]->(m:Method)
            OPTIONAL MATCH (m)-[call:CALLS]->()
            RETURN c.name as class_name,
                   c.file_path as class_file_path,
                   c.visibility as class_visibility,
                   collect({
                       name: m.name,
                       visibility: m.visibility,
                       calls: call.method_name
                   }) as methods
            ORDER BY c.name
            """
            result = session.run(query)
            
            nodes = []
            edges = []
            node_id_counter = 0
            
            for record in result:
                class_name = record["class_name"]
                class_node_id = f"class_{node_id_counter}"
                node_id_counter += 1
                
                # Add class node
                nodes.append({
                    "id": class_node_id,
                    "label": class_name,
                    "type": "class",
                    "file_path": record["class_file_path"],
                    "visibility": record["class_visibility"]
                })
                
                # Process methods
                methods = record["methods"]
                if methods and methods[0]["name"]:  # Check if methods exist
                    for method in methods:
                        if method["name"]:  # Skip null methods
                            method_node_id = f"method_{node_id_counter}"
                            node_id_counter += 1
                            
                            # Add method node
                            nodes.append({
                                "id": method_node_id,
                                "label": method["name"],
                                "type": "method",
                                "visibility": method["visibility"]
                            })
                            
                            # Add edge from class to method
                            edges.append({
                                "from": class_node_id,
                                "to": method_node_id,
                                "type": "has_method"
                            })
                            
                            # Add method call edges
                            if method["calls"]:
                                # For now, just show that this method makes calls
                                # In a more complex version, we'd link to actual method nodes
                                pass
            
            return jsonify({
                "nodes": nodes,
                "edges": edges,
                "stats": {
                    "total_classes": len([n for n in nodes if n["type"] == "class"]),
                    "total_methods": len([n for n in nodes if n["type"] == "method"])
                }
            })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats')
def get_stats():
    """Get database statistics"""
    if not graph_db:
        return jsonify({"error": "Database not connected"}), 500
    
    try:
        with graph_db.db.driver.session() as session:
            stats_query = """
            MATCH (c:Class)
            OPTIONAL MATCH (c)-[:HAS_METHOD]->(m:Method)
            OPTIONAL MATCH (m)-[call:CALLS]->()
            RETURN count(DISTINCT c) as total_classes,
                   count(DISTINCT m) as total_methods,
                   count(call) as total_method_calls
            """
            result = session.run(stats_query)
            stats_record = result.single()
            
            return jsonify({
                "total_classes": stats_record["total_classes"],
                "total_methods": stats_record["total_methods"],
                "total_method_calls": stats_record["total_method_calls"]
            })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def main():
    """Main entry point for the server"""
    print("🚀 Starting CodePecker Web Server...")
    
    # Initialize database connection
    if not initialize_database():
        print("❌ Failed to initialize database. Please ensure:")
        print("   1. Neo4j is running")
        print("   2. Environment variables are set correctly")
        print("   3. Database contains ingested data")
        return
    
    print(f"🌐 Server starting on http://localhost:5000")
    print("📊 API endpoints available:")
    print("   GET /api/health - Health check")
    print("   GET /api/classes - List all classes")
    print("   GET /api/class/<name>/graph - Get class graph")
    print("   GET /api/graph/full - Get full graph")
    print("   GET /api/stats - Database statistics")
    print()
    
    # Start the Flask server
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    main()
