# tests/v2/core/test_flow_engine.py
"""
Unit tests for the V2 Flow Engine FSM implementation.

Run with: pytest tests/v2/core/test_flow_engine.py -v
"""
import pytest
from src.v2.core.flow_engine import (
    FlowEngine, FlowContext, TransitionEvent, determine_event
)
from src.models.flow_models import FlowStep


class TestFlowEngine:
    """Test the Flow Engine FSM implementation"""
    
    @pytest.fixture
    def engine(self):
        """Create a fresh engine instance for each test"""
        return FlowEngine()
    
    @pytest.fixture
    def context(self):
        """Create a test context"""
        return FlowContext(session_id="test-session")
    
    def test_initial_state_transitions(self, engine, context):
        """Test the initial greeting flow"""
        # Start from greeting
        current_state = FlowStep.GREETING
        
        # Should transition to WAIT_FOR_SYMPTOM
        new_state, success = engine.transition(
            current_state, 
            TransitionEvent.START, 
            context
        )
        
        assert success
        assert new_state == FlowStep.WAIT_FOR_SYMPTOM
    
    def test_symptom_flow(self, engine, context):
        """Test the symptom input flow"""
        # Start from WAIT_FOR_SYMPTOM
        current_state = FlowStep.WAIT_FOR_SYMPTOM
        context.user_input = "Mein Hund bellt ständig wenn andere Hunde vorbeigehen"
        
        # Should transition to WAIT_FOR_CONFIRMATION
        new_state, success = engine.transition(
            current_state,
            TransitionEvent.SYMPTOM_RECEIVED,
            context
        )
        
        assert success
        assert new_state == FlowStep.WAIT_FOR_CONFIRMATION
    
    def test_symptom_too_short(self, engine, context):
        """Test that short symptoms don't transition"""
        current_state = FlowStep.WAIT_FOR_SYMPTOM
        context.user_input = "bellt"  # Too short
        
        # Should not transition due to condition
        new_state, success = engine.transition(
            current_state,
            TransitionEvent.SYMPTOM_RECEIVED,
            context
        )
        
        assert not success
        assert new_state == current_state
    
    def test_confirmation_yes_flow(self, engine, context):
        """Test positive confirmation flow"""
        current_state = FlowStep.WAIT_FOR_CONFIRMATION
        
        new_state, success = engine.transition(
            current_state,
            TransitionEvent.CONFIRMATION_YES,
            context
        )
        
        assert success
        assert new_state == FlowStep.WAIT_FOR_CONTEXT
    
    def test_confirmation_no_flow(self, engine, context):
        """Test negative confirmation flow"""
        current_state = FlowStep.WAIT_FOR_CONFIRMATION
        
        new_state, success = engine.transition(
            current_state,
            TransitionEvent.CONFIRMATION_NO,
            context
        )
        
        assert success
        assert new_state == FlowStep.END_OR_RESTART
    
    def test_feedback_flow(self, engine, context):
        """Test the feedback question flow"""
        states = [
            FlowStep.FEEDBACK_Q1,
            FlowStep.FEEDBACK_Q2,
            FlowStep.FEEDBACK_Q3,
            FlowStep.FEEDBACK_Q4,
            FlowStep.FEEDBACK_Q5,
        ]
        
        for i, current_state in enumerate(states[:-1]):
            new_state, success = engine.transition(
                current_state,
                TransitionEvent.FEEDBACK_PROVIDED,
                context
            )
            
            assert success
            assert new_state == states[i + 1]
        
        # Last feedback should go back to greeting
        new_state, success = engine.transition(
            FlowStep.FEEDBACK_Q5,
            TransitionEvent.FEEDBACK_PROVIDED,
            context
        )
        
        assert success
        assert new_state == FlowStep.GREETING
    
    def test_restart_command(self, engine, context):
        """Test that restart command works from any state"""
        test_states = [
            FlowStep.WAIT_FOR_SYMPTOM,
            FlowStep.WAIT_FOR_CONFIRMATION,
            FlowStep.WAIT_FOR_CONTEXT,
            FlowStep.ASK_FOR_EXERCISE,
            FlowStep.FEEDBACK_Q3,
        ]
        
        for state in test_states:
            new_state, success = engine.transition(
                state,
                TransitionEvent.RESTART_COMMAND,
                context
            )
            
            assert success
            assert new_state == FlowStep.GREETING
    
    def test_invalid_transition(self, engine, context):
        """Test that invalid transitions are rejected"""
        # Try an undefined transition
        current_state = FlowStep.GREETING
        
        new_state, success = engine.transition(
            current_state,
            TransitionEvent.CONFIRMATION_YES,  # Invalid from GREETING
            context
        )
        
        assert not success
        assert new_state == current_state
    
    def test_transition_history(self, engine, context):
        """Test that transition history is recorded"""
        # Perform several transitions
        engine.transition(FlowStep.GREETING, TransitionEvent.START, context)
        engine.transition(FlowStep.WAIT_FOR_SYMPTOM, TransitionEvent.SYMPTOM_RECEIVED, context)
        
        # Check history
        assert len(engine.transition_history) == 2
        assert engine.transition_history[0] == (
            FlowStep.GREETING, 
            TransitionEvent.START, 
            FlowStep.WAIT_FOR_SYMPTOM
        )
    
    def test_get_possible_events(self, engine):
        """Test getting possible events from a state"""
        events = engine.get_possible_events(FlowStep.WAIT_FOR_CONFIRMATION)
        
        assert TransitionEvent.CONFIRMATION_YES in events
        assert TransitionEvent.CONFIRMATION_NO in events
        assert TransitionEvent.RESTART_COMMAND in events
        assert len(events) == 3
    
    def test_get_transition_graph(self, engine):
        """Test transition graph generation"""
        graph = engine.get_transition_graph()
        
        # Check that all states are represented
        assert FlowStep.GREETING.value in graph
        assert FlowStep.WAIT_FOR_SYMPTOM.value in graph
        
        # Check specific transitions
        greeting_transitions = graph[FlowStep.GREETING.value]
        assert any(t["event"] == TransitionEvent.START.value for t in greeting_transitions)


class TestDetermineEvent:
    """Test the event determination logic"""
    
    def test_determine_restart_event(self):
        """Test restart command detection"""
        context = FlowContext(session_id="test")
        
        for command in ["neu", "restart", "von vorne"]:
            event = determine_event(FlowStep.WAIT_FOR_SYMPTOM, command, context)
            assert event == TransitionEvent.RESTART_COMMAND
    
    def test_determine_symptom_event(self):
        """Test symptom event detection"""
        context = FlowContext(session_id="test")
        
        # Valid symptom
        event = determine_event(
            FlowStep.WAIT_FOR_SYMPTOM,
            "Mein Hund bellt ständig",
            context
        )
        assert event == TransitionEvent.SYMPTOM_RECEIVED
        
        # Too short
        event = determine_event(
            FlowStep.WAIT_FOR_SYMPTOM,
            "bellt",
            context
        )
        assert event == TransitionEvent.ERROR
    
    def test_determine_confirmation_events(self):
        """Test confirmation event detection"""
        context = FlowContext(session_id="test")
        
        # Yes
        event = determine_event(
            FlowStep.WAIT_FOR_CONFIRMATION,
            "Ja, gerne",
            context
        )
        assert event == TransitionEvent.CONFIRMATION_YES
        
        # No
        event = determine_event(
            FlowStep.WAIT_FOR_CONFIRMATION,
            "Nein danke",
            context
        )
        assert event == TransitionEvent.CONFIRMATION_NO
        
        # Unclear
        event = determine_event(
            FlowStep.WAIT_FOR_CONFIRMATION,
            "vielleicht",
            context
        )
        assert event == TransitionEvent.ERROR
    
    def test_determine_feedback_event(self):
        """Test feedback event detection"""
        context = FlowContext(session_id="test")
        
        for state in [FlowStep.FEEDBACK_Q1, FlowStep.FEEDBACK_Q2, FlowStep.FEEDBACK_Q3]:
            event = determine_event(state, "Meine Antwort", context)
            assert event == TransitionEvent.FEEDBACK_PROVIDED


# Run basic tests if executed directly
if __name__ == "__main__":
    engine = FlowEngine()
    context = FlowContext(session_id="test-direct")
    
    print("Testing basic flow...")
    
    # Test a simple flow
    state = FlowStep.GREETING
    print(f"Starting state: {state}")
    
    state, success = engine.transition(state, TransitionEvent.START, context)
    print(f"After START: {state} (success: {success})")
    
    context.user_input = "Mein Hund bellt ständig"
    state, success = engine.transition(state, TransitionEvent.SYMPTOM_RECEIVED, context)
    print(f"After SYMPTOM: {state} (success: {success})")
    
    # Print transition graph
    print("\nTransition Graph:")
    import json
    print(json.dumps(engine.get_transition_graph(), indent=2))
    
    print("\nBasic flow test completed!")