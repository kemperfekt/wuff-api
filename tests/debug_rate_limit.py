#!/usr/bin/env python3
"""Debug script to test rate limiting configuration"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.rate_limit_config import RATE_LIMIT_TIERS, get_real_ip
from slowapi import Limiter
from fastapi import FastAPI, Request
from slowapi.errors import RateLimitExceeded

def test_limiter_config():
    """Test if limiter configuration is correct"""
    print("🔍 Testing Rate Limiter Configuration")
    print("=" * 50)
    
    # Check rate limits
    limits = RATE_LIMIT_TIERS["default"]
    print(f"📊 Rate Limits: {limits}")
    
    # Create limiter
    limiter = Limiter(key_func=get_real_ip)
    print(f"✅ Limiter created: {limiter}")
    
    # Create test app
    app = FastAPI()
    app.state.limiter = limiter
    
    # Add rate limit handler
    def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return {"error": "Rate limited"}
    
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
    
    # Test endpoint
    @app.get("/test")
    @limiter.limit("2/minute")  # Simple test limit
    async def test_endpoint(request: Request):
        return {"status": "ok"}
    
    print("✅ Test app configured with rate limiting")
    
    # Test IP extraction
    class MockRequest:
        def __init__(self, ip="127.0.0.1"):
            self.client = type('obj', (object,), {'host': ip})
            self.headers = {}
    
    req = MockRequest()
    ip = get_real_ip(req)
    print(f"🌐 IP extraction test: {ip}")
    
    print("\n📝 Summary:")
    print(f"   - Limiter: {'✅ OK' if limiter else '❌ FAIL'}")
    print(f"   - Rate limits: {'✅ OK' if limits else '❌ FAIL'}")
    print(f"   - IP extraction: {'✅ OK' if ip else '❌ FAIL'}")

if __name__ == "__main__":
    test_limiter_config()