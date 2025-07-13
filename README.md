# Codebase Analyzer - Data Ingestion Tool

A modular data ingestion tool that uses LLM to identify entry points, tree-sitter to parse code, and graph databases to store static call stack analysis.

## Features

- 🧠 **LLM Integration**: Uses GPT-4o to identify entry points from project structure
- 🌳 **Tree-sitter Parsing**: Extracts classes, methods, and visibility from C# files
- 📊 **Graph Database**: Stores hierarchical call stack data with switchable backends
- 🏗️ **Modular Architecture**: Factory pattern for easy database switching
- 📁 **Directory Scanning**: Respects `.gitignore` files and generates clean tree output

## Project Structure

```
├── ingestion.py               # Data ingestion entry point
├── server.py                  # Web server and API
├── requirements.txt           # Python dependencies
├── web/                      # Web interface
│   ├── templates/            # HTML templates
│   │   └── index.html        # Main dashboard
│   └── static/               # Static assets (CSS, JS)
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

### 🚀 **One-Command Demo**
```bash
python demo.py
```
This will guide you through the complete workflow: data ingestion → web server → browser interface.

### 📋 **Manual Setup**

1. **Install Dependencies**:
1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**:
2. **Set Environment Variables**:
   Create a `.env` file with your database configuration:
   ```env
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your_password
   ```

3. **Configure Target Project** in `ingestion.py`:
   ```python
   project_path = "path/to/your/csharp/project"
   ```

4. **Run Analysis**:
   ```bash
   python ingestion.py
   ```

5. **Start Web Server**:
   ```bash
   python server.py
   ```

6. **Open Browser**: Navigate to `http://localhost:5000`

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

## Web Server & API

After running the data ingestion, you can start a web server to explore the data:

```bash
python server.py
```

This starts a Flask web server at `http://localhost:5000` with:

### 🌐 **Web Interface**
- **Interactive Dashboard**: View all classes and their methods
- **Class Selection**: Click on any class to see its detailed graph
- **Statistics**: Overview of total classes, methods, and method calls
- **Responsive Design**: Works on desktop and mobile

### 📡 **REST API Endpoints**
- `GET /api/health` - Health check and database status
- `GET /api/classes` - List all classes (entry points)
- `GET /api/class/<name>/graph` - Get detailed graph for a specific class
- `GET /api/graph/full` - Get complete graph data
- `GET /api/stats` - Database statistics

### 🚀 **Usage Workflow**
1. Run `python ingestion.py` to populate the database
2. Start `python server.py` to launch the web interface
3. Open `http://localhost:5000` in your browser
4. Explore your codebase interactively!

## Dependencies

- `pathspec` - For .gitignore file parsing
- `openai` - For LLM integration
- `httpx` - HTTP client with proxy support
- `requests` - For authentication requests
- `neo4j` - Neo4j graph database driver
- `python-dotenv` - Environment variable management
- `flask` - Web server framework
- `flask-cors` - Cross-origin resource sharing
