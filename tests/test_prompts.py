# tests/v2/test_prompts.py
"""
Test that all prompts are loading correctly from the new structure.

Run with: python tests/v2/test_prompts.py
"""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.core.prompt_manager import get_prompt_manager, PromptCategory


def test_prompt_loading():
    """Test that prompts load correctly from files"""
    print("🧪 Testing Prompt Loading...")
    print("-" * 60)
    
    pm = get_prompt_manager()
    
    # Count prompts by category
    categories = {}
    for prompt_key in pm.list_prompts():
        prompt = pm.prompts[prompt_key]
        cat = prompt.category.value
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"\n✅ Loaded {len(pm.prompts)} prompts total:")
    for cat, count in sorted(categories.items()):
        print(f"   {cat}: {count} prompts")
    
    # Test some key prompts
    print("\n🔍 Testing key prompts:")
    
    test_cases = [
        ("dog.greeting", {}),
        ("dog.ask.for.more", {}),
        ("generation.dog_perspective", {"symptom": "Test", "match": "Test match"}),
        ("query.symptom", {"symptom": "Bellen"}),
        ("companion.feedback.intro", {}),
        ("validation.validate.behavior.template", {"text": "Mein Hund bellt"}),
    ]
    
    for key, vars in test_cases:
        try:
            result = pm.get(key, **vars)
            print(f"   ✅ {key}: {result[:50]}...")
        except Exception as e:
            print(f"   ❌ {key}: {e}")
    
    # List all available keys
    print("\n📋 All available prompt keys:")
    for key in sorted(pm.list_prompts()):
        info = pm.get_prompt_info(key)
        vars_str = f" (vars: {', '.join(info['variables'])})" if info['variables'] else ""
        print(f"   - {key}{vars_str}")


def test_prompt_categories():
    """Test prompts by category"""
    print("\n\n🏷️  Testing Prompts by Category")
    print("-" * 60)
    
    pm = get_prompt_manager()
    
    for category in PromptCategory:
        prompts = pm.list_prompts(category)
        print(f"\n{category.value.upper()} ({len(prompts)} prompts):")
        for key in sorted(prompts)[:5]:  # Show first 5
            print(f"   - {key}")
        if len(prompts) > 5:
            print(f"   ... and {len(prompts) - 5} more")


def test_old_vs_new_mapping():
    """Show mapping between old and new prompt keys"""
    print("\n\n🔄 Old vs New Prompt Key Mapping")
    print("-" * 60)
    
    mappings = [
        ("Old: DOG_PERSPECTIVE_TEMPLATE", "New: generation.dog_perspective"),
        ("Old: INSTINCT_DIAGNOSIS_TEMPLATE", "New: generation.instinct_diagnosis"),
        ("Old: EXERCISE_TEMPLATE", "New: generation.exercise"),
        ("Old: VALIDATE_BEHAVIOR_TEMPLATE", "New: validation.validate.behavior.template"),
        ("Old: feedback_questions[0]", "New: companion.feedback.q1"),
    ]
    
    for old, new in mappings:
        print(f"   {old} → {new}")


if __name__ == "__main__":
    test_prompt_loading()
    test_prompt_categories()
    test_old_vs_new_mapping()
    
    print("\n\n✅ Prompt testing complete!")
    print("\nNext steps:")
    print("1. Update existing code to use new prompt keys")
    print("2. Remove old prompt imports")
    print("3. Test the flow with new prompts")