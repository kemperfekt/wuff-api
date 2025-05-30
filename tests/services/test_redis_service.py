# tests/v2/services/test_redis_service.py
"""
Unit tests for V2 Redis Service.

Uses mock-first approach to test without requiring a real Redis instance.
"""
import os
import json
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import timedelta

from src.services.redis_service import (
    RedisService,
    RedisConfig,
    create_redis_service,
    get_redis_singleton
)
from src.core.exceptions import RedisServiceError


@pytest.fixture
def mock_config():
    """Create a test configuration"""
    return RedisConfig(
        url="redis://localhost:6379/0",
        decode_responses=True,
        socket_timeout=5.0
    )


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client"""
    client = AsyncMock()
    
    # Mock basic operations
    client.ping = AsyncMock(return_value=True)
    client.get = AsyncMock(return_value=None)
    client.set = AsyncMock(return_value=True)
    client.setex = AsyncMock(return_value=True)
    client.delete = AsyncMock(return_value=1)
    client.exists = AsyncMock(return_value=1)
    client.keys = AsyncMock(return_value=[])
    client.expire = AsyncMock(return_value=True)
    client.ttl = AsyncMock(return_value=3600)
    client.mget = AsyncMock(return_value=[None, None])
    client.mset = AsyncMock(return_value=True)
    client.incrby = AsyncMock(return_value=1)
    client.info = AsyncMock(return_value={
        "redis_version": "7.0.0",
        "connected_clients": 5,
        "used_memory_human": "1.5M"
    })
    client.close = AsyncMock()
    
    return client


@pytest.fixture
async def redis_service(mock_config, mock_redis_client):
    """Create a Redis service with mocked client"""
    service = RedisService(mock_config)
    
    # Patch the client creation
    with patch('src.services.redis_service.redis.from_url', return_value=mock_redis_client):
        await service.initialize()
    
    return service


class TestRedisService:
    """Test Redis Service functionality"""
    
    async def test_initialization(self, mock_config, mock_redis_client):
        """Test service initialization"""
        service = RedisService(mock_config)
        
        assert service.config == mock_config
        assert not service.is_initialized
        
        with patch('src.services.redis_service.redis.from_url', return_value=mock_redis_client):
            await service.initialize()
        
        assert service.is_initialized
        assert service.is_connected()
        mock_redis_client.ping.assert_called_once()
    
    async def test_initialization_from_env(self):
        """Test initialization from environment variables"""
        with patch.dict('os.environ', {
            'REDIS_DIRECT_URI': 'redis://direct:6379',
            'REDIS_URL': 'redis://standard:6379'
        }):
            service = RedisService()
            
            # Should prefer REDIS_DIRECT_URI
            assert service.config.url == 'redis://direct:6379'
            assert service._url_source == 'REDIS_DIRECT_URI'
    
    async def test_no_redis_url(self):
        """Test behavior when no Redis URL is configured"""
        with patch.dict('os.environ', {}, clear=True):
            service = RedisService()
            
            assert service.config.url is None
            
            # Should initialize without error but with no client
            await service.initialize()
            assert service.is_initialized
            assert not service.is_connected()
    
    async def test_connection_failure(self, mock_config):
        """Test handling of connection failures"""
        service = RedisService(mock_config)
        
        # Make ping fail
        failing_client = AsyncMock()
        failing_client.ping.side_effect = Exception("Connection refused")
        
        with patch('src.services.redis_service.redis.from_url', return_value=failing_client):
            # Should not raise but log warning
            await service.initialize()
        
        assert service.is_initialized
        assert not service.is_connected()
    
    async def test_get_string(self, redis_service, mock_redis_client):
        """Test getting string value"""
        mock_redis_client.get.return_value = "test value"
        
        result = await redis_service.get("test_key")
        
        assert result == "test value"
        mock_redis_client.get.assert_called_once_with("test_key")
    
    async def test_get_json(self, redis_service, mock_redis_client):
        """Test getting JSON value with auto-deserialization"""
        mock_redis_client.get.return_value = '{"name": "test", "value": 42}'
        
        result = await redis_service.get("test_key")
        
        assert result == {"name": "test", "value": 42}
    
    async def test_get_default(self, redis_service, mock_redis_client):
        """Test getting with default value"""
        mock_redis_client.get.return_value = None
        
        result = await redis_service.get("missing_key", default="default_value")
        
        assert result == "default_value"
    
    async def test_get_no_client(self, redis_service):
        """Test get when Redis is not connected"""
        redis_service._client = None
        
        result = await redis_service.get("test_key", default="fallback")
        
        assert result == "fallback"
    
    async def test_set_string(self, redis_service, mock_redis_client):
        """Test setting string value"""
        result = await redis_service.set("test_key", "test value")
        
        assert result is True
        mock_redis_client.set.assert_called_once_with("test_key", "test value")
    
    async def test_set_json(self, redis_service, mock_redis_client):
        """Test setting dict value with auto-serialization"""
        data = {"name": "test", "value": 42}
        
        result = await redis_service.set("test_key", data)
        
        assert result is True
        mock_redis_client.set.assert_called_once_with("test_key", json.dumps(data))
    
    async def test_set_with_ttl(self, redis_service, mock_redis_client):
        """Test setting with TTL"""
        result = await redis_service.set("test_key", "value", ttl=3600)
        
        assert result is True
        mock_redis_client.setex.assert_called_once_with("test_key", 3600, "value")
    
    async def test_set_no_client(self, redis_service):
        """Test set when Redis is not connected"""
        redis_service._client = None
        
        result = await redis_service.set("test_key", "value")
        
        assert result is False
    
    async def test_delete(self, redis_service, mock_redis_client):
        """Test deleting keys"""
        mock_redis_client.delete.return_value = 2
        
        result = await redis_service.delete("key1", "key2")
        
        assert result == 2
        mock_redis_client.delete.assert_called_once_with("key1", "key2")
    
    async def test_exists(self, redis_service, mock_redis_client):
        """Test checking key existence"""
        mock_redis_client.exists.return_value = 1
        
        result = await redis_service.exists("test_key")
        
        assert result == 1
        mock_redis_client.exists.assert_called_once_with("test_key")
    
    async def test_keys(self, redis_service, mock_redis_client):
        """Test getting keys by pattern"""
        mock_redis_client.keys.return_value = [b"key1", b"key2", "key3"]
        
        result = await redis_service.keys("key*")
        
        assert result == ["key1", "key2", "key3"]
        mock_redis_client.keys.assert_called_once_with("key*")
    
    async def test_expire(self, redis_service, mock_redis_client):
        """Test setting expiration"""
        result = await redis_service.expire("test_key", 3600)
        
        assert result is True
        mock_redis_client.expire.assert_called_once_with("test_key", 3600)
    
    async def test_ttl(self, redis_service, mock_redis_client):
        """Test getting TTL"""
        mock_redis_client.ttl.return_value = 3600
        
        result = await redis_service.ttl("test_key")
        
        assert result == 3600
        mock_redis_client.ttl.assert_called_once_with("test_key")
    
    async def test_mget(self, redis_service, mock_redis_client):
        """Test getting multiple values"""
        mock_redis_client.mget.return_value = [
            "value1",
            '{"key": "value2"}',
            None
        ]
        
        result = await redis_service.mget(["key1", "key2", "key3"])
        
        assert result == ["value1", {"key": "value2"}, None]
    
    async def test_mset(self, redis_service, mock_redis_client):
        """Test setting multiple values"""
        mapping = {
            "key1": "value1",
            "key2": {"nested": "data"},
            "key3": 42
        }
        
        result = await redis_service.mset(mapping)
        
        assert result is True
        
        # Check that non-strings were serialized
        call_args = mock_redis_client.mset.call_args[0][0]
        assert call_args["key1"] == "value1"
        assert call_args["key2"] == '{"nested": "data"}'
        assert call_args["key3"] == "42"
    
    async def test_incr(self, redis_service, mock_redis_client):
        """Test incrementing counter"""
        mock_redis_client.incrby.return_value = 5
        
        result = await redis_service.incr("counter", 2)
        
        assert result == 5
        mock_redis_client.incrby.assert_called_once_with("counter", 2)
    
    async def test_health_check_healthy(self, redis_service):
        """Test health check when service is healthy"""
        health = await redis_service.health_check()
        
        assert health['healthy'] is True
        assert health['status'] == 'connected'
        assert health['details']['redis_version'] == '7.0.0'
        assert health['details']['connected_clients'] == 5
    
    async def test_health_check_no_url(self):
        """Test health check when Redis is not configured"""
        service = RedisService()  # No URL
        await service.initialize()
        
        health = await service.health_check()
        
        assert health['healthy'] is True
        assert health['status'] == 'disabled'
        assert 'not configured' in health['details']['message']
    
    async def test_health_check_error(self, redis_service, mock_redis_client):
        """Test health check when Redis has errors"""
        mock_redis_client.ping.side_effect = Exception("Connection lost")
        
        health = await redis_service.health_check()
        
        assert health['healthy'] is False
        assert health['status'] == 'error'
        assert 'Connection lost' in health['details']['error']
    
    async def test_cleanup(self, redis_service, mock_redis_client):
        """Test cleanup closes client"""
        await redis_service.shutdown()
        
        mock_redis_client.close.assert_called_once()
        assert not redis_service.is_initialized


class TestRedisServiceFactory:
    """Test factory functions"""
    
    async def test_create_redis_service(self, mock_redis_client):
        """Test service creation via factory"""
        with patch('src.services.redis_service.redis.from_url', return_value=mock_redis_client):
            service = await create_redis_service(
                url="redis://factory:6379",
                socket_timeout=10.0
            )
            
            assert isinstance(service, RedisService)
            assert service.is_initialized
            assert service.config.url == "redis://factory:6379"
            assert service.config.socket_timeout == 10.0
    
    async def test_singleton(self, mock_redis_client):
        """Test singleton pattern"""
        with patch('src.services.redis_service.redis.from_url', return_value=mock_redis_client):
            # First call creates instance
            service1 = await get_redis_singleton()
            
            # Second call returns same instance
            service2 = await get_redis_singleton()
            
            assert service1 is service2


# Integration tests (optional, skipped by default)
@pytest.mark.integration
class TestRedisServiceIntegration:
    """Integration tests that require a real Redis instance"""
    
    @pytest.mark.skipif(
        not os.getenv("RUN_INTEGRATION_TESTS"),
        reason="Integration tests disabled"
    )
    async def test_real_redis_operations(self):
        """Test with real Redis instance"""
        service = await create_redis_service()
        
        # Test basic operations
        key = "test:integration:key"
        value = {"test": "data", "number": 42}
        
        # Set
        success = await service.set(key, value, ttl=60)
        assert success
        
        # Get
        retrieved = await service.get(key)
        assert retrieved == value
        
        # TTL
        ttl = await service.ttl(key)
        assert 0 < ttl <= 60
        
        # Delete
        deleted = await service.delete(key)
        assert deleted == 1
        
        # Verify deletion
        exists = await service.exists(key)
        assert exists == 0