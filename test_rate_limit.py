#!/usr/bin/env python
"""Test script for rate limiting"""

import requests
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Test configuration
API_URL = "http://localhost:8000"
API_KEY = os.getenv("WUFFCHAT_API_KEY", "gu5xS5Dy8F4hvDJ0DlahW--QZ5nvkhxVQ2gvhu79pEk")

print("🚦 Testing Rate Limiting")
print(f"📍 API URL: {API_URL}")
print(f"🔑 API Key: {API_KEY[:8]}...")

headers = {"X-API-Key": API_KEY}

# Test 1: Single requests within limit
print("\n1️⃣ Testing single requests (should succeed)...")
for i in range(3):
    response = requests.post(f"{API_URL}/flow_intro", headers=headers)
    print(f"   Request {i+1}: Status {response.status_code}")
    if response.status_code == 200:
        print(f"   ✅ Success! Rate limit headers:")
        print(f"      Limit: {response.headers.get('X-RateLimit-Limit', 'N/A')}")
        print(f"      Remaining: {response.headers.get('X-RateLimit-Remaining', 'N/A')}")
    time.sleep(1)

# Test 2: Exceed rate limit
print("\n2️⃣ Testing rate limit (10 requests/minute for flow_intro)...")
print("   Sending 12 rapid requests...")

def make_request(i):
    response = requests.post(f"{API_URL}/flow_intro", headers=headers)
    return i, response.status_code, response.headers.get('X-RateLimit-Remaining', 'N/A')

with ThreadPoolExecutor(max_workers=12) as executor:
    futures = [executor.submit(make_request, i) for i in range(12)]
    
    success_count = 0
    rate_limited_count = 0
    
    for future in as_completed(futures):
        i, status, remaining = future.result()
        if status == 200:
            success_count += 1
            print(f"   ✅ Request {i+1}: Success (Remaining: {remaining})")
        elif status == 429:
            rate_limited_count += 1
            print(f"   🚫 Request {i+1}: Rate limited!")
        else:
            print(f"   ❌ Request {i+1}: Error {status}")

print(f"\n   Summary: {success_count} succeeded, {rate_limited_count} rate limited")

# Test 3: Different endpoint limits
print("\n3️⃣ Testing different endpoint limits...")
print("   flow_intro: 10/minute")
print("   flow_step: 30/minute")

# Create a session first
response = requests.post(f"{API_URL}/flow_intro", headers=headers)
if response.status_code == 200:
    session_id = response.json()["session_id"]
    print(f"   Got session: {session_id}")
    
    # Test flow_step rate limit (30/minute)
    print("\n   Testing flow_step endpoint...")
    for i in range(5):
        body = {"session_id": session_id, "message": f"Test message {i+1}"}
        response = requests.post(f"{API_URL}/flow_step", headers=headers, json=body)
        print(f"   Request {i+1}: Status {response.status_code}, Remaining: {response.headers.get('X-RateLimit-Remaining', 'N/A')}")

# Test 4: Rate limit recovery
print("\n4️⃣ Testing rate limit recovery...")
print("   Waiting 60 seconds for rate limit reset...")
print("   (In production, use exponential backoff instead)")

# Show countdown
for i in range(60, 0, -10):
    print(f"   ⏱️  {i} seconds remaining...")
    time.sleep(10)

print("   Testing after reset...")
response = requests.post(f"{API_URL}/flow_intro", headers=headers)
if response.status_code == 200:
    print(f"   ✅ Rate limit reset! Remaining: {response.headers.get('X-RateLimit-Remaining', 'N/A')}")
else:
    print(f"   ❌ Still limited? Status: {response.status_code}")

print("\n✅ Rate limiting test complete!")
print("\n💡 Tips:")
print("   - Rate limits are per IP address")
print("   - Use X-RateLimit headers to track usage")
print("   - Implement exponential backoff for 429 responses")
print("   - Consider caching to reduce API calls")