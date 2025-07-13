"""
Quick start script for CodePecker
"""
import sys
import os
import subprocess

def run_command(command, description):
    """Run a command and show progress"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error during {description}: {e}")
        return False

def check_requirements():
    """Check if all requirements are met"""
    print("🔍 Checking requirements...")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        print("   Please create a .env file with your Neo4j credentials:")
        print("   NEO4J_URI=bolt://localhost:7687")
        print("   NEO4J_USERNAME=neo4j")
        print("   NEO4J_PASSWORD=your_password")
        return False
    
    print("✅ .env file found")
    
    # Check if Neo4j is accessible (basic check)
    try:
        from src.core.config import Config
        print(f"✅ Configuration loaded (DB type: {Config.DATABASE_TYPE})")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False
    
    return True

def main():
    """Quick start workflow"""
    print("🚀 CODEPECKER QUICK START")
    print("=" * 40)
    
    # Check requirements
    if not check_requirements():
        return
    
    print("\n📋 Quick Start Options:")
    print("1. Run full workflow (ingestion + web server)")
    print("2. Run ingestion only")
    print("3. Run web server only")
    print("4. Exit")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        print("\n🔄 Running full workflow...")
        
        # Run ingestion
        if run_command("python ingestion.py", "Data ingestion"):
            print("\n🌐 Starting web server...")
            print("   Web interface will be available at: http://localhost:5000")
            print("   Press Ctrl+C to stop")
            subprocess.run([sys.executable, "server.py"])
        
    elif choice == "2":
        print("\n🔄 Running data ingestion only...")
        run_command("python ingestion.py", "Data ingestion")
        
    elif choice == "3":
        print("\n🌐 Starting web server...")
        print("   Web interface will be available at: http://localhost:5000")
        print("   Press Ctrl+C to stop")
        subprocess.run([sys.executable, "server.py"])
        
    elif choice == "4":
        print("👋 Goodbye!")
        
    else:
        print("❌ Invalid choice")

if __name__ == '__main__':
    main()
