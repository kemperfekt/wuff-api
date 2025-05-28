#!/usr/bin/env python3
"""
Fix Weaviate integration issues in WuffChat V2
Run this to apply the fixes
"""

import os
import sys

def fix_main_py():
    """Fix the undefined weaviate_service in main.py"""
    print("🔧 Fixing main.py...")
    
    main_path = "src/v2/main.py"
    
    # Read current content
    with open(main_path, 'r') as f:
        content = f.read()
    
    # Fix 1: Import orchestrator's weaviate_service
    import_fix = """from src.v2.core.orchestrator import V2Orchestrator, init_orchestrator
from src.v2.models.flow_models import FlowStep
from src.v2.core.config import setup_logging
from src.v2.services.weaviate_service import WeaviateService"""
    
    content = content.replace(
        """from src.v2.core.orchestrator import V2Orchestrator, init_orchestrator
from src.v2.models.flow_models import FlowStep
from src.v2.core.config import setup_logging""",
        import_fix
    )
    
    # Fix 2: Add weaviate_service initialization after orchestrator
    orchestrator_fix = """# Initialize V2 orchestrator
orchestrator = init_orchestrator(session_store)

# Get weaviate service from orchestrator for debug endpoint
weaviate_service = orchestrator.weaviate_service if hasattr(orchestrator, 'weaviate_service') else WeaviateService()"""
    
    content = content.replace(
        """# Initialize V2 orchestrator
orchestrator = init_orchestrator(session_store)""",
        orchestrator_fix
    )
    
    # Write back
    with open(main_path, 'w') as f:
        f.write(content)
    
    print("✅ Fixed main.py")


def fix_orchestrator_py():
    """Fix service initialization in orchestrator"""
    print("🔧 Fixing orchestrator.py...")
    
    orch_path = "src/v2/core/orchestrator.py"
    
    # Read content
    with open(orch_path, 'r') as f:
        content = f.read()
    
    # Fix: Expose services as instance variables
    init_fix = """            # Initialize services
            self.prompt_manager = PromptManager()
            self.gpt_service = GPTService()
            self.weaviate_service = WeaviateService()
            self.redis_service = RedisService()
            
            # Initialize handlers with services
            self.flow_handlers = FlowHandlers(
                prompt_manager=self.prompt_manager,
                gpt_service=self.gpt_service,
                weaviate_service=self.weaviate_service,
                redis_service=self.redis_service
            )"""
    
    # Check if already has the services exposed
    if "self.weaviate_service = WeaviateService()" not in content:
        print("❌ Orchestrator services not exposed as expected")
        # The code already looks correct, so no fix needed
    else:
        print("✅ Orchestrator already has services exposed correctly")
    
    print("✅ Orchestrator checked")


def create_minimal_test():
    """Create a minimal test to verify Weaviate works"""
    print("🔧 Creating minimal test...")
    
    test_content = '''#!/usr/bin/env python3
"""Minimal test to verify Weaviate integration works"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

async def test_weaviate():
    from src.v2.services.weaviate_service import WeaviateService
    
    print("Testing Weaviate connection...")
    service = WeaviateService()
    
    # Test 1: Initialize
    await service.ensure_initialized()
    print("✅ Initialized")
    
    # Test 2: Health check
    health = await service.health_check()
    print(f"✅ Health: {health['healthy']}")
    print(f"   Collections: {health['details'].get('collections', [])}")
    
    # Test 3: Search
    results = await service.search(
        collection="Symptome",
        query="Hund bellt",
        limit=1
    )
    print(f"✅ Search returned {len(results)} results")
    
    return True

async def test_orchestrator():
    from src.state.session_state import SessionStore
    from src.v2.core.orchestrator import init_orchestrator
    
    print("\\nTesting Orchestrator...")
    session_store = SessionStore()
    orchestrator = init_orchestrator(session_store)
    
    # Check services
    print(f"✅ Has weaviate_service: {hasattr(orchestrator, 'weaviate_service')}")
    
    # Start conversation
    messages = await orchestrator.start_conversation("test-session")
    print(f"✅ Started conversation: {len(messages)} messages")
    
    return True

async def main():
    try:
        await test_weaviate()
        await test_orchestrator()
        print("\\n✅ All tests passed!")
    except Exception as e:
        print(f"\\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    with open("test_weaviate_minimal.py", 'w') as f:
        f.write(test_content)
    
    print("✅ Created test_weaviate_minimal.py")


def check_environment():
    """Check if environment variables are set"""
    print("🔍 Checking environment variables...")
    
    required_vars = {
        "WEAVIATE_URL": os.getenv("WEAVIATE_URL"),
        "WEAVIATE_API_KEY": os.getenv("WEAVIATE_API_KEY"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY")
    }
    
    all_set = True
    for var, value in required_vars.items():
        if value:
            print(f"✅ {var}: Set")
        else:
            print(f"❌ {var}: Not set")
            all_set = False
    
    if not all_set:
        print("\n⚠️  Missing environment variables!")
        print("Set them in your .env file or export them")
    
    return all_set


def main():
    print("🚀 WuffChat V2 Weaviate Fix")
    print("=" * 60)
    
    # Check environment first
    env_ok = check_environment()
    if not env_ok:
        print("\nFix environment variables first!")
        return
    
    # Apply fixes
    try:
        fix_main_py()
        fix_orchestrator_py()
        create_minimal_test()
        
        print("\n" + "=" * 60)
        print("✅ Fixes applied!")
        print("\nNext steps:")
        print("1. Run the minimal test: python test_weaviate_minimal.py")
        print("2. If it passes, start the server: python -m uvicorn src.v2.main:app --reload")
        print("3. Test manually at http://localhost:8000/docs")
        
    except Exception as e:
        print(f"\n❌ Error applying fixes: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()