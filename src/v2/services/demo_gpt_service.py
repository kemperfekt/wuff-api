# src/v2/services/demo_gpt_service.py
"""
Demo showing V2 GPT Service improvements over V1.

Run with: python -m src.v2.services.demo_gpt_service
"""
import asyncio
import os
from src.v2.services.gpt_service import GPTService, GPTConfig, create_gpt_service
from src.v2.core.prompt_manager import get_prompt_manager


async def demo_old_vs_new():
    """Show the differences between old and new implementation"""
    print("🔄 GPT SERVICE: OLD VS NEW")
    print("=" * 60)
    
    print("\n❌ OLD IMPLEMENTATION ISSUES:")
    print("- Mixed async/sync functions")
    print("- Hardcoded prompts inside service")
    print("- No proper error handling")
    print("- No health checks")
    print("- No configuration validation")
    
    print("\n✅ NEW IMPLEMENTATION BENEFITS:")
    print("- Fully async")
    print("- Prompts passed as parameters")
    print("- Structured error handling")
    print("- Built-in health checks")
    print("- Configuration validation")
    print("- Mock-friendly for testing")


async def demo_basic_usage():
    """Demonstrate basic GPT service usage"""
    print("\n\n📝 BASIC USAGE DEMO")
    print("-" * 60)
    
    # Create service (would use real API key in production)
    print("Creating GPT service...")
    service = GPTService(GPTConfig(
        api_key=os.getenv("OPENAI_API_KEY", "demo-key"),
        model="gpt-4",
        temperature=0.7
    ))
    
    # In demo mode, we'll mock the initialization
    print("✅ Service created")
    
    # Show how to use with PromptManager
    print("\n🔗 Integration with PromptManager:")
    pm = get_prompt_manager()
    
    # Example: Get a validation prompt
    validation_prompt = pm.get(
        "validation.validate.behavior.template",
        text="Mein Hund bellt ständig"
    )
    
    print(f"Prompt from manager: {validation_prompt[:50]}...")
    
    # Would call service like this:
    print("\nWould call service:")
    print(">>> result = await service.complete(validation_prompt, temperature=0)")
    
    # Example: Generation with system prompt
    print("\n🎯 Using system prompts:")
    dog_prompt = pm.get("generation.dog_perspective", 
                       symptom="Bellen", 
                       match="Hund ist aufgeregt")
    
    print(">>> result = await service.complete(")
    print("...     prompt=dog_prompt,")
    print("...     system_prompt='Du bist ein Hund',")
    print("...     temperature=0.8")
    print("... )")


async def demo_error_handling():
    """Demonstrate error handling"""
    print("\n\n⚠️ ERROR HANDLING DEMO")
    print("-" * 60)
    
    # Show configuration validation
    print("1. Configuration validation:")
    try:
        bad_service = GPTService(GPTConfig(api_key=None))
        await bad_service.initialize()
    except Exception as e:
        print(f"   ✅ Caught: {type(e).__name__}: {e}")
    
    # Show input validation
    print("\n2. Input validation:")
    print("   - Empty prompts rejected")
    print("   - Invalid parameters caught")
    print("   - API errors wrapped properly")


async def demo_health_checks():
    """Demonstrate health check functionality"""
    print("\n\n🏥 HEALTH CHECK DEMO")
    print("-" * 60)
    
    # Mock health check response
    mock_health = {
        "healthy": True,
        "status": "connected",
        "details": {
            "model": "gpt-4",
            "response_time_ms": 150,
            "api_key_set": True,
            "api_key_prefix": "sk-proj..."
        }
    }
    
    print("Health check response:")
    for key, value in mock_health.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for k, v in value.items():
                print(f"    {k}: {v}")
        else:
            print(f"  {key}: {value}")


async def demo_structured_output():
    """Demonstrate structured output generation"""
    print("\n\n🔧 STRUCTURED OUTPUT DEMO")
    print("-" * 60)
    
    print("Requesting structured JSON output:")
    print(">>> result = await service.complete_structured(")
    print("...     prompt='Analyze this behavior',")
    print("...     response_format={")
    print("...         'instinct': 'string',")
    print("...         'confidence': 'number',")
    print("...         'explanation': 'string'")
    print("...     }")
    print("... )")
    
    print("\nWould return parsed JSON:")
    mock_result = {
        "instinct": "territorial",
        "confidence": 0.8,
        "explanation": "Der Hund zeigt territoriales Verhalten"
    }
    print(f">>> {mock_result}")


async def demo_testing():
    """Show how easy it is to test"""
    print("\n\n🧪 TESTING DEMO")
    print("-" * 60)
    
    print("Mock-first testing approach:")
    print("""
    # Easy to mock in tests
    @pytest.fixture
    def mock_gpt_service():
        service = Mock(spec=GPTService)
        service.complete.return_value = "Mocked response"
        return service
    
    # No real API calls in unit tests
    async def test_my_feature(mock_gpt_service):
        result = await mock_gpt_service.complete("test")
        assert result == "Mocked response"
    """)


async def main():
    """Run all demos"""
    print("\n🚀 WuffChat V2 GPT Service Demo")
    print("=" * 60)
    
    await demo_old_vs_new()
    await demo_basic_usage()
    await demo_error_handling()
    await demo_health_checks()
    await demo_structured_output()
    await demo_testing()
    
    print("\n\n✅ Demo complete!")
    print("\nKey improvements:")
    print("- Clean async interface")
    print("- No embedded prompts")
    print("- Proper error handling")
    print("- Easy to test")
    print("- Health monitoring")
    print("- Structured output support")


if __name__ == "__main__":
    # Handle missing import gracefully
    import sys
    import os
    
    # Add src to path if needed
    if 'src' not in sys.path:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    
    asyncio.run(main())