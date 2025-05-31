# src/v2/core/orchestrator.py
"""
V2 Flow Orchestrator - Clean interface for conversation management.

This replaces the V1 flow_orchestrator.py with a clean, FSM-based approach
that coordinates the flow engine, services, and agents.
"""

from typing import List, Dict, Any, Optional
import logging

from src.models.flow_models import FlowStep
from src.models.session_state import SessionState, SessionStore
from src.agents.base_agent import V2AgentMessage
from src.core.flow_engine import FlowEngine, FlowEvent, create_flow_engine
from src.core.flow_handlers import FlowHandlers
from src.core.exceptions import V2FlowError, V2ValidationError
from src.services.gpt_service import GPTService
from src.services.weaviate_service import WeaviateService  
from src.services.redis_service import RedisService
from src.core.prompt_manager import PromptManager

logger = logging.getLogger(__name__)


class V2Orchestrator:
    """
    V2 Flow Orchestrator - Main interface for conversation management.
    
    This orchestrator:
    1. Manages session state
    2. Classifies user input
    3. Processes FSM events
    4. Returns formatted messages
    5. Handles errors gracefully
    """
    
    def __init__(
        self,
        session_store: Optional[SessionStore] = None,
        flow_engine: Optional[FlowEngine] = None,
        enable_logging: bool = True
    ):
        """
        Initialize V2 orchestrator.
        
        Args:
            session_store: Session management (uses existing V1 for compatibility)
            flow_engine: FSM engine (creates new if not provided)
            enable_logging: Enable detailed logging
        """
        self.session_store = session_store or SessionStore()
        
        # Initialize V2 components
        if flow_engine:
            self.flow_engine = flow_engine
            # Mark as already initialized if provided
            self._services_initialized = True
        else:
            # Defer service initialization to avoid blocking startup
            logger.info("V2 orchestrator created (services will be lazy-loaded)")
            self.flow_engine = None
            self._services_initialized = False
            
            # Initialize empty service references
            self.prompt_manager = None
            self.gpt_service = None
            self.weaviate_service = None
            self.redis_service = None
            self.flow_handlers = None
        
        self.enable_logging = enable_logging
        logger.info("V2 Orchestrator initialized successfully")
    
    async def _ensure_services_initialized(self):
        """
        Lazy initialization of services to avoid blocking startup.
        
        This method is called automatically before any operation that needs services.
        """
        if self._services_initialized:
            return
            
        logger.info("Initializing V2 services (lazy loading)...")
        
        try:
            # Initialize services
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
            )
            
            # Initialize flow engine with handlers
            self.flow_engine = FlowEngine(self.flow_handlers)
            
            self._services_initialized = True
            logger.info("V2 services initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize V2 services: {e}")
            raise
    
    async def handle_message(self, session_id: str, user_input: str) -> List[Dict[str, Any]]:
        """
        Main entry point for handling user messages.
        
        This is the V2 replacement for the V1 handle_message function.
        
        Args:
            session_id: Session identifier
            user_input: User's message text
            
        Returns:
            List of message dictionaries compatible with V1 format
        """
        try:
            # Ensure services are initialized before processing
            await self._ensure_services_initialized()
            
            if self.enable_logging:
                logger.info(f"V2 handling message for session {session_id}: '{user_input[:50]}...'")
            
            # Get or create session
            session = self.session_store.get_or_create(session_id)
            
            # Add user message to session history if not empty
            if user_input.strip():
                # Convert V2AgentMessage to V1 format for session storage
                from src.models.flow_models import AgentMessage
                user_message = AgentMessage(sender="user", text=user_input.strip())
                session.messages.append(user_message)
            
            # Get current state
            current_state = session.current_step
            
            # Classify user input to determine event
            event = self.flow_engine.classify_user_input(user_input, current_state)
            
            if self.enable_logging:
                logger.info(f"Classified input as event: {event.value} in state: {current_state.value}")
            
            # Process the event through FSM
            new_state, v2_messages = await self.flow_engine.process_event(
                session=session,
                event=event,
                user_input=user_input.strip(),
                context={}
            )
            
            # Convert V2AgentMessage list to V1-compatible format
            response_messages = []
            for v2_msg in v2_messages:
                # Convert to V1 AgentMessage format for compatibility
                v1_message = AgentMessage(
                    sender=v2_msg.sender,
                    text=v2_msg.text
                )
                session.messages.append(v1_message)
                
                # Convert to dict format for API response
                response_messages.append({
                    "sender": v2_msg.sender,
                    "text": v2_msg.text,
                    "message_type": v2_msg.message_type,
                    "metadata": v2_msg.metadata
                })
            
            if self.enable_logging:
                logger.info(f"State transition: {current_state.value} -> {new_state.value}")
                logger.info(f"Generated {len(response_messages)} response messages")
            
            return response_messages
            
        except V2FlowError as e:
            logger.error(f"V2 Flow error: {e.message}")
            # Check if the error contains messages from handlers
            if hasattr(e, 'messages') and e.messages:
                # Return the specific error messages from the handler
                return [
                    {
                        "sender": msg.sender,
                        "text": msg.text,
                        "message_type": msg.message_type,
                        "metadata": msg.metadata
                    }
                    for msg in e.messages
                ]
            # For flow errors without messages, return a more specific error
            return self._create_error_response(
                "Ich habe deine Eingabe nicht verstanden. Kannst du es anders formulieren?",
                session_id
            )
            
        except V2ValidationError as e:
            logger.error(f"V2 Validation error: {e.message}")
            # Convert validation error to appropriate agent response
            error_messages = await self._handle_validation_error(e, session_id)
            return error_messages
            
        except Exception as e:
            logger.error(f"Unexpected error in V2 orchestrator: {e}", exc_info=True)
            return self._create_error_response(
                "Es ist ein unerwarteter Fehler aufgetreten. Bitte versuche es später noch einmal.",
                session_id
            )
    
    async def start_conversation(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Start a new conversation.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of greeting messages
        """
        try:
            # Ensure services are initialized before processing
            await self._ensure_services_initialized()
            
            logger.info(f"Starting new V2 conversation for session {session_id}")
            
            # Get or create session
            session = self.session_store.get_or_create(session_id)
            session.current_step = FlowStep.GREETING
            
            # Process greeting event
            new_state, v2_messages = await self.flow_engine.process_event(
                session=session,
                event=FlowEvent.START_SESSION,
                user_input="",
                context={}
            )
            
            # Convert to response format
            response_messages = []
            for v2_msg in v2_messages:
                # Store in session
                from src.models.flow_models import AgentMessage
                v1_message = AgentMessage(sender=v2_msg.sender, text=v2_msg.text)
                session.messages.append(v1_message)
                
                # Add to response
                response_messages.append({
                    "sender": v2_msg.sender,
                    "text": v2_msg.text,
                    "message_type": v2_msg.message_type,
                    "metadata": v2_msg.metadata
                })
            
            logger.info(f"Started conversation with {len(response_messages)} greeting messages")
            return response_messages
            
        except Exception as e:
            logger.error(f"Error starting V2 conversation: {e}", exc_info=True)
            return self._create_error_response(
                "Entschuldige, ich habe Probleme beim Starten. Bitte versuche es noch einmal.",
                session_id
            )
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """
        Get information about a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dict with session information
        """
        session = self.session_store.get_or_create(session_id)
        
        return {
            "session_id": session.session_id,
            "current_step": session.current_step.value,
            "active_symptom": getattr(session, 'active_symptom', ''),
            "message_count": len(session.messages),
            "feedback_collected": len(getattr(session, 'feedback', [])),
            "valid_events": [
                event.value for event in self._get_valid_events(session.current_step)
            ]
        }
    
    def _get_valid_events(self, current_state: FlowStep) -> List[FlowEvent]:
        """Get valid events for current state."""
        transitions = self.flow_engine.get_valid_transitions(current_state)
        return [t.event for t in transitions]
    
    def _create_error_response(self, error_message: str, session_id: str) -> List[Dict[str, Any]]:
        """
        Create standardized error response.
        
        Args:
            error_message: User-friendly error message
            session_id: Session identifier
            
        Returns:
            List with single error message
        """
        return [{
            "sender": "dog",
            "text": error_message,
            "message_type": "error",
            "metadata": {"error": True}
        }]
    
    async def _handle_validation_error(self, error: V2ValidationError, session_id: str) -> List[Dict[str, Any]]:
        """
        Convert validation error to appropriate agent response.
        
        Args:
            error: V2ValidationError containing validation details
            session_id: Session identifier
            
        Returns:
            List of error message dictionaries
        """
        from src.agents.base_agent import AgentContext, MessageType
        
        # Get error type from validation details - map validation to agent error types
        error_details = error.details or {}
        
        # Use the error type from validation details
        validation_error_type = error_details.get("error_type", "")
        
        if validation_error_type == "input_too_short":
            agent_error_type = "input_too_short"
        elif validation_error_type == "context_too_short":
            agent_error_type = "context_too_short"  # Keep specific context error
        elif validation_error_type == "invalid_yes_no":
            agent_error_type = "invalid_yes_no"
        elif "too short" in str(error.message).lower():
            agent_error_type = "input_too_short"
        elif "yes/no" in str(error.message).lower():
            agent_error_type = "invalid_yes_no"
        else:
            agent_error_type = "invalid_input"
        
        try:
            # Create agent context for error response
            agent_context = AgentContext(
                session_id=session_id,
                user_input=str(error.value) if error.value else "",
                message_type=MessageType.ERROR,
                metadata={"error_type": agent_error_type}
            )
            
            # Get dog agent instance from flow handlers
            dog_agent = self.flow_handlers.dog_agent if hasattr(self, 'flow_handlers') else None
            if not dog_agent:
                # Fallback to generic error
                return self._create_error_response(
                    "Ich habe deine Eingabe nicht verstanden. Kannst du es anders formulieren?",
                    session_id
                )
            
            # Generate agent response
            v2_messages = await dog_agent.respond(agent_context)
            
            # Convert to API format
            return [
                {
                    "sender": msg.sender,
                    "text": msg.text,
                    "message_type": msg.message_type,
                    "metadata": msg.metadata
                }
                for msg in v2_messages
            ]
            
        except Exception as e:
            logger.error(f"Error generating validation error response: {e}")
            # Fallback to generic error
            return self._create_error_response(
                "Ich habe deine Eingabe nicht verstanden. Kannst du es anders formulieren?",
                session_id
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of V2 orchestrator and its components.
        
        Returns:
            Dict with health status
        """
        health_status = {
            "orchestrator": "healthy",
            "flow_engine": "unknown",
            "services": {},
            "overall": "healthy"
        }
        
        try:
            # Check if services are initialized
            if not self._services_initialized:
                health_status["flow_engine"] = "not_initialized"
                health_status["services"]["status"] = "lazy_loading_enabled"
                health_status["overall"] = "ready"
                health_status["summary"] = {
                    "session_count": len(self.session_store.sessions),
                    "services_initialized": False
                }
                return health_status
            
            # Check flow engine
            summary = self.flow_engine.get_flow_summary()
            issues = self.flow_engine.validate_fsm()
            
            if issues:
                health_status["flow_engine"] = f"issues: {len(issues)}"
                health_status["overall"] = "warning"
            else:
                health_status["flow_engine"] = "healthy"
            
            # Check services if available
            if hasattr(self, 'flow_handlers'):
                # Check GPT service
                if self.flow_handlers.gpt_service:
                    try:
                        gpt_status = await self.flow_handlers.gpt_service.health_check()
                        health_status["services"]["gpt"] = "healthy" if gpt_status.get("healthy") else "unhealthy"
                    except Exception as e:
                        health_status["services"]["gpt"] = f"error: {str(e)[:50]}"
                        health_status["overall"] = "warning"
                
                # Check Weaviate service
                if self.flow_handlers.weaviate_service:
                    try:
                        weaviate_status = await self.flow_handlers.weaviate_service.health_check()
                        health_status["services"]["weaviate"] = "healthy" if weaviate_status.get("healthy") else "unhealthy"
                    except Exception as e:
                        health_status["services"]["weaviate"] = f"error: {str(e)[:50]}"
                        health_status["overall"] = "warning"
                
                # Check Redis service
                if self.flow_handlers.redis_service:
                    try:
                        redis_status = await self.flow_handlers.redis_service.health_check()
                        health_status["services"]["redis"] = "healthy" if redis_status.get("healthy") else "unhealthy"
                    except Exception as e:
                        health_status["services"]["redis"] = f"error: {str(e)[:50]}"
                        # Redis is optional, so don't mark overall as warning
            
            # Add summary info
            health_status["summary"] = {
                "total_states": summary["total_states"],
                "total_transitions": summary["total_transitions"],
                "session_count": len(self.session_store.sessions)
            }
            
        except Exception as e:
            health_status["orchestrator"] = f"error: {str(e)}"
            health_status["overall"] = "unhealthy"
        
        return health_status
    
    def get_flow_debug_info(self) -> Dict[str, Any]:
        """
        Get debug information about the flow engine.
        
        Returns:
            Dict with debug information
        """
        try:
            summary = self.flow_engine.get_flow_summary()
            issues = self.flow_engine.validate_fsm()
            
            return {
                "flow_summary": summary,
                "validation_issues": issues,
                "session_count": len(self.session_store.sessions),
                "active_sessions": [
                    {
                        "session_id": session_id,
                        "current_step": session.current_step.value,
                        "message_count": len(session.messages)
                    }
                    for session_id, session in self.session_store.sessions.items()
                ]
            }
            
        except Exception as e:
            return {"error": str(e)}


# Global orchestrator instance for easy access
_orchestrator: Optional[V2Orchestrator] = None


def get_orchestrator(session_store: Optional[SessionStore] = None) -> V2Orchestrator:
    """
    Get the global V2 orchestrator instance.
    
    Args:
        session_store: Optional session store (for initialization)
        
    Returns:
        V2Orchestrator instance
    """
    global _orchestrator
    
    if _orchestrator is None:
        logger.info("Creating new V2 orchestrator instance")
        _orchestrator = V2Orchestrator(session_store=session_store)
    
    return _orchestrator


# Compatibility functions for V1 interface
async def handle_message(session_id: str, user_input: str) -> List[Dict[str, Any]]:
    """
    V1-compatible handle_message function.
    
    This provides the same interface as the V1 system but uses V2 internally.
    """
    orchestrator = get_orchestrator()
    return await orchestrator.handle_message(session_id, user_input)


def init_orchestrator(session_store: SessionStore) -> V2Orchestrator:
    """
    V1-compatible init_orchestrator function.
    
    Args:
        session_store: Session store instance
        
    Returns:
        V2Orchestrator instance
    """
    global _orchestrator
    _orchestrator = V2Orchestrator(session_store=session_store)
    return _orchestrator


# Demo/test function
async def demo_conversation():
    """Demo a complete conversation flow."""
    print("🚀 V2 Orchestrator Demo")
    print("=" * 50)
    
    orchestrator = get_orchestrator()
    session_id = "demo-session"
    
    try:
        # Start conversation
        print("\n1. Starting conversation...")
        messages = await orchestrator.start_conversation(session_id)
        for msg in messages:
            print(f"   {msg['sender']}: {msg['text']}")
        
        # Simulate user input
        test_inputs = [
            "Mein Hund bellt ständig wenn Besucher kommen",
            "ja",
            "Es passiert immer wenn jemand an der Tür klingelt. Der Hund springt dann auch hoch.",
            "ja",
            "ja",
            "Sehr hilfreich",
            "Die Hundeperspektive war interessant",
            "Die Übung passt gut",
            "9 von 10",
            "test@example.com"
        ]
        
        for i, user_input in enumerate(test_inputs, 2):
            print(f"\n{i}. User: {user_input}")
            messages = await orchestrator.handle_message(session_id, user_input)
            for msg in messages:
                print(f"   {msg['sender']}: {msg['text'][:100]}...")
        
        # Show session info
        print(f"\n📊 Session Info:")
        info = orchestrator.get_session_info(session_id)
        for key, value in info.items():
            print(f"   {key}: {value}")
        
        print(f"\n✅ Demo completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_conversation())