"""
Rate limiting configuration for WuffChat API
"""

from typing import Dict, Callable
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address
import os

def get_real_ip(request: Request) -> str:
    """
    Get the real IP address, considering proxy headers.
    Important for Scalingo/Heroku deployments behind load balancers.
    """
    # Check for proxy headers (in order of preference)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, take the first
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct connection IP
    return get_remote_address(request)

def create_custom_key_func(prefix: str = "") -> Callable:
    """
    Create a custom key function that includes API key for better rate limiting.
    This allows different rate limits for different API keys if needed.
    """
    def key_func(request: Request) -> str:
        # Get IP address
        ip = get_real_ip(request)
        
        # Optionally include API key for per-key limits
        api_key = request.headers.get("X-API-Key", "no-key")
        
        # In development, also consider API key to avoid limiting yourself
        if os.getenv("ENV") == "development":
            return f"{prefix}:{api_key}:{ip}"
        
        # In production, limit by IP only
        return f"{prefix}:{ip}"
    
    return key_func

# Rate limit configurations for different user types
RATE_LIMIT_TIERS = {
    "default": {
        "flow_intro": "10/minute",      # New conversations
        "flow_step": "30/minute",       # Messages
        "global": "100/minute"          # Overall API calls
    },
    "premium": {  # Future: For authenticated premium users
        "flow_intro": "20/minute",
        "flow_step": "60/minute",
        "global": "200/minute"
    },
    "trusted": {  # Future: For trusted partners
        "flow_intro": "50/minute",
        "flow_step": "150/minute",
        "global": "500/minute"
    }
}

# Cost-based rate limits (prevent expensive operations)
COST_BASED_LIMITS = {
    "gpt_requests": "50/hour",          # Limit GPT API calls
    "weaviate_searches": "100/hour",    # Limit vector searches
    "session_creates": "20/hour"        # Limit new sessions per IP
}

# Burst handling configuration
BURST_CONFIG = {
    "enabled": True,
    "burst_multiplier": 1.5,  # Allow 50% more requests in short bursts
    "burst_window": "10 seconds"
}

# Custom error messages
RATE_LIMIT_MESSAGES = {
    "default": "Zu viele Anfragen. Bitte warte einen Moment und versuche es erneut.",
    "flow_intro": "Zu viele neue Gespräche gestartet. Bitte warte eine Minute.",
    "flow_step": "Zu viele Nachrichten gesendet. Bitte verlangsame etwas.",
    "expensive": "Diese Operation ist begrenzt. Bitte versuche es später erneut."
}

def get_rate_limit_message(endpoint: str) -> str:
    """Get custom error message for rate limited endpoint"""
    return RATE_LIMIT_MESSAGES.get(endpoint, RATE_LIMIT_MESSAGES["default"])

# Advanced rate limiting patterns
class AdaptiveRateLimiter:
    """
    Adaptive rate limiter that adjusts limits based on system load.
    Future enhancement for production scaling.
    """
    def __init__(self):
        self.current_load = 0.0
        self.base_limits = RATE_LIMIT_TIERS["default"].copy()
    
    def get_adjusted_limit(self, endpoint: str) -> str:
        """Adjust rate limit based on current system load"""
        base_limit = self.base_limits.get(endpoint, "100/minute")
        
        # Parse limit
        count, period = base_limit.split("/")
        count = int(count)
        
        # Adjust based on load (reduce limits when load is high)
        if self.current_load > 0.8:
            count = int(count * 0.5)  # Half the limit under high load
        elif self.current_load > 0.6:
            count = int(count * 0.75)  # 75% of limit under medium load
        
        return f"{count}/{period}"
    
    def update_load(self, cpu_percent: float, memory_percent: float):
        """Update current load metrics"""
        self.current_load = max(cpu_percent, memory_percent) / 100.0