"""
Configuration settings for the codebase analyzer
"""
import os
from typing import Dict, Any


class Config:
    """Configuration class for codebase analyzer settings"""
    
    # Database configuration
    DATABASE_TYPE = os.getenv("CODEPECKER_DB_TYPE", "sqlite")  # sqlite, neo4j, memgraph, arangodb
    
    # SQLite specific settings
    SQLITE_DB_PATH = os.getenv("CODEPECKER_SQLITE_PATH", "call_stack_graph.db")
    
    # Neo4j specific settings
    NEO4J_URI = os.getenv("CODEPECKER_NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USERNAME = os.getenv("CODEPECKER_NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("CODEPECKER_NEO4J_PASSWORD", "password")
    
    # Memgraph specific settings
    MEMGRAPH_HOST = os.getenv("CODEPECKER_MEMGRAPH_HOST", "localhost")
    MEMGRAPH_PORT = int(os.getenv("CODEPECKER_MEMGRAPH_PORT", "7687"))
    
    # ArangoDB specific settings
    ARANGODB_URL = os.getenv("CODEPECKER_ARANGODB_URL", "http://localhost:8529")
    ARANGODB_USERNAME = os.getenv("CODEPECKER_ARANGODB_USER", "root")
    ARANGODB_PASSWORD = os.getenv("CODEPECKER_ARANGODB_PASSWORD", "")
    
    @classmethod
    def get_database_config(cls) -> Dict[str, Any]:
        """Get database configuration based on the selected database type"""
        db_type = cls.DATABASE_TYPE.lower()
        
        if db_type == "sqlite":
            return {"db_path": cls.SQLITE_DB_PATH}
        elif db_type == "neo4j":
            return {
                "uri": cls.NEO4J_URI,
                "username": cls.NEO4J_USERNAME,
                "password": cls.NEO4J_PASSWORD
            }
        elif db_type == "memgraph":
            return {
                "host": cls.MEMGRAPH_HOST,
                "port": cls.MEMGRAPH_PORT
            }
        elif db_type == "arangodb":
            return {
                "url": cls.ARANGODB_URL,
                "username": cls.ARANGODB_USERNAME,
                "password": cls.ARANGODB_PASSWORD
            }
        else:
            raise ValueError(f"Unsupported database type: {db_type}")


# Example usage:
# To switch to Neo4j, set environment variable: CODEPECKER_DB_TYPE=neo4j
# To use custom SQLite path: CODEPECKER_SQLITE_PATH=/custom/path/graph.db
