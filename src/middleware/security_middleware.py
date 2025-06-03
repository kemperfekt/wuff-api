"""
Security middleware for WuffChat API
Handles rate limiting, request validation, and security headers
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
import time
import logging
from typing import Callable
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class SecurityMiddleware:
    """Comprehensive security middleware"""
    
    def __init__(self):
        self.blocked_ips = set()
        self.suspicious_patterns = [
            "../",  # Path traversal
            "<script",  # XSS attempts
            "SELECT",  # SQL injection
            "UNION",  # SQL injection
            "${",  # Template injection
            "{{",  # Template injection
        ]
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        # 1. Check if IP is blocked
        client_ip = request.headers.get("X-Forwarded-For", 
                                       request.headers.get("X-Real-IP", 
                                       request.client.host))
        
        if client_ip in self.blocked_ips:
            logger.warning(f"🚫 Blocked IP attempted access: {client_ip}")
            return JSONResponse(
                status_code=403,
                content={"detail": "Access denied"}
            )
        
        # 2. Check for suspicious patterns in request
        if await self._contains_suspicious_content(request):
            logger.warning(f"⚠️ Suspicious request from {client_ip}: {request.url}")
            # Don't block immediately, but log for analysis
            
        # 3. Add security headers to response
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log slow requests
        if process_time > 1.0:
            logger.warning(f"⏱️ Slow request: {request.url.path} took {process_time:.2f}s")
        
        return response
    
    async def _contains_suspicious_content(self, request: Request) -> bool:
        """Check if request contains suspicious patterns"""
        # Check URL
        url_str = str(request.url)
        for pattern in self.suspicious_patterns:
            if pattern.lower() in url_str.lower():
                return True
        
        # Check body for POST requests
        if request.method == "POST":
            try:
                body = await request.body()
                body_str = body.decode("utf-8")
                for pattern in self.suspicious_patterns:
                    if pattern.lower() in body_str.lower():
                        return True
            except:
                pass  # If we can't read body, skip check
        
        return False


class RateLimitMonitor:
    """Monitor and log rate limit violations"""
    
    def __init__(self):
        self.violations = {}  # IP -> violation count
        self.violation_threshold = 10  # Block after 10 violations
    
    def record_violation(self, ip: str):
        """Record a rate limit violation"""
        self.violations[ip] = self.violations.get(ip, 0) + 1
        
        logger.warning(f"🚦 Rate limit violation #{self.violations[ip]} from {ip}")
        
        if self.violations[ip] >= self.violation_threshold:
            logger.error(f"🚫 IP {ip} exceeded violation threshold - consider blocking")
            # In production, you might want to automatically block the IP
            return True
        return False
    
    def get_violation_stats(self) -> dict:
        """Get statistics about rate limit violations"""
        return {
            "total_violators": len(self.violations),
            "total_violations": sum(self.violations.values()),
            "top_violators": sorted(
                self.violations.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]
        }


class RequestLogger:
    """Enhanced request logging with security focus"""
    
    def __init__(self):
        self.request_counts = {}  # IP -> count
        self.start_time = time.time()
    
    async def log_request(self, request: Request):
        """Log request with security-relevant information"""
        client_ip = request.headers.get("X-Forwarded-For", 
                                       request.headers.get("X-Real-IP", 
                                       request.client.host))
        
        # Count requests per IP
        self.request_counts[client_ip] = self.request_counts.get(client_ip, 0) + 1
        
        # Log suspicious activity
        if self.request_counts[client_ip] > 1000:
            logger.warning(f"🔍 High volume from {client_ip}: {self.request_counts[client_ip]} requests")
        
        # Log API key usage
        api_key = request.headers.get("X-API-Key", "")
        if api_key:
            logger.info(f"🔑 API request from {client_ip} with key {api_key[:8]}...")
        else:
            logger.warning(f"🔓 Unauthenticated request from {client_ip} to {request.url.path}")
    
    def get_stats(self) -> dict:
        """Get request statistics"""
        uptime = time.time() - self.start_time
        total_requests = sum(self.request_counts.values())
        
        return {
            "uptime_seconds": uptime,
            "total_requests": total_requests,
            "unique_ips": len(self.request_counts),
            "requests_per_second": total_requests / uptime if uptime > 0 else 0,
            "top_requesters": sorted(
                self.request_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }