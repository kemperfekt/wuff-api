#!/usr/bin/env python3
"""
Debug Weaviate integration issues in WuffChat V2
Run this to identify the exact Weaviate error
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_weaviate_connection():
    """Test basic Weaviate connection"""
    print("🔍 Testing Weaviate Connection...")
    
    try:
        from src.v2.services.weaviate_service import WeaviateService
        
        # Check environment variables
        weaviate_url = os.getenv("WEAVIATE_URL", "Not set")
        weaviate_key = os.getenv("WEAVIATE_API_KEY", "Not set")
        
        print(f"   WEAVIATE_URL: {weaviate_url}")
        print(f"   WEAVIATE_API_KEY: {'Set' if weaviate_key != 'Not set' else 'Not set'}")
        
        # Initialize service
        service = WeaviateService()
        
        # Test initialization
        print("\n📊 Testing service initialization...")
        await service.ensure_initialized()
        print("   ✅ Service initialized")
        
        # Test health check
        print("\n🏥 Testing health check...")
        health = await service.health_check()
        print(f"   Health check result: {health}")
        
        # Test actual query
        print("\n🔎 Testing search functionality...")
        results = await service.search(
            query="Hund bellt",
            collection="Symptome",  # Try V1 collection name
            limit=1
        )
        print(f"   Search returned {len(results)} results")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {str(e)}")
        
        # Common fixes
        if "connection" in str(e).lower():
            print("\n💡 Fix: Check WEAVIATE_URL environment variable")
        elif "unauthorized" in str(e).lower():
            print("\n💡 Fix: Check WEAVIATE_API_KEY environment variable")
        elif "collection" in str(e).lower() or "class" in str(e).lower():
            print("\n💡 Fix: Collection name mismatch. V1 uses 'Symptome', check what V2 expects")
        elif "attribute" in str(e).lower():
            print("\n💡 Fix: Async method not awaited. Add 'await' before Weaviate calls")
        
        return False


async def test_orchestrator_weaviate_integration():
    """Test how orchestrator uses Weaviate"""
    print("\n\n🔧 Testing Orchestrator-Weaviate Integration...")
    
    try:
        from src.v2.core.orchestrator import Orchestrator
        from src.v2.core.flow_engine import FlowEngine
        from unittest.mock import AsyncMock
        
        # Create minimal orchestrator setup
        flow_engine = AsyncMock()
        flow_engine.get_current_state.return_value = "SYMPTOM_COLLECTION"
        
        # This will reveal initialization issues
        print("   Creating orchestrator...")
        orchestrator = Orchestrator(flow_engine=flow_engine)
        
        # Check if orchestrator has Weaviate service
        if hasattr(orchestrator, 'weaviate_service'):
            print("   ✅ Orchestrator has weaviate_service")
            
            # Check if it's initialized
            if hasattr(orchestrator.weaviate_service, 'is_initialized'):
                print(f"   Weaviate initialized: {orchestrator.weaviate_service.is_initialized}")
        else:
            print("   ❌ Orchestrator missing weaviate_service attribute")
            
    except Exception as e:
        print(f"\n❌ Orchestrator Error: {type(e).__name__}: {str(e)}")
        
        if "cannot import" in str(e).lower():
            print("\n💡 Fix: Import error. Check if all V2 services are properly imported")
        elif "'NoneType'" in str(e).lower():
            print("\n💡 Fix: Service not injected. Check Orchestrator __init__ method")


async def test_flow_handler_weaviate():
    """Test how flow handlers use Weaviate"""
    print("\n\n🔄 Testing Flow Handler-Weaviate Integration...")
    
    try:
        from src.v2.core.flow_handlers import FlowHandlers
        
        # Check if handlers reference Weaviate
        print("   Checking FlowHandlers implementation...")
        
        # This will show import/initialization issues
        handlers = FlowHandlers()
        
        # Look for Weaviate usage
        handler_methods = [m for m in dir(handlers) if m.startswith('handle_')]
        print(f"   Found {len(handler_methods)} handler methods")
        
        # Check if any handler uses Weaviate
        for method_name in handler_methods:
            method = getattr(handlers, method_name)
            if method.__code__.co_names and 'weaviate' in str(method.__code__.co_names).lower():
                print(f"   📌 {method_name} uses Weaviate")
                
    except Exception as e:
        print(f"\n❌ Flow Handler Error: {type(e).__name__}: {str(e)}")


async def check_collection_names():
    """Check what collections exist in Weaviate"""
    print("\n\n📚 Checking Weaviate Collections...")
    
    try:
        import weaviate
        
        client = weaviate.Client(
            url=os.getenv("WEAVIATE_URL"),
            auth_client_secret=weaviate.AuthApiKey(api_key=os.getenv("WEAVIATE_API_KEY"))
        )
        
        # Get schema
        schema = client.schema.get()
        
        print("   Available collections:")
        for class_obj in schema.get('classes', []):
            print(f"   - {class_obj['class']}")
            
        # Check expected collections
        expected = ['Symptome', 'Instinkte', 'Erziehung', 'Allgemein']
        for collection in expected:
            exists = any(c['class'] == collection for c in schema.get('classes', []))
            status = "✅" if exists else "❌"
            print(f"   {status} {collection}")
            
    except Exception as e:
        print(f"   ❌ Could not check collections: {e}")


async def generate_quick_fix():
    """Generate a quick fix based on findings"""
    print("\n\n🔨 Generating Quick Fix...")
    
    fix_code = '''# Add this to src/v2/services/weaviate_service.py

class WeaviateService(BaseService):
    async def search(self, query: str, collection: str = "Symptome", limit: int = 5):
        """Search Weaviate with proper error handling"""
        await self.ensure_initialized()
        
        try:
            # Use the V1 collection names that exist
            if collection == "symptoms":  # V2 might use lowercase
                collection = "Symptome"   # V1 uses uppercase
            
            result = self.client.query.get(
                collection,
                ["content", "instinct", "category"]
            ).with_near_text({
                "concepts": [query]
            }).with_limit(limit).do()
            
            return result.get('data', {}).get('Get', {}).get(collection, [])
            
        except Exception as e:
            logger.error(f"Weaviate search error: {e}")
            return []  # Return empty list on error
'''
    
    print(fix_code)
    
    orchestrator_fix = '''# Add this to src/v2/core/orchestrator.py

async def initialize_services(self):
    """Initialize all async services"""
    if hasattr(self, 'weaviate_service'):
        await self.weaviate_service.ensure_initialized()
    if hasattr(self, 'gpt_service'):
        await self.gpt_service.ensure_initialized()
'''
    
    print("\n" + orchestrator_fix)


async def main():
    """Run all diagnostics"""
    print("🚀 WuffChat V2 Weaviate Debugger")
    print("=" * 60)
    
    # Run tests in order
    weaviate_ok = await test_weaviate_connection()
    
    if weaviate_ok:
        await test_orchestrator_weaviate_integration()
        await test_flow_handler_weaviate()
    
    await check_collection_names()
    await generate_quick_fix()
    
    print("\n" + "=" * 60)
    print("✅ Diagnostic complete!")
    print("\nNext steps:")
    print("1. Apply the quick fixes above")
    print("2. Run: python -m uvicorn src.v2.main:app --reload")
    print("3. Test the flow manually")
    print("4. If working, deploy with test skips")


if __name__ == "__main__":
    asyncio.run(main())