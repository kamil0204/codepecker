# Graph Database Architecture

The codebase analyzer uses a modular graph database architecture focused on Neo4j for optimal graph operations.

## Architecture Overview

```
GraphDatabaseInterface (Abstract)
    ├── Neo4jGraphDB (Implemented) ⭐ Primary - neo4j_graph_db.py
    ├── MemgraphGraphDB (Placeholder) - future_graph_dbs.py
    ├── ArangoDBGraphDB (Placeholder) - future_graph_dbs.py
    └── TigerGraphDB (Placeholder) - future_graph_dbs.py

GraphDatabaseFactory
    └── Creates database instances based on configuration

CallStackGraphDB (Wrapper)
    └── Provides backward compatibility
```

## Files Structure

- `graph_db_interface.py` - Abstract interface defining all database operations
- `neo4j_graph_db.py` - Neo4j implementation (primary)
- `graph_db_factory.py` - Factory pattern for creating database instances
- `config.py` - Configuration management for databases
- `future_graph_dbs.py` - Placeholder implementations for other databases (Memgraph, ArangoDB, TigerGraph)

## Usage Examples

### 1. Using Default Configuration (Neo4j)
```python
from graph_db_factory import CallStackGraphDB

# Uses Neo4j by default (reads from .env file)
graph_db = CallStackGraphDB()
```

### 2. Specifying Database Type
```python
# Neo4j with custom connection
graph_db = CallStackGraphDB(
    db_type="neo4j", 
    uri="bolt://localhost:7687",
    username="neo4j", 
    password="your_password"
)
```

### 3. Using Environment Variables
```bash
# Neo4j configuration (in .env file)
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password

# Future examples for other databases:
# export CODEPECKER_DB_TYPE=memgraph
# export CODEPECKER_DB_TYPE=arangodb
```

### 4. Using Factory Directly
```python
from graph_db_factory import GraphDatabaseFactory

# Create specific database instance
db = GraphDatabaseFactory.create_database("neo4j", 
    uri="bolt://localhost:7687", 
    username="neo4j", 
    password="password")
```

## Adding New Database Implementations

To add a new graph database (e.g., Memgraph):

1. **Implement the Interface**:
   ```python
   class MemgraphGraphDB(GraphDatabaseInterface):
       def initialize(self): ...
       def add_class(self, ...): ...
       def add_method(self, ...): ...
       # ... implement all abstract methods
   ```

2. **Update Factory**:
   ```python
   # In GraphDatabaseFactory.create_database()
   elif db_type == "memgraph":
       return MemgraphGraphDB(**kwargs)
   ```

3. **Add Configuration**:
   ```python
   # In Config class
   MEMGRAPH_URI = os.getenv("CODEPECKER_MEMGRAPH_URI", "bolt://localhost:7687")
   ```

4. **No changes needed in main ingestion code!**

## Current Implementation

- ✅ **Neo4j**: Fully implemented and tested (Primary)
- 🚧 **Memgraph**: Interface ready, implementation pending  
- 🚧 **ArangoDB**: Interface ready, implementation pending
- 🚧 **TigerGraph**: Interface ready, implementation pending

## Benefits

1. **Focused on Neo4j**: Optimized for graph database operations
2. **No Code Changes**: Main ingestion code remains unchanged
3. **Extensible**: Add new databases without modifying existing code
4. **Backward Compatible**: Existing code continues to work
5. **Testable**: Easy to mock different database implementations

## Migration Path

The current implementation maintains full backward compatibility. Existing code using `CallStackGraphDB` will continue to work without any changes, while new code can leverage the factory pattern for more flexibility.
