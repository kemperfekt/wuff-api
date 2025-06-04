# src/v2/core/flow_engine.py
"""
V2 Flow Engine - Complete FSM-based flow control with handler integration.

This replaces the hardcoded flow logic from V1 with a proper finite state machine
that uses V2 services and agents through clean handlers.
"""

from typing import Dict, List, Optional, Any, Callable, Awaitable
from enum import Enum
from dataclasses import dataclass
import logging

from src.models.flow_models import FlowStep
from src.models.session_state import SessionState
from src.agents.base_agent import V2AgentMessage
from src.core.exceptions import V2FlowError, V2ValidationError
from src.core.flow_handlers import FlowHandlers

logger = logging.getLogger(__name__)

# Type definitions for cleaner code
TransitionHandler = Callable[[SessionState, str, Dict[str, Any]], Awaitable[List[V2AgentMessage]]]
TransitionCondition = Callable[[SessionState, str, Dict[str, Any]], bool]


class FlowEvent(str, Enum):
    """Events that can trigger state transitions"""
    
    # User input events
    USER_INPUT = "user_input"
    YES_RESPONSE = "yes_response"  # "ja"
    NO_RESPONSE = "no_response"   # "nein"
    
    # System events
    SYMPTOM_FOUND = "symptom_found"
    SYMPTOM_NOT_FOUND = "symptom_not_found"
    CONTEXT_RECEIVED = "context_received"
    EXERCISE_REQUESTED = "exercise_requested"
    EXERCISE_DECLINED = "exercise_declined"
    
    # Special commands
    RESTART_COMMAND = "restart_command"  # "neu", "restart", "von vorne"
    
    # Feedback events
    FEEDBACK_ANSWER = "feedback_answer"
    FEEDBACK_COMPLETE = "feedback_complete"
    
    # Flow control
    START_SESSION = "start_session"
    CONTINUE_FLOW = "continue_flow"


@dataclass
class Transition:
    """Represents a state transition"""
    from_state: FlowStep
    event: FlowEvent
    to_state: FlowStep
    condition: Optional[TransitionCondition] = None
    handler: Optional[TransitionHandler] = None
    description: str = ""


class FlowEngine:
    """
    Complete FSM-based flow engine with V2 integration.
    
    This engine:
    1. Defines all valid state transitions explicitly
    2. Processes events and triggers appropriate transitions
    3. Uses FlowHandlers for business logic
    4. Coordinates V2 agents and services
    """
    
    def __init__(self, flow_handlers: Optional[FlowHandlers] = None):
        """
        Initialize flow engine with handlers.
        
        Args:
            flow_handlers: Handler instance for business logic
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize handlers
        self.handlers = flow_handlers or FlowHandlers()
        
        # Store all defined transitions
        self.transitions: List[Transition] = []
        
        # Quick lookup: {(state, event): Transition}
        self._transition_map: Dict[tuple, Transition] = {}
        
        # Initialize all transitions with handlers
        self._setup_transitions()
        
        # Build lookup map
        self._build_transition_map()
        
        logger.info("V2 FlowEngine initialized with complete handler integration")
    
    def _setup_transitions(self):
        """Define all state transitions with their corresponding handlers"""
        
        # ===========================================
        # GREETING TRANSITIONS
        # ===========================================
        
        self.add_transition(
            from_state=FlowStep.GREETING,
            event=FlowEvent.START_SESSION,
            to_state=FlowStep.WAIT_FOR_SYMPTOM,
            handler=self.handlers.handle_greeting,
            description="Initial greeting -> wait for symptom description"
        )
        
        # ===========================================
        # SYMPTOM INPUT TRANSITIONS  
        # ===========================================
        
        self.add_transition(
            from_state=FlowStep.WAIT_FOR_SYMPTOM,
            event=FlowEvent.USER_INPUT,
            to_state=FlowStep.WAIT_FOR_CONFIRMATION,
            handler=self._handle_symptom_wrapper,
            description="Process symptom input and determine if match found"
        )
        
        # ===========================================
        # CONFIRMATION TRANSITIONS
        # ===========================================
        
        self.add_transition(
            from_state=FlowStep.WAIT_FOR_CONFIRMATION,
            event=FlowEvent.USER_INPUT,
            to_state=FlowStep.WAIT_FOR_CONTEXT,
            handler=self.handlers.handle_confirmation,
            description="Process confirmation response"
        )
        
        # ===========================================
        # CONTEXT INPUT TRANSITIONS
        # ===========================================
        
        self.add_transition(
            from_state=FlowStep.WAIT_FOR_CONTEXT,
            event=FlowEvent.USER_INPUT,
            to_state=FlowStep.ASK_FOR_EXERCISE,
            handler=self.handlers.handle_context_input,
            description="Process context and provide instinct analysis"
        )
        
        # ===========================================
        # EXERCISE OFFER TRANSITIONS
        # ===========================================
        
        self.add_transition(
            from_state=FlowStep.ASK_FOR_EXERCISE,
            event=FlowEvent.YES_RESPONSE,
            to_state=FlowStep.END_OR_RESTART,
            handler=self.handlers.handle_exercise_request,
            description="User wants exercise -> provide exercise and offer restart"
        )
        
        self.add_transition(
            from_state=FlowStep.ASK_FOR_EXERCISE,
            event=FlowEvent.NO_RESPONSE,
            to_state=FlowStep.FEEDBACK_Q1,
            handler=self._handle_exercise_declined,
            description="User doesn't want exercise -> start feedback"
        )
        
        # ===========================================
        # END/RESTART TRANSITIONS
        # ===========================================
        
        self.add_transition(
            from_state=FlowStep.END_OR_RESTART,
            event=FlowEvent.YES_RESPONSE,
            to_state=FlowStep.WAIT_FOR_SYMPTOM,
            handler=self._handle_restart_yes,
            description="User wants another behavior -> restart conversation"
        )
        
        self.add_transition(
            from_state=FlowStep.END_OR_RESTART,
            event=FlowEvent.NO_RESPONSE,
            to_state=FlowStep.FEEDBACK_Q1,
            handler=self._handle_restart_no,
            description="User wants to end -> start feedback collection"
        )
        
        # ===========================================
        # FEEDBACK SEQUENCE TRANSITIONS
        # ===========================================
        
        self.add_transition(
            from_state=FlowStep.FEEDBACK_Q1,
            event=FlowEvent.FEEDBACK_ANSWER,
            to_state=FlowStep.FEEDBACK_Q2,
            handler=self._handle_feedback_q1,
            description="First feedback answer -> second question"
        )
        
        self.add_transition(
            from_state=FlowStep.FEEDBACK_Q2,
            event=FlowEvent.FEEDBACK_ANSWER,
            to_state=FlowStep.FEEDBACK_Q3,
            handler=self._handle_feedback_q2,
            description="Second feedback answer -> third question"
        )
        
        self.add_transition(
            from_state=FlowStep.FEEDBACK_Q3,
            event=FlowEvent.FEEDBACK_ANSWER,
            to_state=FlowStep.FEEDBACK_Q4,
            handler=self._handle_feedback_q3,
            description="Third feedback answer -> fourth question"
        )
        
        self.add_transition(
            from_state=FlowStep.FEEDBACK_Q4,
            event=FlowEvent.FEEDBACK_ANSWER,
            to_state=FlowStep.FEEDBACK_Q5,
            handler=self._handle_feedback_q4,
            description="Fourth feedback answer -> fifth question"
        )
        
        self.add_transition(
            from_state=FlowStep.FEEDBACK_Q5,
            event=FlowEvent.FEEDBACK_COMPLETE,
            to_state=FlowStep.GREETING,
            handler=self.handlers.handle_feedback_completion,
            description="Final feedback answer -> thank user and restart"
        )
        
        # ===========================================
        # UNIVERSAL RESTART TRANSITIONS
        # ===========================================
        
        restart_states = [
            FlowStep.GREETING, FlowStep.WAIT_FOR_SYMPTOM, FlowStep.WAIT_FOR_CONFIRMATION,
            FlowStep.WAIT_FOR_CONTEXT, FlowStep.ASK_FOR_EXERCISE, FlowStep.END_OR_RESTART,
            FlowStep.FEEDBACK_Q1, FlowStep.FEEDBACK_Q2, FlowStep.FEEDBACK_Q3, 
            FlowStep.FEEDBACK_Q4, FlowStep.FEEDBACK_Q5
        ]
        
        for state in restart_states:
            self.add_transition(
                from_state=state,
                event=FlowEvent.RESTART_COMMAND,
                to_state=FlowStep.WAIT_FOR_SYMPTOM,
                handler=self._handle_restart_command,
                description=f"Restart command from {state.value} -> new conversation"
            )
    
    # ===========================================
    # HANDLER WRAPPERS
    # ===========================================
    
    async def _handle_symptom_wrapper(
        self, 
        session: SessionState, 
        user_input: str, 
        context: Dict[str, Any]
    ) -> List[V2AgentMessage]:
        """
        Wrapper for symptom input that handles event determination.
        
        This calls the handler and then determines the next event based on the result.
        """
        try:
            # Call the actual handler
            result = await self.handlers.handle_symptom_input(session, user_input, context)
            
            # Handle the tuple return (next_event_string, messages)
            if isinstance(result, tuple) and len(result) == 2:
                next_event_string, messages = result
                
                # Set the next_event in context based on the string returned
                if next_event_string == 'symptom_found':
                    # Match was found, proceeding to confirmation
                    context['next_event'] = 'symptom_found'
                elif next_event_string in ['symptom_not_found', 'stay_in_state']:
                    # No match found, staying in current state
                    context['next_event'] = 'symptom_not_found'
                else:
                    # Unknown event, default to not found
                    logger.warning(f"Unknown event string from symptom handler: {next_event_string}")
                    context['next_event'] = 'symptom_not_found'
                
                return messages
            else:
                # If handler returns just messages (shouldn't happen)
                logger.warning("handle_symptom_input didn't return expected tuple format")
                return result if isinstance(result, list) else []
            
        except V2FlowError:
            # Re-raise V2FlowError as is to preserve messages
            raise
        except V2ValidationError:
            # Re-raise V2ValidationError as is to preserve validation details
            raise
        except Exception as e:
            logger.error(f"Error in symptom wrapper: {e}")
            raise
    
    
    async def _handle_confirmation_yes(
        self, 
        session: SessionState, 
        user_input: str, 
        context: Dict[str, Any]
    ) -> List[V2AgentMessage]:
        """Handle user saying yes to learning more."""
        from src.agents.base_agent import AgentContext, MessageType
        
        agent_context = AgentContext(
            session_id=session.session_id,
            message_type=MessageType.QUESTION,
            metadata={'question_type': 'context'}
        )
        
        return await self.handlers.dog_agent.respond(agent_context)
    
    async def _handle_confirmation_no(
        self, 
        session: SessionState, 
        user_input: str, 
        context: Dict[str, Any]
    ) -> List[V2AgentMessage]:
        """Handle user saying no to learning more."""
        from src.agents.base_agent import AgentContext, MessageType
        
        agent_context = AgentContext(
            session_id=session.session_id,
            message_type=MessageType.QUESTION,
            metadata={'question_type': 'restart'}
        )
        
        return await self.handlers.dog_agent.respond(agent_context)
    
    
    async def _handle_exercise_declined(
        self, 
        session: SessionState, 
        user_input: str, 
        context: Dict[str, Any]
    ) -> List[V2AgentMessage]:
        """Handle user declining exercise - start feedback."""
        return await self.handlers.handle_feedback_question(
            session, user_input, {'question_number': 1}
        )
    
    async def _handle_restart_yes(
        self, 
        session: SessionState, 
        user_input: str, 
        context: Dict[str, Any]
    ) -> List[V2AgentMessage]:
        """Handle user wanting to restart."""
        from src.agents.base_agent import AgentContext, MessageType
        
        # Clear previous symptom
        session.active_symptom = ""
        
        agent_context = AgentContext(
            session_id=session.session_id,
            message_type=MessageType.INSTRUCTION,
            metadata={'instruction_type': 'describe_more'}
        )
        
        return await self.handlers.dog_agent.respond(agent_context)
    
    async def _handle_restart_no(
        self, 
        session: SessionState, 
        user_input: str, 
        context: Dict[str, Any]
    ) -> List[V2AgentMessage]:
        """Handle user not wanting to restart - go to feedback."""
        return await self.handlers.handle_feedback_question(
            session, user_input, {'question_number': 1}
        )
    
    async def _handle_restart_command(
        self, 
        session: SessionState, 
        user_input: str, 
        context: Dict[str, Any]
    ) -> List[V2AgentMessage]:
        """Handle restart command from any state."""
        from src.agents.base_agent import AgentContext, MessageType
        
        # Clear session state
        session.active_symptom = ""
        if hasattr(session, 'feedback'):
            session.feedback = []
        
        agent_context = AgentContext(
            session_id=session.session_id,
            message_type=MessageType.RESPONSE,
            metadata={'response_mode': 'perspective_only'}
        )
        
        return await self.handlers.dog_agent.respond(agent_context)
    
    # Feedback handlers
    async def _handle_feedback_q1(self, session: SessionState, user_input: str, context: Dict[str, Any]) -> List[V2AgentMessage]:
        """Handle feedback Q1 -> Q2"""
        await self.handlers.handle_feedback_answer(session, user_input, context)
        return await self.handlers.handle_feedback_question(session, "", {'question_number': 2})
    
    async def _handle_feedback_q2(self, session: SessionState, user_input: str, context: Dict[str, Any]) -> List[V2AgentMessage]:
        """Handle feedback Q2 -> Q3"""
        await self.handlers.handle_feedback_answer(session, user_input, context)
        return await self.handlers.handle_feedback_question(session, "", {'question_number': 3})
    
    async def _handle_feedback_q3(self, session: SessionState, user_input: str, context: Dict[str, Any]) -> List[V2AgentMessage]:
        """Handle feedback Q3 -> Q4"""
        await self.handlers.handle_feedback_answer(session, user_input, context)
        return await self.handlers.handle_feedback_question(session, "", {'question_number': 4})
    
    async def _handle_feedback_q4(self, session: SessionState, user_input: str, context: Dict[str, Any]) -> List[V2AgentMessage]:
        """Handle feedback Q4 -> Q5"""
        await self.handlers.handle_feedback_answer(session, user_input, context)
        return await self.handlers.handle_feedback_question(session, "", {'question_number': 5})
    
    # ===========================================
    # CORE FSM METHODS
    # ===========================================
    
    def add_transition(
        self,
        from_state: FlowStep,
        event: FlowEvent,
        to_state: FlowStep,
        condition: Optional[TransitionCondition] = None,
        handler: Optional[TransitionHandler] = None,
        description: str = ""
    ):
        """Add a new transition to the FSM"""
        transition = Transition(
            from_state=from_state,
            event=event,
            to_state=to_state,
            condition=condition,
            handler=handler,
            description=description
        )
        self.transitions.append(transition)
    
    def _build_transition_map(self):
        """Build fast lookup map for transitions"""
        self._transition_map.clear()
        
        for transition in self.transitions:
            key = (transition.from_state, transition.event)
            
            # Handle multiple transitions for same state/event (conditions will resolve)
            if key in self._transition_map:
                self.logger.warning(
                    f"Multiple transitions for {transition.from_state.value} + {transition.event.value}. "
                    f"Using conditions to resolve."
                )
            
            self._transition_map[key] = transition
    
    def get_valid_transitions(self, current_state: FlowStep) -> List[Transition]:
        """Get all valid transitions from current state"""
        return [t for t in self.transitions if t.from_state == current_state]
    
    def can_transition(
        self, 
        current_state: FlowStep, 
        event: FlowEvent, 
        session: SessionState,
        user_input: str = "",
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if a transition is valid"""
        key = (current_state, event)
        
        if key not in self._transition_map:
            return False
        
        transition = self._transition_map[key]
        
        # Check condition if present
        if transition.condition:
            return transition.condition(session, user_input, context or {})
        
        return True
    
    async def process_event(
        self,
        session: SessionState,
        event: FlowEvent,
        user_input: str = "",
        context: Optional[Dict[str, Any]] = None
    ) -> tuple[FlowStep, List[V2AgentMessage]]:
        """
        Process an event and execute the appropriate transition.
        
        Args:
            session: Current session state
            event: Event to process
            user_input: User's input (if any)
            context: Additional context data
            
        Returns:
            Tuple of (new_state, messages)
            
        Raises:
            V2FlowError: If transition is invalid or fails
        """
        current_state = session.current_step
        context = context or {}
        
        self.logger.info(f"Processing event {event.value} from state {current_state.value}")
        
        # Check if transition is valid
        if not self.can_transition(current_state, event, session, user_input, context):
            valid_events = [t.event.value for t in self.get_valid_transitions(current_state)]
            logger.warning(f"Invalid transition: {current_state.value} + {event.value}. Valid events: {valid_events}")
            raise V2FlowError(
                current_state=current_state.value,
                message=f"Invalid transition: {current_state.value} + {event.value}. Valid events: {valid_events}"
            )
        
        # Get the transition
        key = (current_state, event)
        transition = self._transition_map[key]
        
        try:
            # Execute transition handler if present
            messages = []
            if transition.handler:
                result = await transition.handler(session, user_input, context)
                
                # Handle different return types
                if isinstance(result, tuple) and len(result) == 2:
                    # Handler returns (next_state, messages) - e.g., for confirmation
                    next_state, messages = result
                    
                    if next_state == 'stay_in_state':
                        # Stay in current state
                        self.logger.info(f"Handler requested staying in current state: {current_state.value}")
                        return current_state, messages
                    elif isinstance(next_state, FlowStep):
                        # Override transition target with handler result
                        session.current_step = next_state
                        self.logger.info(f"Handler overrode transition: {current_state.value} -> {next_state.value}")
                        return next_state, messages
                elif isinstance(result, list):
                    # Handler returns just messages
                    messages = result
                else:
                    # Unexpected return type
                    self.logger.warning(f"Unexpected handler return type: {type(result)}")
                    messages = result if isinstance(result, list) else []
            
            # Handle special cases that need conditional transitions
            next_event = context.get('next_event')
            if next_event in ['symptom_not_found', 'stay_in_state']:
                # Stay in same state, don't transition
                self.logger.info(f"Staying in current state: {current_state.value}")
                return current_state, messages
            
            # Update session state
            old_state = session.current_step
            session.current_step = transition.to_state
            
            self.logger.info(
                f"Transition successful: {old_state.value} -> {transition.to_state.value}"
            )
            
            return transition.to_state, messages
            
        except V2ValidationError:
            # Re-raise validation errors to be handled by orchestrator
            raise
        except Exception as e:
            self.logger.error(f"Transition handler failed: {e}")
            raise V2FlowError(
                current_state=current_state.value,
                message=f"Transition execution failed: {str(e)}"
            ) from e
    
    def classify_user_input(self, user_input: str, current_state: FlowStep) -> FlowEvent:
        """
        Classify user input into appropriate event for current state.
        
        This replaces the hardcoded if/else logic from V1.
        
        Args:
            user_input: User's input text
            current_state: Current flow state
            
        Returns:
            Classified FlowEvent
        """
        user_input = user_input.strip().lower()
        
        # Universal restart commands
        if user_input in ["neu", "restart", "von vorne"]:
            return FlowEvent.RESTART_COMMAND
        
        # State-specific classification
        if current_state == FlowStep.WAIT_FOR_SYMPTOM:
            return FlowEvent.USER_INPUT
        
        elif current_state == FlowStep.WAIT_FOR_CONFIRMATION:
            # Always use USER_INPUT for confirmation state
            # The handler will determine if it's yes/no/invalid
            return FlowEvent.USER_INPUT
            
        elif current_state in [FlowStep.ASK_FOR_EXERCISE, FlowStep.END_OR_RESTART]:
            # Yes/No responses
            if "ja" in user_input:
                return FlowEvent.YES_RESPONSE
            elif "nein" in user_input:
                return FlowEvent.NO_RESPONSE
            else:
                return FlowEvent.USER_INPUT  # Will trigger "please say yes or no"
        
        elif current_state == FlowStep.WAIT_FOR_CONTEXT:
            return FlowEvent.USER_INPUT
        
        elif current_state in [
            FlowStep.FEEDBACK_Q1, FlowStep.FEEDBACK_Q2, FlowStep.FEEDBACK_Q3, 
            FlowStep.FEEDBACK_Q4
        ]:
            return FlowEvent.FEEDBACK_ANSWER
            
        elif current_state == FlowStep.FEEDBACK_Q5:
            return FlowEvent.FEEDBACK_COMPLETE
        
        else:
            return FlowEvent.USER_INPUT
    
    def get_flow_summary(self) -> Dict[str, Any]:
        """Get summary of the FSM for debugging/monitoring"""
        states = list(set([t.from_state for t in self.transitions] + [t.to_state for t in self.transitions]))
        events = list(set([t.event for t in self.transitions]))
        
        return {
            "total_states": len(states),
            "total_events": len(events),
            "total_transitions": len(self.transitions),
            "states": [s.value for s in states],
            "events": [e.value for e in events],
            "transitions": [
                {
                    "from": t.from_state.value,
                    "event": t.event.value,
                    "to": t.to_state.value,
                    "description": t.description,
                    "has_handler": t.handler is not None
                }
                for t in self.transitions
            ]
        }
    
    def validate_fsm(self) -> List[str]:
        """Validate the FSM for common issues"""
        issues = []
        
        # Check for unreachable states
        reachable_states = {FlowStep.GREETING}  # Start state
        for transition in self.transitions:
            if transition.from_state in reachable_states:
                reachable_states.add(transition.to_state)
        
        all_states = set([t.from_state for t in self.transitions] + [t.to_state for t in self.transitions])
        unreachable = all_states - reachable_states
        
        if unreachable:
            issues.append(f"Unreachable states: {[s.value for s in unreachable]}")
        
        # Check for missing handlers
        transitions_without_handlers = [t for t in self.transitions if not t.handler]
        if transitions_without_handlers:
            issues.append(f"Transitions without handlers: {len(transitions_without_handlers)}")
        
        return issues


# Create singleton instance
def create_flow_engine() -> FlowEngine:
    """Create a properly initialized flow engine"""
    return FlowEngine()


# Validation on import
if __name__ == "__main__":
    print("=== V2 Flow Engine Validation ===")
    engine = create_flow_engine()
    summary = engine.get_flow_summary()
    print(f"States: {summary['total_states']}")
    print(f"Events: {summary['total_events']}")  
    print(f"Transitions: {summary['total_transitions']}")
    
    issues = engine.validate_fsm()
    if issues:
        print("\n⚠️  Issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n✅ FSM validation passed!")
        
    print(f"\n📋 Handler Integration:")
    transitions_with_handlers = sum(1 for t in engine.transitions if t.handler)
    print(f"  Transitions with handlers: {transitions_with_handlers}/{len(engine.transitions)}")
    
    if transitions_with_handlers == len(engine.transitions):
        print("  ✅ All transitions have handlers!")
    else:
        print(f"  ⚠️  {len(engine.transitions) - transitions_with_handlers} transitions missing handlers")