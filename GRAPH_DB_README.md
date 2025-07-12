# Graph Database Architecture

The codebase analyzer now supports a modular graph database architecture that allows easy switching between different database implementations.

## Architecture Overview

```
GraphDatabaseInterface (Abstract)
    ├── SQLiteGraphDB (Implemented)
    ├── Neo4jGraphDB (Placeholder)
    ├── MemgraphGraphDB (Placeholder)
    └── ArangoDBGraphDB (Placeholder)

GraphDatabaseFactory
    └── Creates database instances based on configuration

CallStackGraphDB (Wrapper)
    └── Provides backward compatibility
```

## Files Structure

- `graph_db_interface.py` - Abstract interface defining all database operations
- `sqlite_graph_db.py` - SQLite implementation (currently active)
- `graph_db_factory.py` - Factory pattern for creating database instances
- `config.py` - Configuration management for different databases
- `future_graph_dbs.py` - Placeholder implementations for other databases

## Usage Examples

### 1. Using Default Configuration (SQLite)
```python
from graph_db_factory import CallStackGraphDB

# Uses SQLite by default
graph_db = CallStackGraphDB()
```

### 2. Specifying Database Type
```python
# SQLite with custom path
graph_db = CallStackGraphDB(db_type="sqlite", db_path="custom.db")

# Future: Neo4j
# graph_db = CallStackGraphDB(db_type="neo4j", uri="bolt://localhost:7687")
```

### 3. Using Environment Variables
```bash
# Switch to different databases via environment
export CODEPECKER_DB_TYPE=sqlite
export CODEPECKER_SQLITE_PATH=/path/to/database.db

# Future examples:
# export CODEPECKER_DB_TYPE=neo4j
# export CODEPECKER_NEO4J_URI=bolt://localhost:7687
```

### 4. Using Factory Directly
```python
from graph_db_factory import GraphDatabaseFactory

# Create specific database instance
db = GraphDatabaseFactory.create_database("sqlite", db_path="test.db")
```

## Adding New Database Implementations

To add a new graph database (e.g., Neo4j):

1. **Implement the Interface**:
   ```python
   class Neo4jGraphDB(GraphDatabaseInterface):
       def initialize(self): ...
       def add_class(self, ...): ...
       def add_method(self, ...): ...
       # ... implement all abstract methods
   ```

2. **Update Factory**:
   ```python
   # In GraphDatabaseFactory.create_database()
   elif db_type == "neo4j":
       return Neo4jGraphDB(**kwargs)
   ```

3. **Add Configuration**:
   ```python
   # In Config class
   NEO4J_URI = os.getenv("CODEPECKER_NEO4J_URI", "bolt://localhost:7687")
   ```

4. **No changes needed in main application code!**

## Current Implementation

- ✅ **SQLite**: Fully implemented and tested
- 🚧 **Neo4j**: Interface ready, implementation pending
- 🚧 **Memgraph**: Interface ready, implementation pending  
- 🚧 **ArangoDB**: Interface ready, implementation pending

## Benefits

1. **Easy Switching**: Change database via configuration
2. **No Code Changes**: Main application code remains unchanged
3. **Extensible**: Add new databases without modifying existing code
4. **Backward Compatible**: Existing code continues to work
5. **Testable**: Easy to mock different database implementations

## Migration Path

The current implementation maintains full backward compatibility. Existing code using `CallStackGraphDB` will continue to work without any changes, while new code can leverage the factory pattern for more flexibility.
