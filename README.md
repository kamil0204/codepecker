# Codebase Analyzer

A modular tool that uses LLM to identify entry points, tree-sitter to parse code, and graph databases to store static call stack analysis.

## Features

- 🧠 **LLM Integration**: Uses GPT-4o to identify entry points from project structure
- 🌳 **Tree-sitter Parsing**: Extracts classes, methods, and visibility from C# files
- 📊 **Graph Database**: Stores hierarchical call stack data with switchable backends
- 🏗️ **Modular Architecture**: Factory pattern for easy database switching
- 📁 **Directory Scanning**: Respects `.gitignore` files and generates clean tree output

## Project Structure

```
├── app.py                     # Main application entry point
├── requirements.txt           # Python dependencies
├── src/                      # Source code modules
│   ├── core/                 # Core configuration
│   │   └── config.py         # Environment-based settings
│   ├── database/             # Graph database implementations
│   │   ├── graph_db_interface.py      # Abstract interface
│   │   ├── sqlite_graph_db.py         # SQLite implementation
│   │   ├── graph_db_factory.py        # Factory pattern
│   │   └── future_graph_dbs.py        # Example implementations
│   ├── llm/                  # LLM integration
│   │   └── llm_client.py     # OpenAI API client
│   ├── parsers/              # Code parsing modules
│   │   ├── base_parser.py    # Abstract parser interface
│   │   ├── csharp_parser.py  # C# tree-sitter implementation
│   │   └── parser_manager.py # Multi-language coordinator
│   └── utils/                # Utility functions
│       └── directory_scanner.py # Directory traversal
├── scripts/                  # Development and demo scripts
│   ├── debug_parser.py       # Parser debugging
│   ├── demo_db_switching.py  # Database switching demo
│   └── verify_db.py          # Database verification
└── docs/                     # Documentation
    ├── GRAPH_DB_README.md    # Database architecture guide
    └── codebase_review_plan.md # Analysis planning
```

## Quick Start

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**:
   Create a `.env` file with your database configuration:
   ```env
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your_password
   ```

3. **Configure Target Project** in `app.py`:
   ```python
   project_path = "path/to/your/csharp/project"
   ```

4. **Run Analysis**:
   ```bash
   python app.py
   ```

## Database Switching

The tool supports multiple graph database backends through a factory pattern:

```python
# Use Neo4j (default)
db = CallStackGraphDB(db_type="neo4j", uri="bolt://localhost:7687", 
                     username="neo4j", password="your_password")

# Use SQLite (alternative)
db = CallStackGraphDB(db_type="sqlite", db_path="my_graph.db")
```

## Output Format

The tool generates a hierarchical call stack showing:
- **Classes** with file paths and visibility
- **Methods** nested under their containing classes
- **Visibility modifiers** (Public, Private, Protected, Internal)

Example output:
```
CompanyController (Type:Class, Visibility:Public)
    |____> GetAllCompanyNameAsync (Type:Method, Visibility:Public)
    |____> GetCompaniesAsync (Type:Method, Visibility:Public)
```
   ```bash
   python app.py
   ```

## Dependencies

- `pathspec` - For .gitignore file parsing
- `openai` - For LLM integration
- `httpx` - HTTP client with proxy support
- `requests` - For authentication requests
- `neo4j` - Neo4j graph database driver
- `python-dotenv` - Environment variable management
