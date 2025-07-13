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
            OPTIONAL MATCH (m)-[call:CALLS]->()
            RETURN count(DISTINCT c) as total_classes,
                   count(DISTINCT m) as total_methods,
                   count(call) as total_method_calls
            """
            result = session.run(stats_query)
            stats_record = result.single()
            
            return StatsResponse(
                total_classes=stats_record["total_classes"],
                total_methods=stats_record["total_methods"],
                total_method_calls=stats_record["total_method_calls"]
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    print("   GET /api/health - Health check")
    print("   GET /api/classes - List all classes")
    print("   GET /api/class/{name}/graph - Get class graph")
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
