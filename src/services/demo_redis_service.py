# src/v2/services/demo_redis_service.py
"""
Demo showing V2 Redis Service improvements over V1.

Run with: python -m src.v2.services.demo_redis_service
"""
import asyncio
import os
from datetime import datetime
from src.services.redis_service import RedisService, RedisConfig


async def demo_old_vs_new():
    """Show the differences between old and new implementation"""
    print("🔄 REDIS SERVICE: OLD VS NEW")
    print("=" * 60)
    
    print("\n❌ OLD IMPLEMENTATION ISSUES:")
    print("- Forced singleton pattern")
    print("- Mixed sync/async patterns")
    print("- No proper health checks")
    print("- Limited error handling")
    
    print("\n✅ NEW IMPLEMENTATION BENEFITS:")
    print("- Optional singleton (not forced)")
    print("- Fully async interface")
    print("- Automatic JSON serialization")
    print("- Graceful degradation (optional Redis)")
    print("- Health monitoring")
    print("- Multiple URL source support")


async def demo_basic_usage():
    """Demonstrate basic Redis service usage"""
    print("\n\n📝 BASIC USAGE DEMO")
    print("-" * 60)
    
    # Create service
    print("Creating Redis service...")
    service = RedisService()
    
    print("\nRedis URL priority (Clever Cloud compatible):")
    print("1. REDIS_DIRECT_URI    (preferred)")
    print("2. REDIS_DIRECT_URL")
    print("3. REDIS_URL          (standard)")
    print("4. REDIS_CLI_DIRECT_URI")
    print("5. REDIS_CLI_URL")
    
    print("\n✅ Service created (Redis is optional)")
    
    print("\n🔧 Basic Operations:")
    print(">>> # Set a value")
    print(">>> await redis.set('user:123', {'name': 'Max', 'age': 30})")
    print(">>> ")
    print(">>> # Get a value (auto-deserialized)")
    print(">>> user = await redis.get('user:123')")
    print(">>> print(user)  # {'name': 'Max', 'age': 30}")
    
    print("\n>>> # Set with TTL")
    print(">>> await redis.set('session:abc', data, ttl=3600)")
    print(">>> ")
    print(">>> # Get with default")
    print(">>> value = await redis.get('missing', default='not found')")


async def demo_json_handling():
    """Demonstrate automatic JSON handling"""
    print("\n\n🔧 AUTOMATIC JSON HANDLING")
    print("-" * 60)
    
    print("Complex data structures handled automatically:")
    
    print("\n>>> # Store complex data")
    print(">>> feedback = {")
    print("...     'session_id': 'abc123',")
    print("...     'timestamp': datetime.now().isoformat(),")
    print("...     'responses': ['helpful', 'clear', 8],")
    print("...     'metadata': {'version': 2}")
    print("... }")
    print(">>> await redis.set('feedback:abc123', feedback)")
    
    print("\n>>> # Retrieved as Python object")
    print(">>> data = await redis.get('feedback:abc123')")
    print(">>> print(type(data))  # <class 'dict'>")
    
    print("\n>>> # Disable JSON for raw strings")
    print(">>> await redis.set('raw:data', 'plain text', serialize_json=False)")
    print(">>> text = await redis.get('raw:data', deserialize_json=False)")


async def demo_graceful_degradation():
    """Demonstrate graceful degradation when Redis is unavailable"""
    print("\n\n🛡️ GRACEFUL DEGRADATION")
    print("-" * 60)
    
    print("Redis is optional - app continues without it:")
    
    print("\n>>> # No Redis URL configured")
    print(">>> service = RedisService()  # No error!")
    print(">>> await service.initialize()  # Still works!")
    print(">>> ")
    print(">>> # Operations return defaults")
    print(">>> value = await service.get('key', default='fallback')")
    print(">>> print(value)  # 'fallback'")
    print(">>> ")
    print(">>> success = await service.set('key', 'value')")
    print(">>> print(success)  # False (but no crash)")
    
    print("\n✅ Perfect for development without Redis!")


async def demo_batch_operations():
    """Demonstrate batch operations"""
    print("\n\n📦 BATCH OPERATIONS")
    print("-" * 60)
    
    print("Efficient multi-key operations:")
    
    print("\n>>> # Get multiple values at once")
    print(">>> keys = ['user:1', 'user:2', 'user:3']")
    print(">>> users = await redis.mget(keys)")
    print(">>> # Returns [user1_data, user2_data, None]")
    
    print("\n>>> # Set multiple values at once")
    print(">>> await redis.mset({")
    print("...     'config:feature1': True,")
    print("...     'config:feature2': {'enabled': True, 'level': 5},")
    print("...     'config:version': '2.0'")
    print("... })")
    
    print("\n>>> # Delete multiple keys")
    print(">>> deleted = await redis.delete('old:1', 'old:2', 'old:3')")
    print(">>> print(f'Deleted {deleted} keys')")


async def demo_counters():
    """Demonstrate counter operations"""
    print("\n\n🔢 COUNTER OPERATIONS")
    print("-" * 60)
    
    print("Atomic counter operations:")
    
    print("\n>>> # Increment page views")
    print(">>> views = await redis.incr('stats:page:home')")
    print(">>> print(f'Page views: {views}')")
    print(">>> ")
    print(">>> # Increment by amount")
    print(">>> total = await redis.incr('stats:api:calls', 5)")
    print(">>> ")
    print(">>> # Decrement (negative increment)")
    print(">>> remaining = await redis.incr('quota:user:123', -1)")


async def demo_ttl_operations():
    """Demonstrate TTL and expiration"""
    print("\n\n⏰ TTL AND EXPIRATION")
    print("-" * 60)
    
    print("Managing key expiration:")
    
    print("\n>>> # Set with TTL")
    print(">>> await redis.set('temp:token', 'abc123', ttl=3600)")
    print(">>> ")
    print(">>> # Check remaining TTL")
    print(">>> ttl = await redis.ttl('temp:token')")
    print(">>> print(f'Expires in {ttl} seconds')")
    print(">>> ")
    print(">>> # Set expiration on existing key")
    print(">>> await redis.expire('user:session', 7200)")
    print(">>> ")
    print(">>> # TTL special values:")
    print(">>> # -1 = no expiration")
    print(">>> # -2 = key doesn't exist")


async def demo_health_monitoring():
    """Demonstrate health check functionality"""
    print("\n\n🏥 HEALTH MONITORING")
    print("-" * 60)
    
    # Mock health check responses
    print("Health check scenarios:")
    
    print("\n1. Healthy Redis:")
    healthy = {
        "healthy": True,
        "status": "connected",
        "details": {
            "url_source": "REDIS_DIRECT_URI",
            "redis_version": "7.0.0",
            "connected_clients": 5,
            "used_memory_human": "1.5M"
        }
    }
    for key, value in healthy.items():
        print(f"   {key}: {value}")
    
    print("\n2. Redis not configured:")
    disabled = {
        "healthy": True,
        "status": "disabled",
        "details": {"message": "Redis not configured"}
    }
    for key, value in disabled.items():
        print(f"   {key}: {value}")
    
    print("\n3. Connection error:")
    error = {
        "healthy": False,
        "status": "error",
        "details": {
            "url_source": "REDIS_URL",
            "error": "Connection refused"
        }
    }
    for key, value in error.items():
        print(f"   {key}: {value}")


async def demo_development_workflow():
    """Demonstrate development workflow without caching"""
    print("\n\n💻 DEVELOPMENT WORKFLOW")
    print("-" * 60)
    
    print("Flexible caching strategy:")
    
    print("\n>>> # Development: No Redis needed")
    print(">>> ENABLE_CACHE = os.getenv('ENABLE_CACHE', 'false') == 'true'")
    print(">>> ")
    print(">>> if ENABLE_CACHE and redis.is_connected():")
    print("...     cached = await redis.get(cache_key)")
    print("...     if cached:")
    print("...         return cached")
    print(">>> ")
    print(">>> # Always get fresh data in development")
    print(">>> result = await weaviate.search(...)")
    print(">>> ")
    print(">>> if ENABLE_CACHE and redis.is_connected():")
    print("...     await redis.set(cache_key, result, ttl=3600)")
    
    print("\n✅ Perfect for prompt tuning!")


async def demo_testing():
    """Show testing approach"""
    print("\n\n🧪 TESTING APPROACH")
    print("-" * 60)
    
    print("Easy to mock for testing:")
    print("""
    # Mock Redis operations
    mock_redis = Mock(spec=RedisService)
    mock_redis.get.return_value = {'cached': 'data'}
    mock_redis.set.return_value = True
    mock_redis.is_connected.return_value = True
    
    # Test without real Redis
    async def test_with_cache(mock_redis):
        result = await mock_redis.get('key')
        assert result == {'cached': 'data'}
    
    # Test graceful degradation
    mock_redis.is_connected.return_value = False
    result = await function_using_redis()
    # Should work without Redis!
    """)


async def main():
    """Run all demos"""
    print("\n🚀 WuffChat V2 Redis Service Demo")
    print("=" * 60)
    
    await demo_old_vs_new()
    await demo_basic_usage()
    await demo_json_handling()
    await demo_graceful_degradation()
    await demo_batch_operations()
    await demo_counters()
    await demo_ttl_operations()
    await demo_health_monitoring()
    await demo_development_workflow()
    await demo_testing()
    
    print("\n\n✅ Demo complete!")
    print("\nKey improvements:")
    print("- Optional Redis (graceful degradation)")
    print("- Automatic JSON handling")
    print("- Fully async interface")
    print("- Flexible caching strategy")
    print("- Health monitoring")
    print("- Easy to test")


if __name__ == "__main__":
    asyncio.run(main())