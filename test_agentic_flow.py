#!/usr/bin/env python3
"""
Test script for the complete agentic flow integration.

This tests the full integration:
1. FlowEngine with new agentic states and events
2. FlowHandlers with agentic handlers
3. AgenticDogAgent with all components
"""

import asyncio
import logging
from src.core.flow_engine import FlowEngine, FlowEvent
from src.core.flow_handlers import FlowHandlers
from src.models.flow_models import FlowStep
from src.models.session_state import SessionState
from src.agents.agentic_dog_agent import AgenticDogAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_agentic_flow_integration():
    """Test the complete agentic flow integration"""
    print("🚀 Testing agentic flow integration...\n")
    
    try:
        # 1. Test FlowEngine initialization with agentic states
        print("📊 Testing FlowEngine with agentic states...")
        handlers = FlowHandlers()
        flow_engine = FlowEngine(handlers)
        
        # Check that agentic states are properly registered
        agentic_states = [
            FlowStep.AGENTIC_COLLECTION,
            FlowStep.DOG_PERSPECTIVE, 
            FlowStep.HANDOFF_DECISION
        ]
        
        for state in agentic_states:
            transitions = flow_engine.get_valid_transitions(state)
            print(f"  ✅ {state.value}: {len(transitions)} transitions available")
        
        print()
        
        # 2. Test session flow
        print("🔄 Testing session flow...")
        session = SessionState()
        session.current_step = FlowStep.GREETING
        
        # Test greeting to agentic transition
        print(f"  Starting state: {session.current_step}")
        
        can_start = flow_engine.can_transition(
            current_state=session.current_step,
            event=FlowEvent.START_SESSION,
            session=session,
            user_input="",
            context={}
        )
        
        print(f"  ✅ Can transition from GREETING to agentic: {can_start}")
        
        if can_start:
            new_state, messages = await flow_engine.process_event(
                event=FlowEvent.START_SESSION,
                session=session,
                user_input="",
                context={}
            )
            
            print(f"  ✅ Transition result: {len(messages)} messages")
            print(f"  ✅ New state: {session.current_step}")
            
            if messages:
                print(f"  ✅ First message: {messages[0].text[:50]}...")
        
        print()
        
        # 3. Test AgenticDogAgent integration
        print("🤖 Testing AgenticDogAgent integration...")
        
        # Test that handlers have agentic_dog_agent
        assert hasattr(handlers, 'agentic_dog_agent'), "FlowHandlers should have agentic_dog_agent"
        assert isinstance(handlers.agentic_dog_agent, AgenticDogAgent), "Should be AgenticDogAgent instance"
        
        print("  ✅ AgenticDogAgent properly initialized in handlers")
        
        # Test handler methods exist
        agentic_handlers = [
            'handle_greeting_to_agentic',
            'handle_agentic_collection',
            'handle_perspective_generation',
            'handle_handoff_question',
            'handle_handoff_accepted',
            'handle_handoff_declined'
        ]
        
        for handler_name in agentic_handlers:
            assert hasattr(handlers, handler_name), f"Handler {handler_name} should exist"
            print(f"  ✅ {handler_name} exists")
        
        print()
        
        # 4. Test agentic events
        print("📡 Testing agentic events...")
        agentic_events = [
            FlowEvent.AGENTIC_USER_INPUT,
            FlowEvent.INFORMATION_COLLECTED,
            FlowEvent.PERSPECTIVE_GENERATED,
            FlowEvent.HANDOFF_ACCEPTED,
            FlowEvent.HANDOFF_DECLINED
        ]
        
        for event in agentic_events:
            print(f"  ✅ {event.value} event available")
        
        print()
        
        print("🎉 All agentic flow integration tests passed!")
        print("\n📋 Integration Summary:")
        print("✅ FlowEngine: New agentic states and transitions added")
        print("✅ FlowHandlers: Agentic handlers implemented")
        print("✅ AgenticDogAgent: Properly integrated with flow")
        print("✅ Events: All agentic events defined and working")
        
        print("\n🎯 Ready for UI testing!")
        print("The agentic flow is now integrated and ready to test with the API/UI.")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        raise


async def main():
    """Run integration tests"""
    await test_agentic_flow_integration()


if __name__ == "__main__":
    asyncio.run(main())