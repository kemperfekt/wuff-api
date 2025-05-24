# src/v2/demo.py
"""
Demo script to test V2 core components.

Run with: python -m src.v2.demo
"""
import asyncio
from src.v2.core.flow_engine import FlowEngine, FlowContext, TransitionEvent, determine_event
from src.v2.core.prompt_manager import get_prompt_manager
from src.models.flow_models import FlowStep


def print_separator():
    print("-" * 60)


async def demo_flow_engine():
    """Demonstrate the Flow Engine"""
    print("\n🔧 FLOW ENGINE DEMO")
    print_separator()
    
    engine = FlowEngine()
    context = FlowContext(session_id="demo-session")
    
    # Start the flow
    current_state = FlowStep.GREETING
    print(f"Initial state: {current_state.value}")
    
    # Transition through a typical flow
    transitions = [
        (TransitionEvent.START, "Starting conversation"),
        (TransitionEvent.SYMPTOM_RECEIVED, "User describes symptom"),
        (TransitionEvent.CONFIRMATION_YES, "User wants more info"),
        (TransitionEvent.CONTEXT_PROVIDED, "User provides context"),
        (TransitionEvent.EXERCISE_YES, "User wants exercise"),
        (TransitionEvent.RESTART_NO, "User doesn't want to restart"),
    ]
    
    # Set up context for conditions
    context.user_input = "Mein Hund bellt ständig wenn es klingelt"
    
    for event, description in transitions:
        print(f"\n→ {description} (Event: {event.value})")
        
        # For context event, set appropriate input
        if event == TransitionEvent.CONTEXT_PROVIDED:
            context.user_input = "Es passiert immer wenn Besuch kommt"
        
        new_state, success = engine.transition(current_state, event, context)
        
        if success:
            print(f"  ✓ Transitioned to: {new_state.value}")
            current_state = new_state
        else:
            print(f"  ✗ Transition failed, staying in: {current_state.value}")
    
    print(f"\nFinal state: {current_state.value}")
    print(f"Transition history has {len(engine.transition_history)} entries")


async def demo_prompt_manager():
    """Demonstrate the Prompt Manager"""
    print("\n📝 PROMPT MANAGER DEMO")
    print_separator()
    
    pm = get_prompt_manager()
    
    # List available prompts
    print("Available prompt categories:")
    categories = ["dog", "companion", "query", "validation", "error"]
    for category in categories:
        prompts = pm.list_prompts()
        category_prompts = [p for p in prompts if p.startswith(category)]
        print(f"  {category}: {len(category_prompts)} prompts")
    
    print("\nExample prompts:")
    
    # Get a simple prompt
    greeting = pm.get("dog.greeting")
    print(f"\n1. Simple prompt (dog.greeting):")
    print(f"   {greeting}")
    
    # Get a prompt with variables
    symptom = "Mein Hund bellt ständig"
    match = "Bellen ist oft ein Ausdruck von Aufregung oder Unsicherheit"
    
    perspective = pm.get(
        "dog.perspective",
        symptom=symptom,
        match=match
    )
    print(f"\n2. Prompt with variables (dog.perspective):")
    print(f"   {perspective[:100]}...")
    
    # Show prompt info
    info = pm.get_prompt_info("dog.instinct_diagnosis")
    print(f"\n3. Prompt information (dog.instinct_diagnosis):")
    print(f"   Variables: {info['variables']}")
    print(f"   Category: {info['category']}")
    print(f"   Version: {info['version']}")


async def demo_event_determination():
    """Demonstrate event determination from user input"""
    print("\n🎯 EVENT DETERMINATION DEMO")
    print_separator()
    
    test_cases = [
        (FlowStep.WAIT_FOR_SYMPTOM, "Mein Hund bellt ständig", "Valid symptom"),
        (FlowStep.WAIT_FOR_SYMPTOM, "bellt", "Too short symptom"),
        (FlowStep.WAIT_FOR_CONFIRMATION, "ja gerne", "Confirmation yes"),
        (FlowStep.WAIT_FOR_CONFIRMATION, "nein danke", "Confirmation no"),
        (FlowStep.WAIT_FOR_CONTEXT, "neu", "Restart command"),
        (FlowStep.FEEDBACK_Q1, "Sehr hilfreich", "Feedback response"),
    ]
    
    context = FlowContext(session_id="demo")
    
    for state, user_input, description in test_cases:
        event = determine_event(state, user_input, context)
        print(f"\n{description}:")
        print(f"  State: {state.value}")
        print(f"  Input: '{user_input}'")
        print(f"  → Event: {event.value}")


async def demo_integration():
    """Demonstrate how components work together"""
    print("\n🔗 INTEGRATION DEMO")
    print_separator()
    
    engine = FlowEngine()
    pm = get_prompt_manager()
    context = FlowContext(session_id="integration-demo")
    
    # Simulate a conversation flow
    print("Simulating a conversation flow:\n")
    
    # 1. Greeting
    current_state = FlowStep.GREETING
    greeting_prompt = pm.get("dog.greeting")
    print(f"Bot: {greeting_prompt}")
    
    # 2. User provides symptom
    current_state, _ = engine.transition(current_state, TransitionEvent.START, context)
    user_input = "Mein Hund zieht ständig an der Leine"
    print(f"\nUser: {user_input}")
    
    context.user_input = user_input
    event = determine_event(current_state, user_input, context)
    
    if engine.can_transition(current_state, event, context):
        current_state, _ = engine.transition(current_state, event, context)
        # Bot asks for confirmation
        confirm_prompt = pm.get("dog.ask_for_more")
        print(f"Bot: {confirm_prompt}")
    
    # 3. User confirms
    user_input = "ja"
    print(f"\nUser: {user_input}")
    
    event = determine_event(current_state, user_input, context)
    current_state, _ = engine.transition(current_state, event, context)
    
    # Bot asks for context
    context_prompt = pm.get("dog.ask_for_context")
    print(f"Bot: {context_prompt}")
    
    print(f"\n[Flow continues... Current state: {current_state.value}]")
    
    # Show possible next events
    possible_events = engine.get_possible_events(current_state)
    print(f"\nPossible events from {current_state.value}:")
    for event in possible_events:
        print(f"  - {event.value}")


async def main():
    """Run all demos"""
    print("\n🚀 WuffChat V2 Core Components Demo")
    print("=" * 60)
    
    await demo_flow_engine()
    await demo_prompt_manager()
    await demo_event_determination()
    await demo_integration()
    
    print("\n✅ Demo completed!")
    print("\nNext steps:")
    print("1. Run the tests: pytest tests/v2/core/test_flow_engine.py -v")
    print("2. Commit the changes")
    print("3. Move on to Phase 2: Prompt Extraction")


if __name__ == "__main__":
    asyncio.run(main())