# src/v2/migration_example.py
"""
Example showing how to migrate from old prompt usage to new V2 prompt system.

This demonstrates the changes needed in existing code.
"""

# ============================================================================
# OLD WAY (Current implementation)
# ============================================================================

def old_way_example():
    """Example of current prompt usage"""
    # From src/config/prompts.py
    from src.config.prompts import (
        DOG_PERSPECTIVE_TEMPLATE,
        INSTINCT_DIAGNOSIS_TEMPLATE,
        VALIDATE_BEHAVIOR_TEMPLATE
    )
    
    # Direct template usage
    prompt = DOG_PERSPECTIVE_TEMPLATE.format(
        symptom="Mein Hund bellt ständig",
        match="Bellen ist oft ein Ausdruck von Unsicherheit"
    )
    
    # From flow_orchestrator.py - hardcoded
    greeting = "Hallo! Schön, dass Du da bist. Ich erkläre Dir Hundeverhalten..."
    
    print("OLD WAY:")
    print(f"  - Import from multiple files")
    print(f"  - Direct string formatting")
    print(f"  - Hardcoded strings in code")


# ============================================================================
# NEW WAY (V2 implementation)
# ============================================================================

def new_way_example():
    """Example of V2 prompt usage"""
    # Single import
    from src.v2.core.prompt_manager import get_prompt_manager
    
    # Get prompt manager instance
    pm = get_prompt_manager()
    
    # Get prompts by key with automatic formatting
    greeting = pm.get("dog.greeting")
    
    dog_perspective = pm.get(
        "generation.dog_perspective",
        symptom="Mein Hund bellt ständig",
        match="Bellen ist oft ein Ausdruck von Unsicherheit"
    )
    
    validation_prompt = pm.get(
        "validation.validate.behavior.template",
        text="Mein Hund bellt ständig"
    )
    
    print("\nNEW WAY:")
    print(f"  - Single import point")
    print(f"  - Centralized management")
    print(f"  - Type-safe with validation")
    print(f"  - Easy to find and modify")


# ============================================================================
# MIGRATION MAPPING
# ============================================================================

def show_migration_mapping():
    """Show how to map old imports to new keys"""
    
    print("\n\nMIGRATION MAPPING:")
    print("-" * 60)
    
    mappings = {
        # From src/config/prompts.py
        "DOG_PERSPECTIVE_TEMPLATE": "generation.dog_perspective",
        "EXERCISE_TEMPLATE": "generation.exercise",
        "INSTINCT_DIAGNOSIS_TEMPLATE": "generation.instinct_diagnosis",
        "VALIDATE_BEHAVIOR_TEMPLATE": "validation.validate.behavior.template",
        
        # From hardcoded in flow_orchestrator.py
        '"Hallo! Schön, dass Du da bist..."': "dog.greeting",
        '"Kannst Du das Verhalten bitte..."': "dog.need.more.detail",
        '"Magst Du mehr erfahren..."': "dog.ask.for.more",
        
        # From companion_agent.py
        "self.feedback_questions[0]": "companion.feedback.q1",
        "self.feedback_questions[1]": "companion.feedback.q2",
        
        # Query templates
        "DOG_PERSPECTIVE_QUERY_TEMPLATE": "query.dog_perspective",
        "INSTINCT_ANALYSIS_QUERY_TEMPLATE": "query.instinct_analysis",
        "COMBINED_INSTINCT_QUERY_TEMPLATE": "query.combined_instinct",
    }
    
    for old, new in mappings.items():
        print(f"  {old:<45} → pm.get('{new}')")


# ============================================================================
# PRACTICAL EXAMPLES
# ============================================================================

def migration_in_practice():
    """Show practical migration examples"""
    from src.v2.core.prompt_manager import get_prompt_manager
    pm = get_prompt_manager()
    
    print("\n\nPRACTICAL MIGRATION EXAMPLES:")
    print("-" * 60)
    
    # Example 1: Simple prompt
    print("\n1. Simple prompt (no variables):")
    print("   OLD: greeting = 'Hallo! Schön, dass Du da bist...'")
    print("   NEW: greeting = pm.get('dog.greeting')")
    
    # Example 2: Prompt with variables
    print("\n2. Prompt with variables:")
    print("   OLD: prompt = DOG_PERSPECTIVE_TEMPLATE.format(symptom=s, match=m)")
    print("   NEW: prompt = pm.get('generation.dog_perspective', symptom=s, match=m)")
    
    # Example 3: Checking available prompts
    print("\n3. Finding prompts:")
    print("   List all dog prompts: pm.list_prompts(PromptCategory.DOG)")
    print("   Get prompt info: pm.get_prompt_info('dog.greeting')")
    
    # Example 4: Error handling
    print("\n4. Error handling:")
    try:
        pm.get("nonexistent.prompt")
    except Exception as e:
        print(f"   Error caught: {e}")


if __name__ == "__main__":
    print("🔄 V2 PROMPT MIGRATION GUIDE")
    print("=" * 60)
    
    old_way_example()
    new_way_example()
    show_migration_mapping()
    migration_in_practice()
    
    print("\n\n✅ Migration guide complete!")
    print("\nTo migrate your code:")
    print("1. Replace imports with: from src.v2.core.prompt_manager import get_prompt_manager")
    print("2. Get instance: pm = get_prompt_manager()")
    print("3. Replace template usage with: pm.get('key', **variables)")
    print("4. Use the mapping above to find the right keys")