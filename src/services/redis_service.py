# src/v2/services/redis_service.py
"""
Redis Service for WuffChat V2.

Clean, async-only wrapper around Redis with:
- Flexible configuration for multiple Redis providers
- Automatic JSON serialization/deserialization
- TTL support
- Proper error handling
- Health checks
"""
import os
import json
import redis.asyncio as redis
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass
import logging

from src.core.service_base import BaseService, ServiceConfig
from src.core.exceptions import (
    RedisServiceError,
    ConfigurationError,
    ValidationError
)

logger = logging.getLogger(__name__)


@dataclass
class RedisConfig(ServiceConfig):
    """Configuration for Redis Service"""
    url: Optional[str] = None
    decode_responses: bool = True
    socket_timeout: float = 5.0
    max_connections: int = 10
    retry_on_timeout: bool = True
    health_check_interval: int = 30


class RedisService(BaseService[RedisConfig]):
    """
    Async-only Redis service for caching and storage.
    
    Provides a clean interface for Redis operations with automatic
    JSON serialization and proper error handling.
    """
    
    def __init__(self, config: Optional[RedisConfig] = None):
        """
        Initialize Redis Service.
        
        Args:
            config: Redis configuration. If not provided, uses environment variables.
        """
        self.logger = logging.getLogger(__name__)
        
        # Use provided config or create from environment
        if config is None:
            config = RedisConfig(
                url=self._get_redis_url(),
                decode_responses=True,
                socket_timeout=5.0
            )
        
        super().__init__(config, logger)
        self._url_source = None  # Track which env var was used
    
    def _get_redis_url(self) -> Optional[str]:
        """
        Get Redis URL from environment variables.
        
        Checks multiple variables for Clever Cloud compatibility.
        """
        # Priority order for Redis URLs (Clever Cloud specific)
        url_env_vars = [
            "REDIS_DIRECT_URI",      # Direct connection within Clever Cloud (preferred)
            "REDIS_DIRECT_URL",      # Public URL over proxy
            "REDIS_URL",             # Standard
            "REDIS_CLI_DIRECT_URI",  # Alternative for CLI
            "REDIS_CLI_URL"          # Alternative for CLI
        ]
        
        for var in url_env_vars:
            if url := os.environ.get(var):
                self._url_source = var
                self.logger.info(f"Using Redis URL from {var}")
                return url
        
        return None
    
    def _validate_config(self) -> None:
        """Validate Redis configuration"""
        super()._validate_config()
        
        if not self.config.url:
            self.logger.warning(
                "No Redis URL found. Redis functionality will be disabled. "
                "Set one of: REDIS_DIRECT_URI, REDIS_URL, etc."
            )
    
    async def _initialize_client(self) -> Optional[redis.Redis]:
        """Initialize the Redis client"""
        if not self.config.url:
            self.logger.warning("Redis disabled - no URL configured")
            return None
        
        try:
            # Create async Redis client
            client = redis.from_url(
                self.config.url,
                decode_responses=self.config.decode_responses,
                socket_timeout=self.config.socket_timeout,
                max_connections=self.config.max_connections,
                retry_on_timeout=self.config.retry_on_timeout,
                health_check_interval=self.config.health_check_interval
            )
            
            # Test connection
            await client.ping()
            self.logger.info("Redis connection successful")
            
            return client
            
        except Exception as e:
            error_msg = f"Failed to connect to Redis: {str(e)}"
            self.logger.error(error_msg)
            
            # Don't fail initialization - Redis is optional
            self.logger.warning("Redis functionality disabled due to connection error")
            return None
    
    async def get(
        self, 
        key: str, 
        default: Any = None,
        deserialize_json: bool = True
    ) -> Any:
        """
        Get a value from Redis.
        
        Args:
            key: The key to retrieve
            default: Default value if key doesn't exist
            deserialize_json: Whether to deserialize JSON strings
            
        Returns:
            The stored value or default
        """
        if not self._client:
            return default
        
        try:
            value = await self._client.get(key)
            
            if value is None:
                return default
            
            # Try to deserialize JSON if requested
            if deserialize_json and isinstance(value, str):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    # Not JSON, return as string
                    pass
            
            return value
            
        except Exception as e:
            self.logger.warning(f"Redis get failed for key '{key}': {e}")
            return default
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        serialize_json: bool = True
    ) -> bool:
        """
        Set a value in Redis.
        
        Args:
            key: The key to set
            value: The value to store
            ttl: Time to live in seconds
            serialize_json: Whether to serialize non-string values as JSON
            
        Returns:
            True if successful, False otherwise
        """
        if not self._client:
            return False
        
        try:
            # Serialize value if needed
            if serialize_json and not isinstance(value, (str, bytes)):
                value = json.dumps(value)
            
            # Set with optional TTL
            if ttl:
                await self._client.setex(key, ttl, value)
            else:
                await self._client.set(key, value)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Redis set failed for key '{key}': {e}")
            return False
    
    async def delete(self, *keys: str) -> int:
        """
        Delete one or more keys.
        
        Args:
            *keys: Keys to delete
            
        Returns:
            Number of keys deleted
        """
        if not self._client or not keys:
            return 0
        
        try:
            return await self._client.delete(*keys)
        except Exception as e:
            self.logger.error(f"Redis delete failed: {e}")
            return 0
    
    async def exists(self, *keys: str) -> int:
        """
        Check if keys exist.
        
        Args:
            *keys: Keys to check
            
        Returns:
            Number of keys that exist
        """
        if not self._client or not keys:
            return 0
        
        try:
            return await self._client.exists(*keys)
        except Exception as e:
            self.logger.warning(f"Redis exists check failed: {e}")
            return 0
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """
        Get keys matching pattern.
        
        Args:
            pattern: Pattern to match (default: "*" for all)
            
        Returns:
            List of matching keys
        """
        if not self._client:
            return []
        
        try:
            keys = await self._client.keys(pattern)
            # Convert bytes to strings if needed
            return [k.decode() if isinstance(k, bytes) else k for k in keys]
        except Exception as e:
            self.logger.warning(f"Redis keys failed: {e}")
            return []
    
    async def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration on a key.
        
        Args:
            key: Key to expire
            seconds: Seconds until expiration
            
        Returns:
            True if expiration was set
        """
        if not self._client:
            return False
        
        try:
            return await self._client.expire(key, seconds)
        except Exception as e:
            self.logger.error(f"Redis expire failed for key '{key}': {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """
        Get time to live for a key.
        
        Args:
            key: Key to check
            
        Returns:
            TTL in seconds, -1 if no TTL, -2 if key doesn't exist
        """
        if not self._client:
            return -2
        
        try:
            return await self._client.ttl(key)
        except Exception as e:
            self.logger.warning(f"Redis ttl failed for key '{key}': {e}")
            return -2
    
    async def mget(self, keys: List[str]) -> List[Any]:
        """
        Get multiple values at once.
        
        Args:
            keys: List of keys to get
            
        Returns:
            List of values (None for missing keys)
        """
        if not self._client or not keys:
            return [None] * len(keys)
        
        try:
            values = await self._client.mget(keys)
            # Try to deserialize JSON values
            result = []
            for value in values:
                if value is None:
                    result.append(None)
                elif isinstance(value, str):
                    try:
                        result.append(json.loads(value))
                    except json.JSONDecodeError:
                        result.append(value)
                else:
                    result.append(value)
            return result
        except Exception as e:
            self.logger.warning(f"Redis mget failed: {e}")
            return [None] * len(keys)
    
    async def mset(self, mapping: Dict[str, Any]) -> bool:
        """
        Set multiple values at once.
        
        Args:
            mapping: Dictionary of key-value pairs
            
        Returns:
            True if successful
        """
        if not self._client or not mapping:
            return False
        
        try:
            # Serialize values
            serialized = {}
            for key, value in mapping.items():
                if not isinstance(value, (str, bytes)):
                    serialized[key] = json.dumps(value)
                else:
                    serialized[key] = value
            
            await self._client.mset(serialized)
            return True
        except Exception as e:
            self.logger.error(f"Redis mset failed: {e}")
            return False
    
    async def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment a counter.
        
        Args:
            key: Counter key
            amount: Amount to increment by
            
        Returns:
            New value or None on error
        """
        if not self._client:
            return None
        
        try:
            return await self._client.incrby(key, amount)
        except Exception as e:
            self.logger.error(f"Redis incr failed for key '{key}': {e}")
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check Redis service health.
        
        Returns:
            Health status including connection info
        """
        if not self.config.url:
            return {
                "healthy": True,  # Not unhealthy, just disabled
                "status": "disabled",
                "details": {
                    "message": "Redis not configured"
                }
            }
        
        try:
            if not self._client:
                return {
                    "healthy": False,
                    "status": "not_connected",
                    "details": {
                        "url_source": self._url_source,
                        "error": "Client not initialized"
                    }
                }
            
            # Ping Redis
            await self._client.ping()
            
            # Get info
            info = await self._client.info()
            
            return {
                "healthy": True,
                "status": "connected",
                "details": {
                    "url_source": self._url_source,
                    "redis_version": info.get("redis_version", "unknown"),
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory_human": info.get("used_memory_human", "unknown")
                }
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "status": "error",
                "details": {
                    "url_source": self._url_source,
                    "error": str(e)
                }
            }
    
    async def _cleanup(self) -> None:
        """Clean up Redis connection"""
        if self._client:
            try:
                await self._client.close()
            except Exception as e:
                self.logger.warning(f"Error closing Redis client: {e}")
    
    def is_connected(self) -> bool:
        """Check if Redis is connected and available"""
        return self._client is not None


# Factory function for convenience
async def create_redis_service(
    url: Optional[str] = None,
    **kwargs
) -> RedisService:
    """
    Create and initialize a Redis service instance.
    
    Args:
        url: Redis URL (uses env vars if not provided)
        **kwargs: Additional config parameters
        
    Returns:
        Initialized RedisService
    """
    config = RedisConfig(
        url=url,
        **kwargs
    )
    service = RedisService(config)
    await service.initialize()
    return service


# Optional singleton support (if needed for compatibility)
_singleton_instance: Optional[RedisService] = None


async def get_redis_singleton() -> RedisService:
    """
    Get a singleton Redis instance (for backward compatibility).
    
    Returns:
        Singleton RedisService instance
    """
    global _singleton_instance
    if _singleton_instance is None:
        _singleton_instance = await create_redis_service()
    return _singleton_instance