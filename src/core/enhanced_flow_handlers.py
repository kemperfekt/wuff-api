# src/core/enhanced_flow_handlers.py

"""
Enhanced Flow Handlers - Integrates new architecture components for improved conversation flow.

This module provides enhanced handlers that use the new InformationExtractor,
ConversationMemory, and HandoffManager for seamless agentic conversations.
"""

from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime, timezone

from src.models.session_state import SessionState
from src.models.flow_models import FlowStep
from src.agents.enhanced_agentic_dog_agent import EnhancedAgenticDogAgent
from src.agents.dog_agent import DogAgent
from src.agents.companion_agent import CompanionAgent
from src.agents.base_agent import AgentContext, MessageType, V2AgentMessage
from src.services.gpt_service import GPTService
from src.services.weaviate_service import WeaviateService
from src.services.redis_service import RedisService
from src.services.validation_service import ValidationService
from src.services.rapport_service import RapportService
from src.core.prompt_manager import PromptManager, PromptType
from src.core.exceptions import V2FlowError, V2ValidationError
from src.core.handoff_manager import HandoffManager

logger = logging.getLogger(__name__)


class EnhancedFlowHandlers:
    """
    Enhanced flow handlers that integrate the new architecture components.
    
    Key improvements:
    - Uses EnhancedAgenticDogAgent for natural conversation
    - Seamless handoff between agentic and static flows
    - Better error handling and recovery
    - Improved state management
    """
    
    def __init__(
        self,
        dog_agent: Optional[DogAgent] = None,
        companion_agent: Optional[CompanionAgent] = None,
        enhanced_agentic_agent: Optional[EnhancedAgenticDogAgent] = None,
        gpt_service: Optional[GPTService] = None,
        weaviate_service: Optional[WeaviateService] = None,
        redis_service: Optional[RedisService] = None,
        prompt_manager: Optional[PromptManager] = None,
        validation_service: Optional[ValidationService] = None
    ):
        """Initialize enhanced flow handlers with services and agents"""
        
        # Initialize services
        self.prompt_manager = prompt_manager or PromptManager()
        self.gpt_service = gpt_service or GPTService()
        self.weaviate_service = weaviate_service or WeaviateService()
        self.redis_service = redis_service or RedisService()
        self.validation_service = validation_service or ValidationService(gpt_service=self.gpt_service)
        self.rapport_service = RapportService()
        
        # Initialize handoff manager
        self.handoff_manager = HandoffManager()
        
        # Initialize agents
        self.dog_agent = dog_agent or DogAgent(
            personality="balu",
            prompt_manager=self.prompt_manager,
            gpt_service=self.gpt_service,
            weaviate_service=self.weaviate_service
        )
        
        self.companion_agent = companion_agent or CompanionAgent(
            prompt_manager=self.prompt_manager,
            redis_service=self.redis_service
        )
        
        # Initialize enhanced agentic agent
        self.enhanced_agentic_agent = enhanced_agentic_agent or EnhancedAgenticDogAgent(
            prompt_manager=self.prompt_manager,
            gpt_service=self.gpt_service,
            weaviate_service=self.weaviate_service
        )
        
        logger.info("Enhanced FlowHandlers initialized with new architecture components")
    
    # ===========================================
    # ENHANCED AGENTIC FLOW HANDLERS
    # ===========================================
    
    async def handle_greeting_to_agentic(
        self,
        session: SessionState,
        user_input: str,
        context: Dict[str, Any]
    ) -> List[V2AgentMessage]:
        """Handle greeting and start enhanced agentic conversation"""
        
        logger.info(f"Starting enhanced agentic flow for session {session.session_id[:8]}...")
        
        try:
            # Create context for enhanced agentic agent
            agent_context = AgentContext(
                session_id=session.session_id,
                user_input=user_input,
                message_type=MessageType.GREETING,
                metadata={"session_state": session}
            )
            
            # Get response from enhanced agentic agent
            agentic_response = await self.enhanced_agentic_agent.respond(agent_context)
            
            # Convert to V2AgentMessage format
            message = V2AgentMessage(
                sender="dog",
                text=agentic_response.message,
                message_type="greeting",
                metadata={
                    "phase": agentic_response.phase.value,
                    "information_status": agentic_response.information_collected.model_dump(),
                    "cost_info": agentic_response.cost_info,
                    "enhanced_agentic": True
                }
            )
            
            return [message]
            
        except Exception as e:
            logger.error(f"Enhanced agentic greeting failed: {e}", exc_info=True)
            # Fallback to regular greeting
            return await self._fallback_greeting(session, user_input, context)
    
    async def handle_enhanced_agentic_collection(
        self,
        session: SessionState,
        user_input: str,
        context: Dict[str, Any]
    ) -> List[V2AgentMessage]:
        """Handle user input during enhanced agentic collection"""
        
        logger.info(f"Processing enhanced agentic collection for session {session.session_id[:8]}...")
        
        try:
            # Create context for enhanced agentic agent
            agent_context = AgentContext(
                session_id=session.session_id,
                user_input=user_input,
                message_type=MessageType.RESPONSE,
                metadata={"session_state": session}
            )
            
            # Process with enhanced agentic agent
            agentic_response = await self.enhanced_agentic_agent.respond(agent_context)
            
            # Update session with collected information
            info_status = agentic_response.information_collected
            if info_status.dog_name:
                session.user_dog_name = info_status.dog_name
            if info_status.dog_breed:
                session.user_dog_breed = info_status.dog_breed
            if info_status.main_concern:
                session.active_symptom = info_status.main_concern
            if info_status.user_name:
                session.user_name = info_status.user_name
            
            # Check for transition to static flow
            if agentic_response.should_transition and agentic_response.next_flow_step:
                # Prepare for handoff
                await self._prepare_static_handoff(session, agentic_response)
            
            # Convert to V2AgentMessage
            message = V2AgentMessage(
                sender="dog",
                text=agentic_response.message,
                message_type="response",
                metadata={
                    "phase": agentic_response.phase.value,
                    "information_status": agentic_response.information_collected.model_dump(),
                    "should_transition": agentic_response.should_transition,
                    "cost_info": agentic_response.cost_info,
                    "enhanced_agentic": True
                }
            )
            
            return [message]
            
        except Exception as e:
            logger.error(f"Enhanced agentic collection failed: {e}", exc_info=True)
            # Return error message
            error_message = V2AgentMessage(
                sender="dog",
                text="*nachdenklich* Entschuldige, könntest du das nochmal sagen?",
                message_type="error"
            )
            return [error_message]
    
    async def handle_enhanced_handoff_accepted(
        self,
        session: SessionState,
        user_input: str,
        context: Dict[str, Any]
    ) -> List[V2AgentMessage]:
        """Handle handoff acceptance with enhanced flow"""
        
        logger.info(f"Processing enhanced handoff for session {session.session_id[:8]}...")
        
        try:
            # Get handoff package from enhanced agent
            handoff_dict = await self.enhanced_agentic_agent.prepare_handoff(session.session_id)
            
            # Validate we have required information
            if not all([
                handoff_dict.get("dog_name"),
                handoff_dict.get("dog_breed"),
                handoff_dict.get("symptom")
            ]):
                # Missing information - continue in agentic mode
                logger.warning("Handoff attempted but missing required information")
                return [V2AgentMessage(
                    sender="dog",
                    text="*nachdenklich* Lass mich noch ein paar Details sammeln...",
                    message_type="response"
                )]
            
            # Execute handoff to session
            session.user_dog_name = handoff_dict["dog_name"]
            session.user_dog_breed = handoff_dict["dog_breed"] 
            session.active_symptom = handoff_dict["symptom"]
            session.user_name = handoff_dict.get("user_name")
            session.dog_info_collected = True
            
            # Store handoff metadata
            session.agentic_metadata = handoff_dict.get("metadata", {})
            
            # Transition message
            transition_msg = f"*schwanzwedel* Super! Jetzt wo ich alles über {handoff_dict['dog_name']} weiß, können wir das Verhalten genauer analysieren..."
            
            message = V2AgentMessage(
                sender="dog",
                text=transition_msg,
                message_type="response",
                metadata={
                    "handoff_completed": True,
                    "next_step": "WAIT_FOR_SYMPTOM",
                    "handoff_data": {
                        "dog_name": handoff_dict["dog_name"],
                        "dog_breed": handoff_dict["dog_breed"],
                        "turns": handoff_dict.get("metadata", {}).get("turns", 0)
                    }
                }
            )
            
            return [message]
            
        except Exception as e:
            logger.error(f"Enhanced handoff failed: {e}", exc_info=True)
            # Fallback transition
            return [V2AgentMessage(
                sender="dog",
                text="*schwanzwedel* Dann schauen wir uns das genauer an...",
                message_type="response"
            )]
    
    async def _prepare_static_handoff(
        self,
        session: SessionState,
        agentic_response
    ) -> None:
        """Prepare session for handoff to static flow"""
        
        # Mark that information has been collected
        session.dog_info_collected = True
        
        # Store perspective if available
        if hasattr(agentic_response, 'tool_results'):
            for tool_result in agentic_response.tool_results:
                if tool_result.tool_name == "weaviate_perspective" and tool_result.success:
                    session.dog_perspective = tool_result.result
    
    async def _fallback_greeting(
        self,
        session: SessionState,
        user_input: str,
        context: Dict[str, Any]
    ) -> List[V2AgentMessage]:
        """Fallback greeting using regular dog agent"""
        
        agent_context = AgentContext(
            session_id=session.session_id,
            user_input=user_input,
            message_type=MessageType.GREETING,
            metadata={}
        )
        
        messages = await self.dog_agent.respond(agent_context)
        return messages
    
    # ===========================================
    # ENHANCED STATIC FLOW HANDLERS (Existing but improved)
    # ===========================================
    
    async def handle_enhanced_symptom_input(
        self,
        session: SessionState,
        user_input: str,
        context: Dict[str, Any]
    ) -> Tuple[Any, List[V2AgentMessage]]:
        """Enhanced symptom input handling with better context awareness"""
        
        logger.info(f"Handling enhanced symptom input: '{user_input[:50]}...'")
        
        # If we already have dog information from agentic flow, use it
        if session.dog_info_collected and session.user_dog_name and session.user_dog_breed:
            logger.info(f"Using pre-collected dog info: {session.user_dog_name} ({session.user_dog_breed})")
            
            # We can skip the symptom matching since we already have the concern
            # and go directly to context gathering
            messages = await self.dog_agent.respond(AgentContext(
                session_id=session.session_id,
                user_input=user_input,
                message_type=MessageType.RESPONSE,
                metadata={
                    "response_mode": "acknowledge_symptom",
                    "dog_name": session.user_dog_name,
                    "dog_breed": session.user_dog_breed,
                    "pre_collected": True
                }
            ))
            
            return ('symptom_found', messages)
        
        # Otherwise, fall back to regular symptom handling
        return await self._handle_regular_symptom_input(session, user_input, context)
    
    async def _handle_regular_symptom_input(
        self,
        session: SessionState,
        user_input: str,
        context: Dict[str, Any]
    ) -> Tuple[Any, List[V2AgentMessage]]:
        """Regular symptom input handling (from original flow handlers)"""
        
        # Delegate validation to validation service
        validation_result = await self.validation_service.validate_symptom_input(user_input)
        if not validation_result.valid:
            logger.info(f"Symptom validation failed: {validation_result.message}")
            raise V2ValidationError(
                message=validation_result.message,
                field="user_input",
                value=user_input,
                details=validation_result.details
            )
        
        try:
            # Use semantic search to find matching symptoms
            results = await self.weaviate_service.search(
                collection="Symptome",
                query=user_input,
                limit=3,
                properties=["symptom_name", "schnelldiagnose"],
                return_metadata=True
            )
            
            # Check if we have a good match
            if results and results[0]['metadata'].get('distance', 1.0) < 0.6:
                match_found = True
                match_data = results[0]['properties'].get('schnelldiagnose', '')
                logger.info(f"Good match found with distance {results[0]['metadata'].get('distance')}")
            else:
                match_found = False
                match_data = None
                logger.info("No good match found")
            
        except Exception as e:
            logger.error(f"Error in symptom search: {e}", exc_info=True)
            return ('symptom_not_found', [V2AgentMessage(
                sender="dog",
                text="*verwirrt* Da ist etwas schiefgelaufen. Kannst du es nochmal versuchen?",
                message_type="error"
            )])
        
        # Store symptom
        session.active_symptom = user_input
        
        if match_found and match_data:
            # Generate response and ask for confirmation
            messages = await self.dog_agent.respond(AgentContext(
                session_id=session.session_id,
                user_input=user_input,
                message_type=MessageType.RESPONSE,
                metadata={
                    "response_mode": "perspective_only",
                    "match_data": match_data
                }
            ))
            
            # Add confirmation question
            messages.extend(await self.dog_agent.respond(AgentContext(
                session_id=session.session_id,
                message_type=MessageType.QUESTION,
                metadata={"question_type": "ask_for_more"}
            )))
            
            return ('symptom_found', messages)
        else:
            # No match - ask to try again
            messages = await self.dog_agent.respond(AgentContext(
                session_id=session.session_id,
                user_input=user_input,
                message_type=MessageType.ERROR,
                metadata={"error_type": "no_behavior_match"}
            ))
            
            return ('symptom_not_found', messages)
    
    # ===========================================
    # DELEGATION TO ORIGINAL HANDLERS (for compatibility)
    # ===========================================
    
    # Import and delegate other methods from original FlowHandlers
    # This ensures backward compatibility while adding enhanced features
    
    async def handle_confirmation(self, session: SessionState, user_input: str, context: Dict[str, Any]):
        """Delegate to regular confirmation handler"""
        # Import original implementation
        from src.core.flow_handlers import FlowHandlers
        original_handlers = FlowHandlers(
            prompt_manager=self.prompt_manager,
            gpt_service=self.gpt_service,
            weaviate_service=self.weaviate_service,
            redis_service=self.redis_service
        )
        return await original_handlers.handle_confirmation(session, user_input, context)
    
    async def handle_context_input(self, session: SessionState, user_input: str, context: Dict[str, Any]):
        """Delegate to regular context handler"""
        from src.core.flow_handlers import FlowHandlers
        original_handlers = FlowHandlers(
            prompt_manager=self.prompt_manager,
            gpt_service=self.gpt_service,
            weaviate_service=self.weaviate_service,
            redis_service=self.redis_service
        )
        return await original_handlers.handle_context_input(session, user_input, context)
    
    async def handle_exercise_request(self, session: SessionState, user_input: str, context: Dict[str, Any]):
        """Delegate to regular exercise handler"""
        from src.core.flow_handlers import FlowHandlers
        original_handlers = FlowHandlers(
            prompt_manager=self.prompt_manager,
            gpt_service=self.gpt_service,
            weaviate_service=self.weaviate_service,
            redis_service=self.redis_service
        )
        return await original_handlers.handle_exercise_request(session, user_input, context)
    
    async def handle_feedback_question(self, session: SessionState, user_input: str, context: Dict[str, Any]):
        """Delegate to regular feedback question handler"""
        from src.core.flow_handlers import FlowHandlers
        original_handlers = FlowHandlers(
            prompt_manager=self.prompt_manager,
            gpt_service=self.gpt_service,
            weaviate_service=self.weaviate_service,
            redis_service=self.redis_service
        )
        return await original_handlers.handle_feedback_question(session, user_input, context)
    
    async def handle_feedback_answer(self, session: SessionState, user_input: str, context: Dict[str, Any]):
        """Delegate to regular feedback answer handler"""
        from src.core.flow_handlers import FlowHandlers
        original_handlers = FlowHandlers(
            prompt_manager=self.prompt_manager,
            gpt_service=self.gpt_service,
            weaviate_service=self.weaviate_service,
            redis_service=self.redis_service
        )
        return await original_handlers.handle_feedback_answer(session, user_input, context)
    
    async def handle_feedback_completion(self, session: SessionState, user_input: str, context: Dict[str, Any]):
        """Delegate to regular feedback completion handler"""
        from src.core.flow_handlers import FlowHandlers
        original_handlers = FlowHandlers(
            prompt_manager=self.prompt_manager,
            gpt_service=self.gpt_service,
            weaviate_service=self.weaviate_service,
            redis_service=self.redis_service
        )
        return await original_handlers.handle_feedback_completion(session, user_input, context)