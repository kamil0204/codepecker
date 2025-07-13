"""
Web API server for CodePecker - serves data from Neo4j database using FastAPI
"""
import sys
import os
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from src.database.graph_db_factory import CallStackGraphDB
from src.core.config import Config

# FastAPI app instance
app = FastAPI(
    title="CodePecker API",
    description="Code Analysis API - serves data from Neo4j database",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="src/web/static"), name="static")

# Global database instance
graph_db = None

# Pydantic models for request/response validation
class HealthResponse(BaseModel):
    status: str
    database_connected: bool
    database_type: str

class ClassInfo(BaseModel):
    name: str
    file_path: Optional[str]
    visibility: str

class ClassesResponse(BaseModel):
    classes: List[ClassInfo]
    count: int

class MethodInfo(BaseModel):
    name: str
    visibility: str
    calls: List[str]

class ClassGraphResponse(BaseModel):
    name: str
    file_path: Optional[str]
    visibility: str
    methods: List[MethodInfo]

class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    file_path: Optional[str] = None
    visibility: Optional[str] = None

class GraphEdge(BaseModel):
    source: str
    target: str
    type: str

class FullGraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    stats: Dict[str, int]

class StatsResponse(BaseModel):
    total_classes: int
    total_methods: int
    total_method_calls: int

class RecursiveCallInfo(BaseModel):
    caller_class: str
    caller_method: str
    callee_class: str
    callee_method: str
    depth: int

class RecursiveMethodInfo(BaseModel):
    name: str
    visibility: str
    recursive_calls: Dict[str, RecursiveCallInfo]
    max_depth_reached: int

class RecursiveCallStackResponse(BaseModel):
    class_name: str
    file_path: Optional[str]
    methods: Dict[str, RecursiveMethodInfo]
    max_depth: int

class CallTreeNode(BaseModel):
    class_name: str
    method: str
    visibility: str
    file_path: Optional[str]
    calls: List[Dict[str, str]]

class CallTreeResponse(BaseModel):
    root: Dict[str, str]
    tree: Dict[str, List[CallTreeNode]]
    max_depth: int

class CallPathStep(BaseModel):
    step: int
    class_name: str
    method: str
    visibility: str
    file_path: Optional[str]

class CallPathResponse(BaseModel):
    from_method: Dict[str, str]
    to_method: Dict[str, str]
    path: List[CallPathStep]
    path_length: int

class CallerInfo(BaseModel):
    class_name: str
    method: str
    visibility: str
    file_path: Optional[str]

class ReverseCallStackResponse(BaseModel):
    target: Dict[str, str]
    callers: Dict[str, List[CallerInfo]]
    max_depth: int

class MethodStatistics(BaseModel):
    class_name: str
    method: str
    visibility: str
    file_path: Optional[str]
    outgoing_calls: int
    incoming_calls: int
    total_calls: int

class CallStatisticsResponse(BaseModel):
    class_filter: Optional[str]
    methods: List[MethodStatistics]
    summary: Dict[str, int]

class ErrorResponse(BaseModel):
    error: str

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

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    if not initialize_database():
        print("❌ Failed to initialize database. Please ensure:")
        print("   1. Neo4j is running")
        print("   2. Environment variables are set correctly")
        print("   3. Database contains ingested data")

@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the main UI page"""
    try:
        with open("src/web/templates/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Index page not found")

@app.get("/call-stack", response_class=HTMLResponse)
async def call_stack_page():
    """Serve the call stack viewer page"""
    try:
        with open("src/web/templates/call-stack.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Call stack page not found")

@app.get("/advanced-call-stack", response_class=HTMLResponse)
async def advanced_call_stack_page():
    """Serve the advanced call stack viewer page with recursive analysis"""
    try:
        with open("src/web/templates/advanced-call-stack.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Advanced call stack page not found")

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        database_connected=graph_db is not None,
        database_type=Config.DATABASE_TYPE
    )

@app.get("/api/classes", response_model=ClassesResponse)
async def get_classes():
    """Get all classes (entry points) from the database"""
    if not graph_db:
        raise HTTPException(status_code=500, detail="Database not connected")
    
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
                classes.append(ClassInfo(
                    name=record["name"],
                    file_path=record["file_path"],
                    visibility=record["visibility"]
                ))
            
            return ClassesResponse(
                classes=classes,
                count=len(classes)
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/class/{class_name}/graph", response_model=ClassGraphResponse)
async def get_class_graph(class_name: str):
    """Get the complete graph for a specific class"""
    if not graph_db:
        raise HTTPException(status_code=500, detail="Database not connected")
    
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
                raise HTTPException(status_code=404, detail="Class not found")
            
            # Get methods and their calls
            methods_query = """
            MATCH (c:Class {name: $class_name})-[:HAS_METHOD]->(m:Method)
            OPTIONAL MATCH (m)-[:METHOD_CALL]->(target_method:Method)<-[:HAS_METHOD]-(target_class:Class)
            RETURN m.name as method_name, 
                   m.visibility as method_visibility,
                   collect(DISTINCT target_class.name + '.' + target_method.name) as method_calls
            ORDER BY m.name
            """
            methods_result = session.run(methods_query, class_name=class_name)
            
            methods = []
            for method_record in methods_result:
                # Filter out None values from method_calls
                method_calls = [call for call in method_record["method_calls"] if call is not None]
                
                methods.append(MethodInfo(
                    name=method_record["method_name"],
                    visibility=method_record["method_visibility"],
                    calls=method_calls
                ))
            
            return ClassGraphResponse(
                name=class_record["name"],
                file_path=class_record["file_path"],
                visibility=class_record["visibility"],
                methods=methods
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/graph/full", response_model=FullGraphResponse)
async def get_full_graph():
    """Get the complete graph data for visualization"""
    if not graph_db:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    try:
        with graph_db.db.driver.session() as session:
            # Get all nodes and relationships
            query = """
            MATCH (c:Class)
            OPTIONAL MATCH (c)-[:HAS_METHOD]->(m:Method)
            OPTIONAL MATCH (m)-[:METHOD_CALL]->(target_method:Method)<-[:HAS_METHOD]-(target_class:Class)
            RETURN c.name as class_name,
                   c.file_path as class_file_path,
                   c.visibility as class_visibility,
                   collect({
                       name: m.name,
                       visibility: m.visibility,
                       calls: target_class.name + '.' + target_method.name
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
                nodes.append(GraphNode(
                    id=class_node_id,
                    label=class_name,
                    type="class",
                    file_path=record["class_file_path"],
                    visibility=record["class_visibility"]
                ))
                
                # Process methods
                methods = record["methods"]
                if methods and methods[0]["name"]:  # Check if methods exist
                    for method in methods:
                        if method["name"]:  # Skip null methods
                            method_node_id = f"method_{node_id_counter}"
                            node_id_counter += 1
                            
                            # Add method node
                            nodes.append(GraphNode(
                                id=method_node_id,
                                label=method["name"],
                                type="method",
                                visibility=method["visibility"]
                            ))
                            
                            # Add edge from class to method
                            edges.append(GraphEdge(
                                source=class_node_id,
                                target=method_node_id,
                                type="has_method"
                            ))
                            
                            # Add method call edges
                            if method["calls"]:
                                # For now, just show that this method makes calls
                                # In a more complex version, we'd link to actual method nodes
                                pass
            
            return FullGraphResponse(
                nodes=nodes,
                edges=edges,
                stats={
                    "total_classes": len([n for n in nodes if n.type == "class"]),
                    "total_methods": len([n for n in nodes if n.type == "method"])
                }
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Get database statistics"""
    if not graph_db:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    try:
        with graph_db.db.driver.session() as session:
            stats_query = """
            MATCH (c:Class)
            OPTIONAL MATCH (c)-[:HAS_METHOD]->(m:Method)
            OPTIONAL MATCH (m)-[r:METHOD_CALL]->()
            RETURN count(DISTINCT c) as total_classes,
                   count(DISTINCT m) as total_methods,
                   count(r) as total_method_calls
            """
            result = session.run(stats_query)
            stats_record = result.single()
            
            return StatsResponse(
                total_classes=stats_record["total_classes"],
                total_methods=stats_record["total_methods"],
                total_method_calls=stats_record["total_method_calls"]
            )
    
    except Exception as e:
        print(f"Error in stats endpoint: {e}")
        raise HTTPException(status_code=500, detail="Database query failed")

@app.get("/api/call-stack/{class_name}")
async def get_call_stack(class_name: str):
    """Get complete call stack for a specific class"""
    if not graph_db:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    try:
        call_stack = graph_db.get_call_stack(class_name)
        return call_stack
    except Exception as e:
        print(f"Error in call-stack endpoint for {class_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get call stack: {str(e)}")

@app.get("/api/call-stack/{class_name}/{method_name}")
async def get_method_call_stack(class_name: str, method_name: str):
    """Get call stack for a specific method in a class"""
    if not graph_db:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    try:
        call_stack = graph_db.get_method_call_stack(class_name, method_name)
        return call_stack
    except Exception as e:
        print(f"Error in method call-stack endpoint for {class_name}.{method_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get method call stack: {str(e)}")

@app.get("/api/call-stack/{class_name}/recursive", response_model=RecursiveCallStackResponse)
async def get_recursive_call_stack(class_name: str, max_depth: int = 10):
    """Get complete recursive call stack for a class with configurable depth"""
    if not graph_db:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    if max_depth > 20:
        raise HTTPException(status_code=400, detail="Maximum depth cannot exceed 20 to prevent performance issues")
    
    try:
        result = graph_db.db.get_recursive_call_stack(class_name, max_depth)
        
        # Transform the result to match our response model
        if not result:
            raise HTTPException(status_code=404, detail="Class not found or no call stack data")
        
        class_info = list(result.keys())[0]
        class_data = result[class_info]
        
        methods = {}
        for method_name, method_data in class_data["methods"].items():
            recursive_calls = {}
            for call_key, call_info in method_data["recursive_calls"].items():
                recursive_calls[call_key] = RecursiveCallInfo(**call_info)
            
            methods[method_name] = RecursiveMethodInfo(
                name=method_name,
                visibility=method_data["visibility"],
                recursive_calls=recursive_calls,
                max_depth_reached=method_data["max_depth_reached"]
            )
        
        return RecursiveCallStackResponse(
            class_name=class_info,
            file_path=class_data["file_path"],
            methods=methods,
            max_depth=max_depth
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in recursive call-stack endpoint for {class_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recursive call stack: {str(e)}")

@app.get("/api/call-tree/{class_name}/{method_name}", response_model=CallTreeResponse)
async def get_method_call_tree(class_name: str, method_name: str, max_depth: int = 5):
    """Get hierarchical call tree for a specific method"""
    if not graph_db:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    if max_depth > 15:
        raise HTTPException(status_code=400, detail="Maximum depth cannot exceed 15 for tree visualization")
    
    try:
        result = graph_db.db.get_method_call_tree(class_name, method_name, max_depth)
        
        # Transform tree data to match response model
        tree_data = {}
        for depth_key, nodes in result["tree"].items():
            tree_nodes = []
            for node in nodes:
                tree_nodes.append(CallTreeNode(
                    class_name=node["class"],
                    method=node["method"],
                    visibility=node["visibility"],
                    file_path=node["file_path"],
                    calls=node["calls"]
                ))
            tree_data[depth_key] = tree_nodes
        
        return CallTreeResponse(
            root=result["root"],
            tree=tree_data,
            max_depth=result["max_depth"]
        )
    
    except Exception as e:
        print(f"Error in call-tree endpoint for {class_name}.{method_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get call tree: {str(e)}")

@app.get("/api/call-path", response_model=CallPathResponse)
async def get_method_call_path(
    from_class: str, 
    from_method: str, 
    to_class: str, 
    to_method: str, 
    max_depth: int = 10
):
    """Find all paths between two specific methods"""
    if not graph_db:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    if max_depth > 20:
        raise HTTPException(status_code=400, detail="Maximum depth cannot exceed 20")
    
    try:
        path_steps = graph_db.db.get_method_call_path(from_class, from_method, to_class, to_method, max_depth)
        
        if not path_steps:
            raise HTTPException(status_code=404, detail="No path found between the specified methods")
        
        # Transform path steps to match response model
        path = []
        for step in path_steps:
            path.append(CallPathStep(
                step=step["step"],
                class_name=step["class"],
                method=step["method"],
                visibility=step["visibility"],
                file_path=step["file_path"]
            ))
        
        return CallPathResponse(
            from_method={"class": from_class, "method": from_method},
            to_method={"class": to_class, "method": to_method},
            path=path,
            path_length=len(path)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in call-path endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get call path: {str(e)}")

@app.get("/api/reverse-call-stack/{class_name}/{method_name}", response_model=ReverseCallStackResponse)
async def get_reverse_call_stack(class_name: str, method_name: str, max_depth: int = 5):
    """Find what methods call into this method (reverse lookup)"""
    if not graph_db:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    if max_depth > 15:
        raise HTTPException(status_code=400, detail="Maximum depth cannot exceed 15")
    
    try:
        result = graph_db.db.get_reverse_call_stack(class_name, method_name, max_depth)
        
        # Transform callers data to match response model
        callers = {}
        for depth_key, caller_list in result["callers"].items():
            transformed_callers = []
            for caller in caller_list:
                transformed_callers.append(CallerInfo(
                    class_name=caller["class"],
                    method=caller["method"],
                    visibility=caller["visibility"],
                    file_path=caller["file_path"]
                ))
            callers[depth_key] = transformed_callers
        
        return ReverseCallStackResponse(
            target=result["target"],
            callers=callers,
            max_depth=result["max_depth"]
        )
    
    except Exception as e:
        print(f"Error in reverse call-stack endpoint for {class_name}.{method_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get reverse call stack: {str(e)}")

@app.get("/api/call-statistics", response_model=CallStatisticsResponse)
@app.get("/api/call-statistics/{class_name}", response_model=CallStatisticsResponse)
async def get_call_statistics(class_name: Optional[str] = None):
    """Get detailed call statistics for analysis"""
    if not graph_db:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    try:
        result = graph_db.db.get_call_statistics(class_name)
        
        # Transform methods data to match response model
        methods = []
        for method in result["methods"]:
            methods.append(MethodStatistics(
                class_name=method["class"],
                method=method["method"],
                visibility=method["visibility"],
                file_path=method["file_path"],
                outgoing_calls=method["outgoing_calls"],
                incoming_calls=method["incoming_calls"],
                total_calls=method["total_calls"]
            ))
        
        return CallStatisticsResponse(
            class_filter=result["class_filter"],
            methods=methods,
            summary=result["summary"]
        )
    
    except Exception as e:
        print(f"Error in call-statistics endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get call statistics: {str(e)}")

# TODO: Add NetworkX-based graph visualization endpoints
# 
# Priority: HIGH - Interactive graph UI layer for visual drill-down experience
# 
# Planned endpoints:
# @app.get("/api/graph/networkx/{class_name}")
# async def get_networkx_graph(class_name: str, layout: str = "spring"):
#     """Generate NetworkX graph with positioned nodes for frontend visualization"""
#     # 1. Query Neo4j for class and its relationships
#     # 2. Build NetworkX DiGraph from the data
#     # 3. Apply layout algorithm (spring, circular, hierarchical)
#     # 4. Return positioned nodes/edges for D3.js/Cytoscape.js rendering
#     # 5. Support different zoom levels (class-only, with-methods, with-calls)
# 
# @app.get("/api/graph/export/{class_name}")
# async def export_graph(class_name: str, format: str = "png"):
#     """Export graph visualization as image (PNG/SVG/PDF)"""
#     # Generate graph using matplotlib/plotly and return file
# 
# Features to implement:
# - Interactive drill-down: Class → Methods → Method calls
# - Multiple layout algorithms: spring, hierarchical, circular
# - Visual coding: colors/shapes for visibility (public/private)
# - Search and filtering within the graph
# - Path highlighting for call chains
# - Zoom/pan functionality
# - Export capabilities
# 
# Dependencies needed:
# pip install networkx matplotlib plotly python-igraph
# 
# Frontend integration:
# - D3.js or Cytoscape.js for web-based graph rendering
# - Interactive navigation and node selection
# - Real-time layout switching
def main():
    """Main entry point for the server"""
    print("🚀 Starting CodePecker FastAPI Server...")
    
    print(f"🌐 Server will start on http://localhost:8000")
    print("📊 API endpoints available:")
    print("   GET / - Web interface")
    print("   GET /call-stack - Call stack viewer")
    print("   GET /advanced-call-stack - Advanced recursive call stack viewer")
    print("   GET /api/health - Health check")
    print("   GET /api/classes - List all classes")
    print("   GET /api/class/{name}/graph - Get class graph")
    print("   GET /api/call-stack/{name} - Get call stack for class")
    print("   GET /api/call-stack/{name}/{method} - Get nested call stack for method")
    print("   GET /api/call-stack/{name}/recursive?max_depth=10 - Get recursive call stack")
    print("   GET /api/call-tree/{name}/{method}?max_depth=5 - Get hierarchical call tree")
    print("   GET /api/call-path?from_class=A&from_method=B&to_class=C&to_method=D - Find call paths")
    print("   GET /api/reverse-call-stack/{name}/{method} - Get reverse call stack (who calls this)")
    print("   GET /api/call-statistics - Get call statistics for all classes")
    print("   GET /api/call-statistics/{name} - Get call statistics for specific class")
    print("   GET /api/graph/full - Get full graph")
    print("   GET /api/stats - Database statistics")
    print("   GET /docs - Swagger UI documentation")
    print("   GET /redoc - ReDoc documentation")
    print()
    
    # Start the FastAPI server with Uvicorn
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )

if __name__ == '__main__':
    main()
