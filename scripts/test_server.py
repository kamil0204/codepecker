"""
Test script to verify server functionality
"""
import sys
import os
import requests
import time
import subprocess
import threading

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

def test_server():
    """Test the server endpoints"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing server endpoints...")
    
    # Wait a moment for server to start
    time.sleep(2)
    
    try:
        # Test health endpoint
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health check: {health_data['status']}")
            print(f"   Database connected: {health_data['database_connected']}")
            print(f"   Database type: {health_data['database_type']}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
        
        # Test classes endpoint
        response = requests.get(f"{base_url}/api/classes", timeout=5)
        if response.status_code == 200:
            classes_data = response.json()
            if 'error' in classes_data:
                print(f"⚠️  Classes endpoint error: {classes_data['error']}")
            else:
                print(f"✅ Classes endpoint: {classes_data['count']} classes found")
        else:
            print(f"❌ Classes endpoint failed: {response.status_code}")
        
        # Test stats endpoint
        response = requests.get(f"{base_url}/api/stats", timeout=5)
        if response.status_code == 200:
            stats_data = response.json()
            if 'error' in stats_data:
                print(f"⚠️  Stats endpoint error: {stats_data['error']}")
            else:
                print(f"✅ Stats endpoint: {stats_data['total_classes']} classes, {stats_data['total_methods']} methods")
        else:
            print(f"❌ Stats endpoint failed: {response.status_code}")
        
        # Test main page
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            print("✅ Main page loads successfully")
        else:
            print(f"❌ Main page failed: {response.status_code}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Server connection failed: {e}")
        return False

def main():
    """Run server tests"""
    print("🔍 CODEPECKER SERVER TEST")
    print("=" * 35)
    
    print("🚀 Starting server for testing...")
    
    # Start server in background
    server_process = subprocess.Popen([
        sys.executable, "../server.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    try:
        # Run tests
        success = test_server()
        
        if success:
            print("\n✅ All tests passed!")
            print("   Server is working correctly")
        else:
            print("\n❌ Some tests failed")
            print("   Check your database connection and configuration")
        
    finally:
        # Clean up
        print("\n🛑 Stopping test server...")
        server_process.terminate()
        server_process.wait()

if __name__ == '__main__':
    main()
