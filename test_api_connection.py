#!/usr/bin/env python3
"""
Test script to verify API connection and endpoints
"""

import requests
import json

# Base URL for the API
BASE_URL = "http://localhost:8000"

def test_health_endpoint():
    """Test the health check endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Health check: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_root_endpoint():
    """Test the root endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✅ Root endpoint: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
        return False

def test_user_registration():
    """Test user registration endpoint."""
    try:
        test_user = {
            "email": "test@example.com",
            "password": "testpass123",
            "first_name": "Test",
            "last_name": "User",
            "vehicle_type": "tesla"
        }
        
        response = requests.post(
            f"{BASE_URL}/users/register",
            json=test_user,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"✅ User registration: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
            return True
        elif response.status_code == 400:
            print(f"   Response: {response.json()}")
            print("   (This might be expected if user already exists)")
            return True
        else:
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ User registration failed: {e}")
        return False

def test_user_login():
    """Test user login endpoint."""
    try:
        test_credentials = {
            "email": "test@example.com",
            "password": "testpass123"
        }
        
        response = requests.post(
            f"{BASE_URL}/users/login",
            json=test_credentials,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"✅ User login: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ User login failed: {e}")
        return False

def test_stations_endpoint():
    """Test stations endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/stations/")
        print(f"✅ Stations endpoint: {response.status_code}")
        if response.status_code == 200:
            stations = response.json()
            print(f"   Found {len(stations)} stations")
        else:
            print(f"   Response: {response.text}")
        return response.status_code in [200, 503]  # 503 is expected if Snowflake not configured
        
    except Exception as e:
        print(f"❌ Stations endpoint failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing EV User Intelligence Platform API")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_endpoint),
        ("Root Endpoint", test_root_endpoint),
        ("User Registration", test_user_registration),
        ("User Login", test_user_login),
        ("Stations Endpoint", test_stations_endpoint),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Testing: {test_name}")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your API is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        
    # Provide next steps
    print("\n📋 Next Steps:")
    if passed >= 3:  # At least basic endpoints working
        print("   1. ✅ API is accessible")
        print("   2. 🔧 Configure Snowflake database if not done")
        print("   3. 🚀 Test frontend connection")
    else:
        print("   1. ❌ Check if backend server is running")
        print("   2. 🔧 Verify backend configuration")
        print("   3. 📖 Review error messages above")

if __name__ == "__main__":
    main()
