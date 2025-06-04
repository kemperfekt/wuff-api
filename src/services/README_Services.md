# WuffChat V2 Services

## Overview

The V2 services layer provides clean, async-only interfaces to external services with consistent patterns:

- All services inherit from `BaseService`
- Fully async methods
- Proper error handling with V2 exceptions
- Health checks for monitoring
- Mock-friendly for testing
- No embedded prompts or business logic

## Services

### GPTService

Clean wrapper around OpenAI's GPT API.

```python
from src.v2.services.gpt_service import GPTService

# Initialize
service = GPTService()
await service.initialize()

# Generate text
response = await service.complete(
    prompt="Describe this behavior",
    system_prompt="You are a helpful assistant",
    temperature=0.7
)

# Validate input
is_dog_related = await service.validate_behavior_input(text)

# Health check
health = await service.health_check()
```

**Key Features:**
- Async-only interface
- Configuration validation
- Structured output support
- Health monitoring
- Easy to mock for testing

### WeaviateService

Direct vector search without Query Agent complexity.

```python
from src.v2.services.weaviate_service import WeaviateService

# Initialize
service = WeaviateService()
await service.initialize()

# Search
results = await service.search(
    collection="Symptome",
    query="Hund bellt",
    limit=5,
    return_metadata=True
)

# Vector search
results = await service.vector_search(
    collection="Instinkte",
    vector=[0.1, 0.2, ...],
    limit=3
)

# Get collections
collections = await service.get_collections()
```

**Key Features:**
- Direct search (no Query Agent)
- Generic interface
- No built-in caching
- Multiple search methods
- Health monitoring

### RedisService

Optional caching with graceful degradation.

```python
from src.v2.services.redis_service import RedisService

# Initialize
service = RedisService()
await service.initialize()

# Basic operations
await service.set("key", {"data": "value"}, ttl=3600)
data = await service.get("key", default=None)

# Batch operations
await service.mset({"k1": "v1", "k2": {"nested": "data"}})
values = await service.mget(["k1", "k2", "k3"])

# Counters
count = await service.incr("counter", 1)
```

**Key Features:**
- Optional (app works without Redis)
- Automatic JSON serialization
- Multiple Redis URL support (Clever Cloud)
- Batch operations
- TTL support

## Common Patterns

### Initialization

All services follow the same pattern:

```python
# Default configuration from environment
service = ServiceClass()
await service.initialize()

# Custom configuration
config = ServiceConfig(
    api_key="...",
    timeout=30
)
service = ServiceClass(config)
await service.initialize()

# Factory function
service = await create_service(param="value")
```

### Error Handling

All services use the V2 exception hierarchy:

```python
try:
    result = await service.operation()
except ConfigurationError as e:
    # Handle configuration issues
    pass
except ServiceError as e:
    # Handle service-specific errors
    pass
```

### Health Checks

All services provide health monitoring:

```python
health = await service.health_check()
# Returns:
# {
#     "healthy": bool,
#     "status": str,
#     "details": {...}
# }
```

### Testing

Services are designed to be easily mocked:

```python
# Mock service
mock_service = Mock(spec=GPTService)
mock_service.complete.return_value = "Response"

# Inject mock
agent = Agent(gpt_service=mock_service)
```

## Development vs Production

### Development (Prompt Tuning)
- No caching in Weaviate service
- Redis optional
- Fresh results every query
- Easy to test changes

### Production
- Enable caching at orchestration layer
- Redis for distributed cache
- Optimize for performance
- Health monitoring active

## Migration from V1

### Key Differences

1. **All Async**
   ```python
   # V1
   response = ask_gpt(prompt)
   
   # V2
   response = await gpt_service.complete(prompt)
   ```

2. **No Embedded Prompts**
   ```python
   # V1
   def validate_input(text):
       prompt = "Check if this is about dogs..."  # Embedded
   
   # V2
   async def validate_input(text, prompt):
       # Prompt passed from outside
   ```

3. **Consistent Patterns**
   - All services inherit from BaseService
   - All use the same initialization pattern
   - All provide health checks

4. **Better Separation**
   - Services only handle external communication
   - No business logic in services
   - Prompts come from PromptManager

## Environment Variables

```bash
# GPT Service
OPENAI_API_KEY=sk-...
GPT_MODEL=gpt-4
GPT_TEMPERATURE=0.7

# Weaviate Service
WEAVIATE_URL=https://...
WEAVIATE_API_KEY=...

# Redis Service (all optional)
REDIS_DIRECT_URI=redis://...
REDIS_URL=redis://...

# Feature Flags
ENABLE_CACHE=false  # Development
ENABLE_CACHE=true   # Production
```