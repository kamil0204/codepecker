# CodePecker - TODO & Roadmap

## Current Status ✅
- [x] Data ingestion pipeline with LLM + tree-sitter
- [x] Neo4j graph database implementation
- [x] FastAPI web server with auto-generated docs
- [x] Basic web UI for browsing classes and methods
- [x] REST API endpoints for data access

## Immediate Priorities 🚀

### 1. Interactive Graph Visualization (HIGH PRIORITY)
**TODO: Build NetworkX-based Graph UI Layer**

**Goal**: Create an interactive, visual drill-down experience for exploring code relationships

**Implementation Plan**:
- [ ] **Backend**: Add NetworkX integration to generate graph layouts
  - [ ] Install `networkx` and `matplotlib` dependencies
  - [ ] Create new API endpoint `/api/graph/networkx/{class_name}` 
  - [ ] Generate graph layouts using NetworkX algorithms (spring, hierarchical, circular)
  - [ ] Export graph data in formats suitable for web visualization (JSON, GraphML)

- [ ] **Frontend**: Interactive graph visualization
  - [ ] Integrate D3.js or Cytoscape.js for web-based graph rendering
  - [ ] Implement drill-down navigation (click class → show methods → show calls)
  - [ ] Add zoom, pan, and node selection capabilities
  - [ ] Create different layout options (hierarchical, force-directed, circular)

- [ ] **Features**:
  - [ ] **Multi-level navigation**: Class level → Method level → Call chain level
  - [ ] **Visual coding**: Different colors/shapes for public/private methods
  - [ ] **Search & filter**: Find specific classes/methods in the graph
  - [ ] **Path highlighting**: Show call chains and dependencies
  - [ ] **Export options**: Save graphs as PNG/SVG/PDF

**Benefits**:
- Visual understanding of code architecture
- Quick identification of code hotspots and dependencies  
- Interactive exploration replaces static text output
- Better UX for large codebases

**Technical Stack**:
- Backend: FastAPI + NetworkX + Matplotlib/Plotly
- Frontend: D3.js/Cytoscape.js + HTML5 Canvas
- Data format: JSON graph structure

## Future Enhancements 🔮

### 2. Advanced Analysis Features
- [ ] **Dependency Analysis**: Identify circular dependencies and architectural violations
- [ ] **Code Metrics**: Calculate complexity metrics, coupling, cohesion
- [ ] **Change Impact Analysis**: Show which components are affected by changes
- [ ] **Performance Hotspots**: Identify frequently called methods

### 3. Multi-Language Support
- [ ] **JavaScript/TypeScript**: Add tree-sitter parsers for frontend code
- [ ] **Python**: Support for Python codebases
- [ ] **Java**: Enterprise application analysis
- [ ] **Cross-language**: Visualize polyglot applications

### 4. Enterprise Features
- [ ] **Git Integration**: Track code evolution over time
- [ ] **CI/CD Integration**: Automated analysis on code commits
- [ ] **Team Collaboration**: Share and annotate graph visualizations
- [ ] **Reporting**: Generate architectural reports and documentation

### 5. Performance & Scalability
- [ ] **Caching Layer**: Redis/Memcached for frequently accessed graphs
- [ ] **Incremental Updates**: Update only changed parts of the graph
- [ ] **Large Codebases**: Handle enterprise-scale applications (10k+ classes)
- [ ] **Parallel Processing**: Multi-threaded analysis and rendering

## Implementation Notes 📝

### NetworkX Integration Example
```python
# New endpoint structure
@app.get("/api/graph/networkx/{class_name}")
async def get_networkx_graph(class_name: str, layout: str = "spring"):
    """Generate NetworkX graph layout for visualization"""
    
    # 1. Get graph data from Neo4j
    # 2. Build NetworkX graph
    # 3. Apply layout algorithm
    # 4. Return positioned nodes/edges for frontend
    
    import networkx as nx
    G = nx.DiGraph()
    
    # Add nodes and edges from database
    # Apply layout (spring, circular, hierarchical)
    pos = nx.spring_layout(G) if layout == "spring" else nx.circular_layout(G)
    
    # Return positioned graph data
    return {
        "nodes": [{"id": node, "x": pos[node][0], "y": pos[node][1]} for node in G.nodes()],
        "edges": [{"source": edge[0], "target": edge[1]} for edge in G.edges()]
    }
```

### Frontend Visualization Example
```javascript
// D3.js integration for interactive graphs
function renderGraph(graphData) {
    // Create SVG canvas
    // Draw nodes and edges with D3.js
    // Add interactions (click, drag, zoom)
    // Implement drill-down navigation
}
```

## Dependencies to Add 📦
```bash
# For graph analysis and visualization
pip install networkx matplotlib plotly

# For advanced layouts (optional)
pip install python-igraph pygraphviz
```

---

**Priority**: The NetworkX graph visualization should be the next major feature development as it will significantly enhance the user experience and make the tool more valuable for architectural analysis.
