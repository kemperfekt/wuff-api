# src/v2/core/flow_engine.py
"""
Flow Engine with proper FSM implementation for WuffChat V2.

This replaces the hardcoded state transitions in the current flow_orchestrator.py
with a maintainable, testable state machine pattern.
"""
from typing import Dict, Any, Callable, Optional, List, Tuple
from enum import Enum
from dataclasses import dataclass, field
import logging
from src.models.flow_models import FlowStep, AgentMessage

logger = logging.getLogger(__name__)


class TransitionEvent(str, Enum):
    """Events that trigger state transitions"""
    # Initial events
    START = "start"
    
    # User input events
    SYMPTOM_RECEIVED = "symptom_received"
    CONFIRMATION_YES = "confirmation_yes"
    CONFIRMATION_NO = "confirmation_no"
    CONTEXT_PROVIDED = "context_provided"
    EXERCISE_YES = "exercise_yes"
    EXERCISE_NO = "exercise_no"
    RESTART_YES = "restart_yes"
    RESTART_NO = "restart_no"
    
    # Feedback events
    FEEDBACK_PROVIDED = "feedback_provided"
    
    # Special events
    RESTART_COMMAND = "restart_command"
    ERROR = "error"


@dataclass
class StateTransition:
    """Represents a state transition in the FSM"""
    from_state: FlowStep
    event: TransitionEvent
    to_state: FlowStep
    condition: Optional[Callable[[Any], bool]] = None
    action: Optional[Callable[[Any], Any]] = None


@dataclass
class FlowContext:
    """Context passed through the flow"""
    session_id: str
    user_input: str = ""
    symptom: str = ""
    context: str = ""
    feedback_responses: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class FlowEngine:
    """
    FSM-based flow engine for managing conversation states.
    
    This engine:
    - Defines all possible state transitions
    - Validates transitions before executing
    - Provides hooks for state entry/exit actions
    - Maintains transition history for debugging
    """
    
    def __init__(self):
        self.transitions: Dict[Tuple[FlowStep, TransitionEvent], StateTransition] = {}
        self.state_entry_actions: Dict[FlowStep, Callable] = {}
        self.state_exit_actions: Dict[FlowStep, Callable] = {}
        self.transition_history: List[Tuple[FlowStep, TransitionEvent, FlowStep]] = []
        self._setup_transitions()
    
    def _setup_transitions(self):
        """Define all state transitions for the conversation flow"""
        
        # Initial flow
        self.add_transition(
            FlowStep.GREETING, 
            TransitionEvent.START,
            FlowStep.WAIT_FOR_SYMPTOM
        )
        
        # Symptom handling
        self.add_transition(
            FlowStep.WAIT_FOR_SYMPTOM,
            TransitionEvent.SYMPTOM_RECEIVED,
            FlowStep.WAIT_FOR_CONFIRMATION,
            condition=lambda ctx: len(ctx.user_input) >= 10
        )
        
        # Confirmation handling
        self.add_transition(
            FlowStep.WAIT_FOR_CONFIRMATION,
            TransitionEvent.CONFIRMATION_YES,
            FlowStep.WAIT_FOR_CONTEXT
        )
        
        self.add_transition(
            FlowStep.WAIT_FOR_CONFIRMATION,
            TransitionEvent.CONFIRMATION_NO,
            FlowStep.END_OR_RESTART
        )
        
        # Context handling
        self.add_transition(
            FlowStep.WAIT_FOR_CONTEXT,
            TransitionEvent.CONTEXT_PROVIDED,
            FlowStep.ASK_FOR_EXERCISE,
            condition=lambda ctx: len(ctx.user_input) >= 5
        )
        
        # Exercise handling
        self.add_transition(
            FlowStep.ASK_FOR_EXERCISE,
            TransitionEvent.EXERCISE_YES,
            FlowStep.END_OR_RESTART
        )
        
        self.add_transition(
            FlowStep.ASK_FOR_EXERCISE,
            TransitionEvent.EXERCISE_NO,
            FlowStep.FEEDBACK_Q1
        )
        
        # End or restart handling
        self.add_transition(
            FlowStep.END_OR_RESTART,
            TransitionEvent.RESTART_YES,
            FlowStep.WAIT_FOR_SYMPTOM
        )
        
        self.add_transition(
            FlowStep.END_OR_RESTART,
            TransitionEvent.RESTART_NO,
            FlowStep.FEEDBACK_Q1
        )
        
        # Feedback flow
        feedback_transitions = [
            (FlowStep.FEEDBACK_Q1, FlowStep.FEEDBACK_Q2),
            (FlowStep.FEEDBACK_Q2, FlowStep.FEEDBACK_Q3),
            (FlowStep.FEEDBACK_Q3, FlowStep.FEEDBACK_Q4),
            (FlowStep.FEEDBACK_Q4, FlowStep.FEEDBACK_Q5),
        ]
        
        for from_state, to_state in feedback_transitions:
            self.add_transition(
                from_state,
                TransitionEvent.FEEDBACK_PROVIDED,
                to_state
            )
        
        # Final feedback to greeting
        self.add_transition(
            FlowStep.FEEDBACK_Q5,
            TransitionEvent.FEEDBACK_PROVIDED,
            FlowStep.GREETING
        )
        
        # Global restart command (can be triggered from any state)
        for state in FlowStep:
            if state != FlowStep.GREETING:
                self.add_transition(
                    state,
                    TransitionEvent.RESTART_COMMAND,
                    FlowStep.GREETING
                )
    
    def add_transition(
        self, 
        from_state: FlowStep, 
        event: TransitionEvent,
        to_state: FlowStep,
        condition: Optional[Callable[[FlowContext], bool]] = None,
        action: Optional[Callable[[FlowContext], Any]] = None
    ):
        """Add a state transition to the FSM"""
        transition = StateTransition(
            from_state=from_state,
            event=event,
            to_state=to_state,
            condition=condition,
            action=action
        )
        
        key = (from_state, event)
        if key in self.transitions:
            logger.warning(f"Overwriting transition: {from_state} + {event}")
        
        self.transitions[key] = transition
    
    def add_state_entry_action(self, state: FlowStep, action: Callable):
        """Add an action to be executed when entering a state"""
        self.state_entry_actions[state] = action
    
    def add_state_exit_action(self, state: FlowStep, action: Callable):
        """Add an action to be executed when exiting a state"""
        self.state_exit_actions[state] = action
    
    def can_transition(
        self, 
        current_state: FlowStep, 
        event: TransitionEvent, 
        context: FlowContext
    ) -> bool:
        """Check if a transition is valid"""
        key = (current_state, event)
        
        if key not in self.transitions:
            return False
        
        transition = self.transitions[key]
        
        # Check condition if one exists
        if transition.condition:
            return transition.condition(context)
        
        return True
    
    def get_next_state(
        self, 
        current_state: FlowStep, 
        event: TransitionEvent
    ) -> Optional[FlowStep]:
        """Get the next state for a given current state and event"""
        key = (current_state, event)
        
        if key in self.transitions:
            return self.transitions[key].to_state
        
        return None
    
    def transition(
        self, 
        current_state: FlowStep, 
        event: TransitionEvent, 
        context: FlowContext
    ) -> Tuple[FlowStep, bool]:
        """
        Execute a state transition.
        
        Returns:
            Tuple of (new_state, success)
        """
        key = (current_state, event)
        
        # Check if transition exists
        if key not in self.transitions:
            logger.warning(f"No transition defined for {current_state} + {event}")
            return current_state, False
        
        transition = self.transitions[key]
        
        # Check condition
        if transition.condition and not transition.condition(context):
            logger.info(f"Transition condition failed for {current_state} + {event}")
            return current_state, False
        
        # Execute exit action for current state
        if current_state in self.state_exit_actions:
            try:
                self.state_exit_actions[current_state](context)
            except Exception as e:
                logger.error(f"Error in exit action for {current_state}: {e}")
        
        # Execute transition action if any
        if transition.action:
            try:
                transition.action(context)
            except Exception as e:
                logger.error(f"Error in transition action: {e}")
        
        # Update state
        new_state = transition.to_state
        
        # Execute entry action for new state
        if new_state in self.state_entry_actions:
            try:
                self.state_entry_actions[new_state](context)
            except Exception as e:
                logger.error(f"Error in entry action for {new_state}: {e}")
        
        # Record transition
        self.transition_history.append((current_state, event, new_state))
        
        logger.info(f"Transitioned from {current_state} to {new_state} via {event}")
        
        return new_state, True
    
    def get_possible_events(self, current_state: FlowStep) -> List[TransitionEvent]:
        """Get all possible events from the current state"""
        events = []
        
        for (state, event), transition in self.transitions.items():
            if state == current_state:
                events.append(event)
        
        return events
    
    def reset(self):
        """Reset the engine state"""
        self.transition_history.clear()
    
    def get_transition_graph(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Get a representation of the state machine for visualization.
        
        Returns:
            Dict mapping states to their possible transitions
        """
        graph = {}
        
        for (from_state, event), transition in self.transitions.items():
            state_name = from_state.value
            
            if state_name not in graph:
                graph[state_name] = []
            
            graph[state_name].append({
                "event": event.value,
                "to_state": transition.to_state.value,
                "has_condition": transition.condition is not None,
                "has_action": transition.action is not None
            })
        
        return graph


# Helper function to determine event from user input
def determine_event(
    current_state: FlowStep, 
    user_input: str, 
    context: FlowContext
) -> TransitionEvent:
    """
    Determine which event to trigger based on current state and user input.
    
    This function maps user input to appropriate events based on the current state.
    """
    user_input_lower = user_input.lower().strip()
    
    # Global restart commands
    if user_input_lower in ["neu", "restart", "von vorne"]:
        return TransitionEvent.RESTART_COMMAND
    
    # State-specific event determination
    if current_state == FlowStep.WAIT_FOR_SYMPTOM:
        if len(user_input) >= 10:
            return TransitionEvent.SYMPTOM_RECEIVED
    
    elif current_state == FlowStep.WAIT_FOR_CONFIRMATION:
        if "ja" in user_input_lower:
            return TransitionEvent.CONFIRMATION_YES
        elif "nein" in user_input_lower:
            return TransitionEvent.CONFIRMATION_NO
    
    elif current_state == FlowStep.WAIT_FOR_CONTEXT:
        if len(user_input) >= 5:
            return TransitionEvent.CONTEXT_PROVIDED
    
    elif current_state == FlowStep.ASK_FOR_EXERCISE:
        if "ja" in user_input_lower:
            return TransitionEvent.EXERCISE_YES
        elif "nein" in user_input_lower:
            return TransitionEvent.EXERCISE_NO
    
    elif current_state == FlowStep.END_OR_RESTART:
        if "ja" in user_input_lower:
            return TransitionEvent.RESTART_YES
        elif "nein" in user_input_lower:
            return TransitionEvent.RESTART_NO
    
    elif current_state in [
        FlowStep.FEEDBACK_Q1, FlowStep.FEEDBACK_Q2, 
        FlowStep.FEEDBACK_Q3, FlowStep.FEEDBACK_Q4, FlowStep.FEEDBACK_Q5
    ]:
        return TransitionEvent.FEEDBACK_PROVIDED
    
    # Default to error event if no match
    return TransitionEvent.ERROR