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
            
            # Check agent's internal phase transitions and trigger FSM events
            from src.models.agentic_models import ConversationPhase
            
            if agentic_response.phase == ConversationPhase.PERSPECTIVE:
                # Agent moved to perspective phase - trigger FSM transition
                context['next_event'] = 'information_collected'
                session.current_step = session.current_step  # Stay in current for FSM to handle transition
                logger.info("Agentic agent ready for perspective - triggering INFORMATION_COLLECTED event")
                
            elif agentic_response.phase == ConversationPhase.HANDOFF:
                # Agent generated perspective AND handoff question - transition to handoff decision state
                logger.info("Agentic agent moved to handoff phase - perspective and handoff question already included, transitioning to HANDOFF_DECISION")
                # Return tuple to override state transition
                return (FlowStep.HANDOFF_DECISION, [message])
                
            elif agentic_response.should_transition and agentic_response.next_flow_step:
                # Agent ready to transition to static flow
                await self._prepare_static_handoff(session, agentic_response)
                context['next_event'] = 'handoff_accepted'
                logger.info("Agentic agent ready for handoff - triggering HANDOFF_ACCEPTED event")
            
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
            
            # Since we already have the symptom, we should ask the first question
            # from the static flow, which is about context after symptom confirmation
            
            dog_name = handoff_dict['dog_name']
            symptom = handoff_dict['symptom']
            
            # Since we have all the information, we can skip directly to context gathering
            # Return a tuple with the target state to override the transition
            from src.models.flow_models import FlowStep
            
            # Transition message + context question
            messages = [
                V2AgentMessage(
                    sender="dog",
                    text="*schwanzwedel* Wunderbar! Dann schauen wir uns das genauer an...",
                    message_type="response",
                    metadata={
                        "handoff_completed": True,
                        "symptom_pre_collected": True
                    }
                ),
                V2AgentMessage(
                    sender="dog",
                    text=f"*aufmerksam* Also, {dog_name} {symptom}. Kannst du mir mehr über die Situation erzählen? Wann passiert das genau? Was ist drumherum los?",
                    message_type="question",
                    metadata={
                        "question_type": "context",
                        "dog_name": dog_name,
                        "symptom": symptom
                    }
                )
            ]
            
            # Return tuple to override state transition to WAIT_FOR_CONTEXT
            return (FlowStep.WAIT_FOR_CONTEXT, messages)
            
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
        if session.dog_info_collected and session.user_dog_name and session.user_dog_breed and session.active_symptom:
            logger.info(f"Using pre-collected dog info: {session.user_dog_name} ({session.user_dog_breed})")
            logger.info(f"Pre-collected symptom: {session.active_symptom}")
            
            # We already have the symptom from agentic flow, so we can proceed to asking about context
            # Generate the context question like the static flow would after symptom confirmation
            messages = await self.dog_agent.respond(AgentContext(
                session_id=session.session_id,
                user_input=session.active_symptom,  # Use the pre-collected symptom
                message_type=MessageType.QUESTION,
                metadata={
                    "question_type": "context",
                    "dog_name": session.user_dog_name,
                    "dog_breed": session.user_dog_breed,
                    "symptom": session.active_symptom,
                    "skip_confirmation": True,  # We don't need confirmation since it came from agentic flow
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
    # COMPATIBILITY WRAPPERS FOR FLOW ENGINE
    # ===========================================
    
    async def handle_agentic_collection(
        self,
        session: SessionState,
        user_input: str,
        context: Dict[str, Any]
    ) -> List[V2AgentMessage]:
        """Compatibility wrapper for enhanced agentic collection"""
        return await self.handle_enhanced_agentic_collection(session, user_input, context)
    
    async def handle_handoff_accepted(
        self,
        session: SessionState,
        user_input: str,
        context: Dict[str, Any]
    ) -> List[V2AgentMessage]:
        """Compatibility wrapper for enhanced handoff"""
        return await self.handle_enhanced_handoff_accepted(session, user_input, context)
    
    async def handle_perspective_generation(
        self,
        session: SessionState,
        user_input: str,
        context: Dict[str, Any]
    ) -> List[V2AgentMessage]:
        """Generate dog perspective using enhanced agent"""
        
        logger.info(f"Generating perspective for session {session.session_id[:8]}...")
        
        try:
            # Use enhanced agentic agent to generate perspective
            agent_context = AgentContext(
                session_id=session.session_id,
                user_input=user_input,
                message_type=MessageType.RESPONSE,
                metadata={
                    "session_state": session,
                    "generate_perspective": True
                }
            )
            
            response = await self.enhanced_agentic_agent.respond(agent_context)
            
            # Convert to V2AgentMessage
            message = V2AgentMessage(
                sender="dog",
                text=response.message,
                message_type="perspective",
                metadata={
                    "perspective_generated": True,
                    "enhanced_agentic": True
                }
            )
            
            # Trigger transition to handoff question
            context['next_event'] = 'perspective_generated'
            
            return [message]
            
        except Exception as e:
            logger.error(f"Perspective generation failed: {e}", exc_info=True)
            return [V2AgentMessage(
                sender="dog",
                text="*nachdenklich* Lass mich über das Verhalten nachdenken...",
                message_type="perspective"
            )]
    
    async def handle_handoff_question(
        self,
        session: SessionState,
        user_input: str,
        context: Dict[str, Any]
    ) -> List[V2AgentMessage]:
        """Ask user if they want to continue to full flow"""
        
        message = V2AgentMessage(
            sender="dog",
            text="*schwanzwedel* Möchtest du mehr über das Verhalten erfahren und lernen, wie du damit umgehen kannst?",
            message_type="question"
        )
        
        return [message]
    
    async def handle_handoff_declined(
        self,
        session: SessionState,
        user_input: str,
        context: Dict[str, Any]
    ) -> List[V2AgentMessage]:
        """Handle when user declines to continue"""
        
        message = V2AgentMessage(
            sender="dog",
            text="*schwanzwedel* Kein Problem! Ich bin da, wenn du Fragen hast. Wuff!",
            message_type="response"
        )
        
        return [message]
    
    async def handle_symptom_input(
        self,
        session: SessionState,
        user_input: str,
        context: Dict[str, Any]
    ) -> Tuple[Any, List[V2AgentMessage]]:
        """Compatibility wrapper for enhanced symptom input"""
        return await self.handle_enhanced_symptom_input(session, user_input, context)
    
    async def handle_handoff_accepted(
        self,
        session: SessionState,
        user_input: str,
        context: Dict[str, Any]
    ):
        """Compatibility wrapper for enhanced handoff accepted"""
        return await self.handle_enhanced_handoff_accepted(session, user_input, context)
    
    # ===========================================
    # ORIGINAL HANDLERS (copied from git history)
    # ===========================================
    
    async def handle_confirmation(self, session: SessionState, user_input: str, context: Dict[str, Any]) -> Tuple[Any, List[V2AgentMessage]]:
        """Handle user's confirmation response with match tracking"""
        logger.info(f"Handling confirmation response: '{user_input}'")
        
        # Delegate validation to validation service
        validation_result = await self.validation_service.validate_yes_no_response(user_input)
        
        if not validation_result.valid:
            logger.info(f"Yes/no validation failed: {validation_result.message}")
            raise V2ValidationError(
                message=validation_result.message,
                field="user_input", 
                value=user_input,
                details=validation_result.details
            )
        
        # Get response type from validation
        response_type = validation_result.details.get("response_type")
        
        # Get match distance from V2 SessionState field
        match_distance = session.match_distance if session.match_distance is not None else 'unknown'
        
        if response_type == "yes":
            logger.info(f"Match confirmation - Symptom: '{session.active_symptom}', Confirmed: yes, Distance: {match_distance}")
            
            # Import FlowStep for transition
            from src.models.flow_models import FlowStep
            
            # Transition to context gathering
            messages = await self.dog_agent.respond(AgentContext(
                session_id=session.session_id,
                user_input="",
                message_type=MessageType.QUESTION,
                metadata={"question_type": "context"}
            ))
            
            return (FlowStep.WAIT_FOR_CONTEXT, messages)
            
        elif response_type == "no":
            logger.info(f"Match confirmation - Symptom: '{session.active_symptom}', Confirmed: no, Distance: {match_distance}")
            
            # User said no - restart the conversation completely
            # Clear ALL session data for a true fresh start
            session.active_symptom = ""
            session.match_distance = None
            session.symptoms.clear()
            session.awaiting_diagnosis_confirmation = False
            session.diagnosis_confirmed = False
            session.feedback.clear()
            session.messages.clear()
            session.agent_status.clear()
            
            # Generate the same greeting as a new conversation would
            messages = await self.handle_greeting(session, "", {})
            
            from src.models.flow_models import FlowStep
            return (FlowStep.GREETING, messages)
    
    async def handle_context_input(
        self, 
        session: SessionState, 
        user_input: str, 
        context: Dict[str, Any]
    ) -> List[V2AgentMessage]:
        """
        Handle context input - analyze instincts and generate diagnosis.
        
        This performs instinct analysis using both symptom and context.
        
        Args:
            session: Current session state
            user_input: User's context description
            context: Additional context data
            
        Returns:
            List of diagnosis messages from dog agent
        """
        logger.info(f"Handling context input: '{user_input[:50]}...'")
        
        # Delegate validation to validation service
        validation_result = await self.validation_service.validate_context_input(user_input)
        if not validation_result.valid:
            logger.info(f"Context validation failed: {validation_result.message}")
            raise V2ValidationError(
                message=validation_result.message,
                field="user_input",
                value=user_input,
                details=validation_result.details
            )
        
        try:
            # Combine symptom and context for analysis
            symptom = session.active_symptom
            combined_input = f"Verhalten: {symptom}\nKontext: {user_input}"
            
            # Perform instinct analysis
            analysis_data = await self._analyze_instincts(symptom, user_input)

            
            # Extract dog info from context input too
            dog_info = await self.rapport_service.extract_dog_info(user_input, session)
            if dog_info:
                self.rapport_service.update_session_with_dog_info(session, dog_info)
            
            # Generate diagnosis from dog perspective
            agent_context = AgentContext(
                session_id=session.session_id,
                user_input=combined_input,
                message_type=MessageType.RESPONSE,
                metadata={
                    'response_mode': 'diagnosis',
                    'analysis_data': analysis_data,
                    'symptom': symptom,
                    'context': user_input,
                    'detected_dog_info': dog_info,
                    'user_dog_breed': session.user_dog_breed
                }
            )
            
            messages = await self.dog_agent.respond(agent_context)
            
            # Add exercise offer question
            exercise_context = AgentContext(
                session_id=session.session_id,
                message_type=MessageType.QUESTION,
                metadata={'question_type': 'exercise'}
            )
            
            exercise_messages = await self.dog_agent.respond(exercise_context)
            messages.extend(exercise_messages)
            
            return messages
            
        except Exception as e:
            logger.error(f"Error in context input handler: {e}")
            
            # Fallback to basic response
            agent_context = AgentContext(
                session_id=session.session_id,
                message_type=MessageType.ERROR,
                metadata={'error_type': 'technical'}
            )
            
            messages = await self.dog_agent.respond(agent_context)
            return messages
    
    async def handle_exercise_request(
        self, 
        session: SessionState, 
        user_input: str, 
        context: Dict[str, Any]
    ) -> List[V2AgentMessage]:
        """
        Handle exercise request - find and format training exercise.
        
        Args:
            session: Current session state
            user_input: User's response (should be "ja")
            context: Additional context data
            
        Returns:
            List of exercise messages from dog agent
        """
        logger.info(f"Handling exercise request for symptom: {session.active_symptom}")
        
        try:
            # Search for relevant exercise
            exercise_data = await self._find_exercise(session.active_symptom)
            
            # Generate exercise response
            agent_context = AgentContext(
                session_id=session.session_id,
                user_input=session.active_symptom,
                message_type=MessageType.RESPONSE,
                metadata={
                    'response_mode': 'exercise',
                    'exercise_data': exercise_data
                }
            )
            
            messages = await self.dog_agent.respond(agent_context)
            
            # Add restart question
            restart_context = AgentContext(
                session_id=session.session_id,
                message_type=MessageType.QUESTION,
                metadata={'question_type': 'restart'}
            )
            
            restart_messages = await self.dog_agent.respond(restart_context)
            messages.extend(restart_messages)
            
            return messages
            
        except Exception as e:
            logger.error(f"Error in exercise request handler: {e}")
            
            # Fallback exercise
            agent_context = AgentContext(
                session_id=session.session_id,
                message_type=MessageType.RESPONSE,
                metadata={
                    'response_mode': 'exercise',
                    'exercise_data': None  # Will use fallback
                }
            )
            
            messages = await self.dog_agent.respond(agent_context)
            return messages
    
    async def handle_feedback_question(
        self, 
        session: SessionState, 
        user_input: str, 
        context: Dict[str, Any]
    ) -> List[V2AgentMessage]:
        """
        Handle feedback question - generate specific feedback question.
        
        Args:
            session: Current session state
            user_input: User's input (usually empty for first question)
            context: Must contain 'question_number'
            
        Returns:
            List of feedback question messages from companion agent
        """
        question_number = context.get('question_number', 1)
        logger.info(f"Handling feedback question {question_number}")
        
        try:
            # Generate feedback question
            agent_context = AgentContext(
                session_id=session.session_id,
                user_input=user_input,
                message_type=MessageType.QUESTION,
                metadata={'question_number': question_number}
            )
            
            messages = await self.companion_agent.respond(agent_context)
            return messages
            
        except Exception as e:
            logger.error(f"Error in feedback question handler: {e}")
            
            # Fallback to companion error
            agent_context = AgentContext(
                session_id=session.session_id,
                message_type=MessageType.ERROR,
                metadata={'error_type': 'general'}
            )
            
            messages = await self.companion_agent.respond(agent_context)
            return messages
    
    async def handle_feedback_answer(
        self, 
        session: SessionState, 
        user_input: str, 
        context: Dict[str, Any]
    ) -> List[V2AgentMessage]:
        """
        Handle feedback answer - store answer and acknowledge.
        
        Args:
            session: Current session state
            user_input: User's feedback answer
            context: Additional context data
            
        Returns:
            List of acknowledgment messages from companion agent
        """
        logger.info(f"Handling feedback answer: '{user_input[:30]}...'")
        
        try:
            # Store feedback in the feedback list
            session.feedback.append(user_input.strip())
            
            # Generate acknowledgment
            agent_context = AgentContext(
                session_id=session.session_id,
                user_input=user_input,
                message_type=MessageType.RESPONSE,
                metadata={'response_mode': 'acknowledgment'}
            )
        
            messages = await self.companion_agent.respond(agent_context)
            return messages
        
        except Exception as e:
            logger.error(f"Error in feedback answer handler: {e}")            
            
            # Still acknowledge, but log error
            agent_context = AgentContext(
                session_id=session.session_id,
                message_type=MessageType.RESPONSE,
                metadata={'response_mode': 'acknowledgment'}
            )
            
            messages = await self.companion_agent.respond(agent_context)
            return messages
    
    async def handle_feedback_completion(
        self, 
        session: SessionState, 
        user_input: str, 
        context: Dict[str, Any]
    ) -> List[V2AgentMessage]:
        """
        Handle feedback completion - save all feedback and thank user.
        
        Args:
            session: Current session state
            user_input: Final feedback answer
            context: Additional context data
            
        Returns:
            List of completion messages from companion agent
        """
        logger.info(f"Handling feedback completion for session {session.session_id[:8]}...")
        
        try:
            # Store final answer in feedback list
            session.feedback.append(user_input.strip())
            
            # Save feedback to storage
            save_success = await self._save_feedback(session)
            
            # Generate completion message
            agent_context = AgentContext(
                session_id=session.session_id,
                user_input=user_input,
                message_type=MessageType.RESPONSE,
                metadata={
                    'response_mode': 'completion',
                    'save_success': save_success
                }
            )
            
            messages = await self.companion_agent.respond(agent_context)
            return messages
            
        except Exception as e:
            logger.error(f"Error in feedback completion handler: {e}")
            
            # Generate completion with save failure
            agent_context = AgentContext(
                session_id=session.session_id,
                message_type=MessageType.RESPONSE,
                metadata={
                    'response_mode': 'completion',
                    'save_success': False
                }
            )
            
            messages = await self.companion_agent.respond(agent_context)
            return messages

    # === Private Helper Methods ===
    
    async def _analyze_instincts(self, symptom: str, context: str) -> Dict[str, Any]:
        """
        Analyze instincts using vector search and GPT.
        
        Args:
            symptom: The described behavior
            context: Additional context
            
        Returns:
            Dict with instinct analysis data
        """
        try:
            # Search instinct database
            combined_query = f"{symptom} {context}"
            instinct_results = await self.weaviate_service.search(
                collection="Instinkte",
                query=combined_query,
                limit=5
            )
            
            # Use GPT to analyze and determine primary instinct
            if instinct_results:
                # Format instinct data for analysis
                instinct_descriptions = {}
                for result in instinct_results:
                    properties = result.get('properties', {})
                    instinct_name = properties.get('instinkt', '').lower()
                    hundesperspektive = properties.get('hundesperspektive', '')
                    
                    if 'jagd' in instinct_name:
                        instinct_descriptions['jagd'] = hundesperspektive
                    elif 'rudel' in instinct_name:
                        instinct_descriptions['rudel'] = hundesperspektive
                    elif 'territorial' in instinct_name:
                        instinct_descriptions['territorial'] = hundesperspektive
                    elif 'sexual' in instinct_name:
                        instinct_descriptions['sexual'] = hundesperspektive
                
                # GPT analysis
                from src.core.prompt_manager import PromptType
                analysis_prompt = self.prompt_manager.get_prompt(
                    PromptType.INSTINCT_ANALYSIS,  
                    symptom=symptom,
                    context=context
                )
                
                gpt_response = await self.gpt_service.complete(analysis_prompt)
                
                # Parse GPT response into structured data
                return {
                    'primary_instinct': self._extract_primary_instinct(gpt_response),
                    'primary_description': self._extract_description(gpt_response),
                    'all_instincts': instinct_descriptions,
                    'confidence': 0.8
                }
            
            # Fallback if no instinct data found
            return {
                'primary_instinct': 'unbekannt',
                'primary_description': 'Konnte nicht eindeutig bestimmt werden',
                'all_instincts': {},
                'confidence': 0.3
            }
            
        except Exception as e:
            logger.error(f"Error in instinct analysis: {e}")
            return {
                'primary_instinct': 'unbekannt',
                'primary_description': 'Fehler bei der Analyse',
                'all_instincts': {},
                'confidence': 0.1
            }
    
    async def _find_exercise(self, symptom: str) -> str:
        """
        Find relevant exercise for the symptom.
        
        Args:
            symptom: The behavior to find exercise for
            
        Returns:
            Exercise description string
        """
        try:
            # Search exercise database
            exercise_results = await self.weaviate_service.search(
                collection="Erziehung",
                query=symptom,
                limit=3
            )
            
            
            if exercise_results and len(exercise_results) > 0:
                # Return best matching exercise
                best_exercise = exercise_results[0]

                text = best_exercise.get('properties', {}).get('anleitung', 'Keine spezifische Übung gefunden.')

                return text
            
            # Fallback exercise
            return "Übe täglich 10 Minuten Impulskontrolle mit deinem Hund durch klare Kommandos und Belohnungen."
            
        except Exception as e:
            logger.error(f"Error finding exercise: {e}")
            return "Arbeite an der Grundausbildung mit deinem Hund - Sitz, Platz, Bleib."
    
    async def _save_feedback(self, session: SessionState) -> bool:
        """
        Save feedback to storage.
        
        Args:
            session: Session with feedback data
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Get feedback from the session's feedback list
            feedback_list = session.feedback
            
            if not feedback_list:
                return False
            
            # Prepare feedback data
            feedback_data = {
                'session_id': session.session_id,
                'symptom': getattr(session, 'active_symptom', ''),
                'responses': feedback_list,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            # Save to Redis
            if self.redis_service:
                self.redis_service.set(
                    f"feedback:{session.session_id}",
                    feedback_data,
                    expire=7776000  # 90 days
                )
            
            logger.info(f"Feedback saved for session {session.session_id[:8]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error saving feedback: {e}")
            return False
    
    def _extract_primary_instinct(self, gpt_response: str) -> str:
        """Extract primary instinct from GPT response."""
        response_lower = gpt_response.lower()
        
        if 'jagd' in response_lower:
            return 'jagd'
        elif 'rudel' in response_lower:
            return 'rudel'
        elif 'territorial' in response_lower:
            return 'territorial'
        elif 'sexual' in response_lower:
            return 'sexual'
        else:
            return 'unbekannt'
    
    def _extract_description(self, gpt_response: str) -> str:
        """Extract description from GPT response."""
        # Simple extraction - take first sentence
        sentences = gpt_response.split('.')
        if sentences and len(sentences[0]) > 20:
            return sentences[0].strip()
        return "Keine Beschreibung verfügbar"
    
    async def handle_greeting(self, session: SessionState, user_input: str, context: Dict[str, Any]) -> List[V2AgentMessage]:
        """Handle greeting - needed for confirmation handler fallback"""
        agent_context = AgentContext(
            session_id=session.session_id,
            user_input=user_input,
            message_type=MessageType.GREETING,
            metadata={}
        )
        
        try:
            messages = await self.dog_agent.respond(agent_context)
            return messages
        except Exception as e:
            logger.error(f"Greeting handler failed: {e}")
            # Return fallback greeting message
            return [V2AgentMessage(
                sender="dog",
                text="*schwanzwedel* Hallo! Schön, dass du da bist. Wie kann ich dir helfen?",
                message_type="greeting"
            )]