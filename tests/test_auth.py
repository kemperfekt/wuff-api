#!/usr/bin/env python3
"""Test API authentication on both local and production"""

import requests
import os

# Configuration
LOCAL_URL = "http://localhost:8000"
PROD_URL = "https://dogbot-agent.osc-fr1.scalingo.io"
VALID_API_KEY = os.getenv("WUFFCHAT_API_KEY", "gu5xS5Dy8F4hvDJ0DlahW--QZ5nvkhxVQ2gvhu79pEk")
INVALID_API_KEY = "invalid-key-123"

def test_endpoint_auth(base_url, endpoint, description):
    """Test authentication for a specific endpoint"""
    print(f"\n🔒 Testing {description}")
    print(f"   Endpoint: {base_url}{endpoint}")
    
    # Test 1: No API key
    try:
        response = requests.post(f"{base_url}{endpoint}", timeout=10)
        print(f"   ❌ No API key: Status {response.status_code}")
        if response.status_code == 401:
            print(f"      ✅ Correctly rejected (401 Unauthorized)")
        else:
            print(f"      ⚠️ Expected 401, got {response.status_code}")
    except Exception as e:
        print(f"   ❌ No API key: Error - {str(e)[:50]}...")
    
    # Test 2: Invalid API key
    try:
        headers = {"X-API-Key": INVALID_API_KEY}
        response = requests.post(f"{base_url}{endpoint}", headers=headers, timeout=10)
        print(f"   ❌ Invalid API key: Status {response.status_code}")
        if response.status_code == 401:
            print(f"      ✅ Correctly rejected (401 Unauthorized)")
        else:
            print(f"      ⚠️ Expected 401, got {response.status_code}")
    except Exception as e:
        print(f"   ❌ Invalid API key: Error - {str(e)[:50]}...")
    
    # Test 3: Valid API key
    try:
        headers = {"X-API-Key": VALID_API_KEY}
        response = requests.post(f"{base_url}{endpoint}", headers=headers, timeout=10)
        print(f"   ✅ Valid API key: Status {response.status_code}")
        if response.status_code in [200, 500]:  # 500 might be app logic issues
            print(f"      ✅ Correctly authenticated (passed auth check)")
        elif response.status_code == 401:
            print(f"      ❌ Still rejected - auth may not be working")
        else:
            print(f"      ⚠️ Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Valid API key: Error - {str(e)[:50]}...")

def test_public_endpoints(base_url):
    """Test that public endpoints don't require auth"""
    print(f"\n🌐 Testing public endpoints on {base_url}")
    
    public_endpoints = ["/", "/health", "/healthz", "/alive"]
    
    for endpoint in public_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            print(f"   {endpoint}: Status {response.status_code}")
            if response.status_code == 200:
                print(f"      ✅ Public access working")
            elif response.status_code == 401:
                print(f"      ❌ Incorrectly requires auth")
            else:
                print(f"      ⚠️ Unexpected status")
        except Exception as e:
            print(f"   {endpoint}: Error - {str(e)[:30]}...")

if __name__ == "__main__":
    print("🔐 Testing API Authentication")
    print(f"🔑 Using API Key: {VALID_API_KEY[:8]}...")
    
    # Check if local server is running
    try:
        requests.get(f"{LOCAL_URL}/health", timeout=2)
        local_running = True
    except:
        local_running = False
    
    if local_running:
        print(f"\n{'='*50}")
        print("🏠 LOCAL SERVER TESTS")
        print(f"{'='*50}")
        
        test_public_endpoints(LOCAL_URL)
        test_endpoint_auth(LOCAL_URL, "/flow_intro", "flow_intro endpoint (local)")
        test_endpoint_auth(LOCAL_URL, "/flow_step", "flow_step endpoint (local)")
    else:
        print(f"\n🏠 Local server not running, skipping local tests")
    
    print(f"\n{'='*50}")
    print("🌍 PRODUCTION SERVER TESTS")
    print(f"{'='*50}")
    
    test_public_endpoints(PROD_URL)
    test_endpoint_auth(PROD_URL, "/flow_intro", "flow_intro endpoint (production)")
    test_endpoint_auth(PROD_URL, "/flow_step", "flow_step endpoint (production)")
    
    print(f"\n🎯 Authentication Test Complete!")
    print(f"📋 Summary:")
    print(f"   - Protected endpoints should return 401 without valid API key")
    print(f"   - Protected endpoints should accept requests with valid API key") 
    print(f"   - Public endpoints should work without API key")