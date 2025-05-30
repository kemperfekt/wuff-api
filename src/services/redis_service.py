# src/v2/services/redis_service.py
"""
V2 Redis Service - Simple version that works without Redis.
"""

import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class RedisService:
    """
    Simple Redis service that uses in-memory storage.
    
    This allows V2 to run without Redis for local testing.
    """
    
    def __init__(self):
        """Initialize with in-memory storage."""
        self.logger = logger
        self.storage = {}
        logger.info("V2 RedisService: Using in-memory storage (Redis not required)")
    
    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Store a value."""
        self.storage[key] = value
        return True
    
    def get(self, key: str, as_json: bool = True) -> Any:
        """Retrieve a value."""
        return self.storage.get(key)
    
    def delete(self, key: str) -> bool:
        """Delete a key."""
        if key in self.storage:
            del self.storage[key]
            return True
        return False
    
    def keys(self, pattern: str = "*") -> List[str]:
        """Get all keys."""
        return list(self.storage.keys())
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health."""
        return {
            "healthy": True,
            "service": "redis",
            "type": "in-memory",
            "message": "Using in-memory storage for local testing"
        }