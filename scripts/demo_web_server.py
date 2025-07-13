"""
Demo script to test the web server functionality
"""
import sys
import os
import time
import subprocess

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

def check_database_has_data():
    """Check if the database has any data"""
    try:
        from src.database.graph_db_factory import CallStackGraphDB
        from src.core.config import Config
        
        db_config = Config.get_database_config()
        graph_db = CallStackGraphDB(
            db_type=Config.DATABASE_TYPE, 
            clear_db=False,
            **db_config
        )
        
        with graph_db.db.driver.session() as session:
            result = session.run("MATCH (c:Class) RETURN count(c) as count")
            count = result.single()["count"]
            
        graph_db.close()
        return count > 0, count
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return False, 0

def main():
    """Demo the web server functionality"""
    print("🔍 CODEPECKER WEB SERVER DEMO")
    print("=" * 50)
    
    # Check if database has data
    print("📊 Checking database status...")
    has_data, class_count = check_database_has_data()
    
    if not has_data:
        print("❌ No data found in database!")
        print("   Please run the following first:")
        print("   1. python ingestion.py")
        print("   2. python server.py")
        print()
        print("   This will populate the database and start the web server.")
        return
    
    print(f"✅ Database contains {class_count} classes")
    print()
    
    print("🚀 Starting web server...")
    print("   Server will be available at: http://localhost:5000")
    print("   Press Ctrl+C to stop the server")
    print()
    
    # Start the server
    try:
        import subprocess
        subprocess.run([sys.executable, "server.py"])
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

if __name__ == '__main__':
    main()
