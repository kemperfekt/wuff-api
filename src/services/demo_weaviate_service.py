# src/v2/services/demo_weaviate_service.py
"""
Demo showing V2 Weaviate Service improvements over V1.

Run with: python -m src.v2.services.demo_weaviate_service
"""
import asyncio
import os
from src.services.weaviate_service import WeaviateService, WeaviateConfig
from src.core.prompt_manager import get_prompt_manager


async def demo_old_vs_new():
    """Show the differences between old and new implementation"""
    print("🔄 WEAVIATE SERVICE: OLD VS NEW")
    print("=" * 60)
    
    print("\n❌ OLD IMPLEMENTATION ISSUES:")
    print("- Query Agent adds complexity and latency")
    print("- Singleton pattern makes testing difficult")
    print("- Mixed initialization patterns")
    print("- No proper health checks")
    print("- Query Agent makes prompt tuning harder")
    
    print("\n✅ NEW IMPLEMENTATION BENEFITS:")
    print("- Direct search only - full control")
    print("- Consistent async interface")
    print("- Predictable results for prompt tuning")
    print("- Proper health monitoring")
    print("- Easy to mock for testing")
    print("- Generic interface - flexible usage")


async def demo_basic_usage():
    """Demonstrate basic Weaviate service usage"""
    print("\n\n📝 BASIC USAGE DEMO")
    print("-" * 60)
    
    # Create service
    print("Creating Weaviate service...")
    service = WeaviateService(WeaviateConfig(
        url=os.getenv("WEAVIATE_URL", "https://demo.weaviate.network"),
        api_key=os.getenv("WEAVIATE_API_KEY", "demo-key")
    ))
    
    print("✅ Service created")
    
    print("\n🔍 Generic Search Interface:")
    print(">>> # Search for symptoms")
    print(">>> results = await service.search(")
    print("...     collection='Symptome',")
    print("...     query='Hund bellt ständig',")
    print("...     limit=5,")
    print("...     return_metadata=True")
    print("... )")
    
    print("\n>>> # Search with specific properties")
    print(">>> results = await service.search(")
    print("...     collection='Instinkte',")
    print("...     query='Jagdverhalten',")
    print("...     properties=['name', 'description'],")
    print("...     limit=3")
    print("... )")
    
    print("\n>>> # Direct vector search")
    print(">>> results = await service.vector_search(")
    print("...     collection='Erziehung',")
    print("...     vector=[0.1, 0.2, 0.3, ...],")
    print("...     limit=10")
    print("... )")


async def demo_prompt_integration():
    """Show how to use with PromptManager"""
    print("\n\n🔗 PROMPT MANAGER INTEGRATION")
    print("-" * 60)
    
    pm = get_prompt_manager()
    
    print("Getting queries from PromptManager:")
    
    # Get a query template
    symptom_query = pm.get("query.symptom", symptom="Bellen")
    print(f"\nQuery template: {symptom_query}")
    
    print("\nUsing with WeaviateService:")
    print(">>> # Get query from PromptManager")
    print(">>> query = pm.get('query.symptom', symptom='Bellen')")
    print(">>> ")
    print(">>> # Use directly with Weaviate")
    print(">>> results = await weaviate.search(")
    print("...     collection='Symptome',")
    print("...     query=query,")
    print("...     limit=5")
    print("... )")


async def demo_collections():
    """Demonstrate collection operations"""
    print("\n\n📚 COLLECTION OPERATIONS")
    print("-" * 60)
    
    print("Available collections in WuffChat:")
    collections = [
        "Symptome - Dog behaviors and symptoms",
        "Instinkte - Four core instincts (Jagd, Rudel, Territorial, Sexual)",
        "Erziehung - Training exercises",
        "Allgemein - General information",
        "Instinktveranlagung - Instinct predispositions"
    ]
    
    for collection in collections:
        print(f"  • {collection}")
    
    print("\n>>> # Get all collections")
    print(">>> collections = await service.get_collections()")
    print(">>> ")
    print(">>> # Check if collection exists")
    print(">>> exists = await service.collection_exists('Symptome')")
    print(">>> ")
    print(">>> # Count objects in collection")
    print(">>> count = await service.count_objects('Symptome')")


async def demo_symptom_search():
    """Demonstrate symptom search workflow"""
    print("\n\n🐕 SYMPTOM SEARCH WORKFLOW")
    print("-" * 60)
    
    print("Finding matches for dog behavior:")
    
    print("\n1. Direct search approach:")
    print(">>> # Search for behavior")
    print(">>> results = await weaviate.search(")
    print("...     collection='Symptome',")
    print("...     query='Mein Hund bellt wenn es klingelt',")
    print("...     limit=3,")
    print("...     properties=['beschreibung', 'schnelldiagnose']")
    print("... )")
    
    print("\n2. Compare with instincts:")
    print(">>> # Search each instinct")
    print(">>> instincts = ['jagd', 'rudel', 'territorial', 'sexual']")
    print(">>> for instinct in instincts:")
    print("...     results = await weaviate.search(")
    print("...         collection='Instinkte',")
    print("...         query=f'{symptom} {instinct}',")
    print("...         limit=1")
    print("...     )")
    
    print("\n3. Using convenience method:")
    print(">>> # Direct symptom match")
    print(">>> match = await weaviate.find_symptom_match('Bellen')")
    print(">>> if match:")
    print("...     print(f'Found: {match}')")


async def demo_health_monitoring():
    """Demonstrate health check functionality"""
    print("\n\n🏥 HEALTH MONITORING")
    print("-" * 60)
    
    # Mock health check response
    mock_health = {
        "healthy": True,
        "status": "connected",
        "details": {
            "url": "https://demo.weaviate.network",
            "collections_count": 5,
            "collections": ["Symptome", "Instinkte", "Erziehung", "Allgemein", "Instinktveranlagung"],
            "object_counts": {
                "Symptome": 150,
                "Instinkte": 4,
                "Erziehung": 75
            }
        }
    }
    
    print("Health check provides:")
    for key, value in mock_health.items():
        if isinstance(value, dict):
            print(f"\n{key}:")
            for k, v in value.items():
                if isinstance(v, dict):
                    print(f"  {k}:")
                    for kk, vv in v.items():
                        print(f"    {kk}: {vv}")
                else:
                    print(f"  {k}: {v}")
        else:
            print(f"{key}: {value}")


async def demo_testing():
    """Show testing approach"""
    print("\n\n🧪 TESTING APPROACH")
    print("-" * 60)
    
    print("Easy to mock for testing:")
    print("""
    # Mock search results
    mock_results = [
        {
            "id": "uuid-1",
            "properties": {
                "beschreibung": "Test behavior",
                "schnelldiagnose": "Test diagnosis"
            },
            "metadata": {"distance": 0.15}
        }
    ]
    
    # Mock the service
    mock_weaviate = Mock(spec=WeaviateService)
    mock_weaviate.search.return_value = mock_results
    
    # Test without real Weaviate
    results = await mock_weaviate.search("Symptome", "test")
    assert len(results) == 1
    """)


async def demo_no_caching():
    """Explain the no-caching approach"""
    print("\n\n🚫 NO BUILT-IN CACHING")
    print("-" * 60)
    
    print("Why no caching in the service?")
    print("- Enables prompt tuning in development")
    print("- Fresh results for every query")
    print("- Cache at orchestration layer when needed")
    
    print("\nDevelopment workflow:")
    print("1. Modify prompt in PromptManager")
    print("2. Query Weaviate - get fresh results")
    print("3. See immediate effect of changes")
    print("4. Iterate quickly")
    
    print("\nProduction caching (in orchestrator):")
    print(">>> # Check Redis cache first")
    print(">>> cache_key = f'weaviate:symptom:{query}'")
    print(">>> if cached := await redis.get(cache_key):")
    print("...     return cached")
    print(">>> ")
    print(">>> # Fresh search if not cached")
    print(">>> results = await weaviate.search(...)")
    print(">>> await redis.set(cache_key, results, ttl=3600)")


async def main():
    """Run all demos"""
    print("\n🚀 WuffChat V2 Weaviate Service Demo")
    print("=" * 60)
    
    await demo_old_vs_new()
    await demo_basic_usage()
    await demo_prompt_integration()
    await demo_collections()
    await demo_symptom_search()
    await demo_health_monitoring()
    await demo_testing()
    await demo_no_caching()
    
    print("\n\n✅ Demo complete!")
    print("\nKey improvements:")
    print("- Direct search control (no Query Agent)")
    print("- Generic, flexible interface")
    print("- Perfect for prompt tuning")
    print("- Easy to test with mocks")
    print("- Health monitoring included")
    print("- No hidden caching")


if __name__ == "__main__":
    asyncio.run(main())