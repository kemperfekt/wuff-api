#!/usr/bin/env python
"""Test script for API authentication"""

import requests
import os

# Test configuration
API_URL = "http://localhost:8000"
API_KEY = os.getenv("WUFFCHAT_API_KEY", "test-key-123")

print("🔐 Testing API Authentication")
print(f"📍 API URL: {API_URL}")
print(f"🔑 API Key: {API_KEY[:8]}...")

# Test 1: Health check (no auth required)
print("\n1️⃣ Testing health check (no auth)...")
response = requests.get(f"{API_URL}/")
print(f"   Status: {response.status_code}")
print(f"   Response: {response.json()}")

# Test 2: Protected endpoint without API key
print("\n2️⃣ Testing protected endpoint without API key...")
response = requests.post(f"{API_URL}/flow_intro")
print(f"   Status: {response.status_code}")
if response.status_code == 401:
    print(f"   ✅ Correctly rejected: {response.json()['detail']}")
else:
    print(f"   ❌ Should have been rejected!")

# Test 3: Protected endpoint with wrong API key
print("\n3️⃣ Testing protected endpoint with wrong API key...")
headers = {"X-API-Key": "wrong-key"}
response = requests.post(f"{API_URL}/flow_intro", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 401:
    print(f"   ✅ Correctly rejected: {response.json()['detail']}")
else:
    print(f"   ❌ Should have been rejected!")

# Test 4: Protected endpoint with correct API key
print("\n4️⃣ Testing protected endpoint with correct API key...")
headers = {"X-API-Key": API_KEY}
response = requests.post(f"{API_URL}/flow_intro", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    print(f"   ✅ Success! Session ID: {response.json()['session_id']}")
else:
    print(f"   ❌ Failed: {response.text}")

print("\n✅ API Authentication test complete!")