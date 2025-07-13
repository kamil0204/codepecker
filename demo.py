"""
Complete demo of CodePecker web functionality
Shows the full workflow from ingestion to web interface
"""
import sys
import os
import subprocess
import time
import webbrowser

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"🔍 {title}")
    print("=" * 60)

def print_step(step_num, title, description=""):
    """Print a formatted step"""
    print(f"\n📍 Step {step_num}: {title}")
    if description:
        print(f"   {description}")

def run_with_feedback(command, description, timeout=30):
    """Run a command with user feedback"""
    print(f"🔄 {description}...")
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate(timeout=timeout)
        
        if process.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True, stdout
        else:
            print(f"❌ {description} failed:")
            print(stderr)
            return False, stderr
    except subprocess.TimeoutExpired:
        process.kill()
        print(f"⏰ {description} timed out after {timeout} seconds")
        return False, "Timeout"
    except Exception as e:
        print(f"❌ Error during {description}: {e}")
        return False, str(e)

def check_database():
    """Check if database has data"""
    try:
        sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
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
        return False, str(e)

def main():
    """Run complete demo"""
    print_header("CODEPECKER COMPLETE DEMO")
    
    print("🎯 This demo will show you the complete CodePecker workflow:")
    print("   1. Check prerequisites")
    print("   2. Run data ingestion (if needed)")
    print("   3. Start web server")
    print("   4. Open web interface")
    print("   5. Test API endpoints")
    
    input("\nPress Enter to continue...")
    
    # Step 1: Check prerequisites
    print_step(1, "Checking Prerequisites")
    
    # Check .env file
    if os.path.exists('.env'):
        print("✅ .env file found")
    else:
        print("❌ .env file not found")
        print("   Please create a .env file with:")
        print("   NEO4J_URI=bolt://localhost:7687")
        print("   NEO4J_USERNAME=neo4j")
        print("   NEO4J_PASSWORD=your_password")
        return
    
    # Check database
    print("🔍 Checking database connection...")
    has_data, result = check_database()
    
    if isinstance(result, str):  # Error occurred
        print(f"❌ Database connection failed: {result}")
        print("   Please ensure Neo4j is running and credentials are correct")
        return
    
    if has_data:
        print(f"✅ Database contains {result} classes")
        run_ingestion = False
    else:
        print("⚠️  Database is empty")
        response = input("   Would you like to run data ingestion? (y/n): ").lower()
        run_ingestion = response.startswith('y')
    
    # Step 2: Run ingestion if needed
    if run_ingestion:
        print_step(2, "Running Data Ingestion", "This may take a few minutes...")
        
        success, output = run_with_feedback(
            "python ingestion.py", 
            "Data ingestion", 
            timeout=120
        )
        
        if not success:
            print("❌ Ingestion failed. Cannot proceed with demo.")
            return
        
        # Verify data was created
        has_data, count = check_database()
        if has_data:
            print(f"✅ Ingestion completed! Created {count} classes in database")
        else:
            print("⚠️  Ingestion completed but no data found")
    else:
        print_step(2, "Skipping Data Ingestion", "Using existing database data")
    
    # Step 3: Start web server
    print_step(3, "Starting Web Server", "Server will start at http://localhost:8000")
    
    print("🚀 Starting server...")
    print("   The web interface will open automatically")
    print("   Press Ctrl+C in this terminal to stop the server")
    print()
    
    # Wait a moment then open browser
    def open_browser():
        time.sleep(3)  # Give server time to start
        try:
            webbrowser.open('http://localhost:8000')
            print("🌐 Web browser opened to http://localhost:8000")
        except Exception as e:
            print(f"⚠️  Could not open browser automatically: {e}")
            print("   Please manually open http://localhost:8000")
    
    import threading
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Start server (this will block until Ctrl+C)
    try:
        subprocess.run([sys.executable, "server.py"])
    except KeyboardInterrupt:
        print("\n\n👋 Demo completed! Server stopped by user.")
    except Exception as e:
        print(f"\n❌ Server error: {e}")

if __name__ == '__main__':
    main()
