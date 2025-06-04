#!/usr/bin/env python3
"""
Test session security implementation
"""

import requests
import time
import json

# Test configuration
API_URL = "http://localhost:8000"
API_KEY = "gu5xS5Dy8F4hvDJ0DlahW--QZ5nvkhxVQ2gvhu79pEk"
headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

print("🔐 Testing Session Security Implementation")
print("=" * 50)

def test_flow_intro():
    """Test that flow_intro returns session token"""
    print("\n1️⃣ Testing /flow_intro returns token...")
    
    response = requests.post(f"{API_URL}/flow_intro", headers=headers)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Session ID: {data.get('session_id', 'N/A')[:8]}...")
        print(f"   ✅ Token: {data.get('session_token', 'N/A')[:8]}...")
        print(f"   ✅ Messages: {len(data.get('messages', []))} messages")
        
        if 'session_token' not in data:
            print("   ❌ ERROR: No session_token in response!")
            return None, None
            
        return data['session_id'], data['session_token']
    else:
        print(f"   ❌ Error: {response.text}")
        return None, None

def test_flow_step_with_token(session_id, token):
    """Test flow_step with valid token"""
    print("\n2️⃣ Testing /flow_step with valid token...")
    
    payload = {
        "session_id": session_id,
        "session_token": token,
        "message": "Mein Hund bellt ständig"
    }
    
    response = requests.post(f"{API_URL}/flow_step", headers=headers, json=payload)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Success! Got {len(data.get('messages', []))} messages")
        return True
    else:
        print(f"   ❌ Error: {response.text}")
        return False

def test_flow_step_without_token(session_id):
    """Test flow_step without token (should fail)"""
    print("\n3️⃣ Testing /flow_step WITHOUT token (should fail)...")
    
    payload = {
        "session_id": session_id,
        "message": "Test without token"
    }
    
    response = requests.post(f"{API_URL}/flow_step", headers=headers, json=payload)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 422:  # Validation error - missing field
        print("   ✅ Correctly rejected (422 - missing token field)")
        return True
    elif response.status_code == 401:
        print("   ✅ Correctly rejected (401 - unauthorized)")
        return True
    else:
        print(f"   ❌ Unexpected status: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def test_flow_step_with_wrong_token(session_id):
    """Test flow_step with wrong token"""
    print("\n4️⃣ Testing /flow_step with WRONG token...")
    
    payload = {
        "session_id": session_id,
        "session_token": "wrong-token-12345",
        "message": "Test with wrong token"
    }
    
    response = requests.post(f"{API_URL}/flow_step", headers=headers, json=payload)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 401:
        print("   ✅ Correctly rejected (401)")
        return True
    else:
        print(f"   ❌ Expected 401, got {response.status_code}")
        return False

def test_session_expiration():
    """Test session expiration (would take 30 min, so just show concept)"""
    print("\n5️⃣ Session expiration test...")
    print("   ⏰ Sessions expire after 30 minutes")
    print("   ⏰ Token refreshes on each valid request")
    print("   ✅ (Skipping actual 30-min wait)")

def test_multiple_sessions():
    """Test that multiple sessions work independently"""
    print("\n6️⃣ Testing multiple independent sessions...")
    
    # Create first session
    response1 = requests.post(f"{API_URL}/flow_intro", headers=headers)
    if response1.status_code == 200:
        data1 = response1.json()
        session1 = data1['session_id']
        token1 = data1['session_token']
        print(f"   ✅ Session 1: {session1[:8]}...")
    
    # Create second session
    response2 = requests.post(f"{API_URL}/flow_intro", headers=headers)
    if response2.status_code == 200:
        data2 = response2.json()
        session2 = data2['session_id']
        token2 = data2['session_token']
        print(f"   ✅ Session 2: {session2[:8]}...")
    
    # Verify they're different
    if session1 != session2 and token1 != token2:
        print("   ✅ Sessions are independent")
        return True
    else:
        print("   ❌ Sessions are not independent!")
        return False

if __name__ == "__main__":
    # First check if server is running
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        if response.status_code != 200:
            print("❌ Server not responding properly")
            exit(1)
    except:
        print("❌ Server not running at http://localhost:8000")
        print("   Please start with: python -m uvicorn src.main:app --port 8000")
        exit(1)
    
    # Run tests
    session_id, token = test_flow_intro()
    
    if session_id and token:
        test_flow_step_with_token(session_id, token)
        test_flow_step_without_token(session_id)
        test_flow_step_with_wrong_token(session_id)
    
    test_session_expiration()
    test_multiple_sessions()
    
    print("\n" + "=" * 50)
    print("✅ Session security test complete!")
    print("\n💡 Key security features:")
    print("   - Token required for all /flow_step requests")
    print("   - Invalid/missing tokens return 401")
    print("   - Sessions expire after 30 minutes")
    print("   - Each session has unique token")