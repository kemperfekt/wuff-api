# src/v2/core/flow_handlers.py
"""
Flow handlers for V2 Flow Engine - Business logic implementation.

These handlers execute the actual business logic during FSM state transitions.
They coordinate between V2 services (GPT, Weaviate, Redis) and V2 agents (Dog, Companion).
"""

from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime, timezone

from src.state.session_state import SessionState
from src.v2.agents.dog_agent import DogAgent
from src.v2.agents.companion_agent import CompanionAgent
from src.v2.agents.base_agent import AgentContext, MessageType, V2AgentMessage
from src.v2.services.gpt_service import GPTService
from src.v2.services.weaviate_service import WeaviateService
from src.v2.services.redis_service import RedisService
from src.v2.core.prompt_manager import PromptManager, PromptType
from src.v2.core.exceptions import V2FlowError, V2ValidationError

logger = logging.getLogger(__name__)


class FlowHandlers:
    """
    Implements all flow handlers for the V2 FSM.
    
    Each handler corresponds to a specific state transition and implements
    the business logic needed for that transition.
    """
    
    def __init__(
        self,
        dog_agent: Optional[DogAgent] = None,
        companion_agent: Optional[CompanionAgent] = None,
        gpt_service: Optional[GPTService] = None,
        weaviate_service: Optional[WeaviateService] = None,
        redis_service: Optional[RedisService] = None,
        prompt_manager: Optional[PromptManager] = None
    ):
        """
        Initialize flow handlers with V2 services and agents.
        
        Args:
            dog_agent: Dog agent for dog-perspective messages
            companion_agent: Companion agent for feedback messages
            gpt_service: GPT service for text generation
            weaviate_service: Vector search service
            redis_service: Caching and feedback storage
            prompt_manager: Centralized prompt management
        """
        # Initialize services
        self.prompt_manager = prompt_manager or PromptManager()
        self.gpt_service = gpt_service or GPTService()
        self.weaviate_service = weaviate_service or WeaviateService()
        self.redis_service = redis_service or RedisService()
        
        # Initialize agents with services
        self.dog_agent = dog_agent or DogAgent(
            prompt_manager=self.prompt_manager,
            gpt_service=self.gpt_service,
            weaviate_service=self.weaviate_service
        )
        
        self.companion_agent = companion_agent or CompanionAgent(
            prompt_manager=self.prompt_manager,
            redis_service=self.redis_service
        )
        
        logger.info("FlowHandlers initialized with V2 services and agents")
    
    async def handle_greeting(
        self, 
        session: SessionState, 
        user_input: str, 
        context: Dict[str, Any]
    ) -> List[V2AgentMessage]:
        """
        Handle initial greeting - start conversation.
        
        Args:
            session: Current session state
            user_input: User's input (empty for greeting)
            context: Additional context data
            
        Returns:
            List of greeting messages from dog agent
        """
        logger.info(f"Handling greeting for session {session.session_id}")
        
        try:
            # Create context for dog agent
            agent_context = AgentContext(
                session_id=session.session_id,
                user_input=user_input,
                message_type=MessageType.GREETING
            )
            
            # Get greeting messages from dog agent
            messages = await self.dog_agent.respond(agent_context)
            
            logger.info(f"Generated {len(messages)} greeting messages")
            return messages
            
        except Exception as e:
            logger.error(f"Error in greeting handler: {e}")
            raise V2FlowError(
                current_state="GREETING",
                message=f"Failed to generate greeting: {str(e)}"
            ) from e
    
    async def handle_symptom_input(
        self, 
        session: SessionState, 
        user_input: str, 
        context: Dict[str, Any]
    ) -> Tuple[str, List[V2AgentMessage]]:
        """
        Handle symptom input - analyze behavior and generate dog perspective.
        
        This is the core business logic that:
        1. Searches for symptom in vector database
        2. Analyzes behavior with AI
        3. Generates dog perspective response
        
        Args:
            session: Current session state
            user_input: User's symptom description
            context: Additional context data
            
        Returns:
            Tuple of (next_event, messages)
            - next_event: "symptom_found" or "symptom_not_found"
            - messages: Dog agent responses
        """
        logger.info(f"Handling symptom input: '{user_input[:50]}...'")
        
        try:
            # Validate input length
            if len(user_input.strip()) < 10:
                # Input too short - ask for more detail
                agent_context = AgentContext(
                    session_id=session.session_id,
                    user_input=user_input,
                    message_type=MessageType.INSTRUCTION,
                    metadata={'instruction_type': 'describe_more'}
                )
                
                messages = await self.dog_agent.respond(agent_context)
                return "symptom_not_found", messages
            
            # Store symptom in session
            session.active_symptom = user_input.strip()
            
            # Search for similar symptoms in vector database
            search_results = await self.weaviate_service.vector_search(
                query=user_input,
                collection_name="Symptome",
                limit=3
            )
            
            if search_results and len(search_results) > 0:
                # Found matching symptoms - generate dog perspective
                
                # Get best match data
                best_match = search_results[0]
                match_data = best_match.get('text', '')
                match_score = best_match.get('score', 0.0)
                
                logger.info(f"Found symptom match with score {match_score}")
                
                # Create context for dog agent
                agent_context = AgentContext(
                    session_id=session.session_id,
                    user_input=user_input,
                    message_type=MessageType.RESPONSE,
                    metadata={
                        'response_mode': 'perspective_only',
                        'match_data': match_data,
                        'match_score': match_score
                    }
                )
                
                # Generate dog perspective
                messages = await self.dog_agent.respond(agent_context)
                
                # Add confirmation question
                confirmation_context = AgentContext(
                    session_id=session.session_id,
                    message_type=MessageType.QUESTION,
                    metadata={'question_type': 'confirmation'}
                )
                
                confirmation_messages = await self.dog_agent.respond(confirmation_context)
                messages.extend(confirmation_messages)
                
                return "symptom_found", messages
                
            else:
                # No matching symptoms found
                logger.info("No matching symptoms found in database")
                
                agent_context = AgentContext(
                    session_id=session.session_id,
                    user_input=user_input,
                    message_type=MessageType.ERROR,
                    metadata={'error_type': 'no_match'}
                )
                
                messages = await self.dog_agent.respond(agent_context)
                return "symptom_not_found", messages
                
        except Exception as e:
            logger.error(f"Error in symptom input handler: {e}")
            
            # Generate error message
            agent_context = AgentContext(
                session_id=session.session_id,
                user_input=user_input,
                message_type=MessageType.ERROR,
                metadata={'error_type': 'technical'}
            )
            
            messages = await self.dog_agent.respond(agent_context)
            return "symptom_not_found", messages
    
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
        
        try:
            # Validate input length
            if len(user_input.strip()) < 5:
                agent_context = AgentContext(
                    session_id=session.session_id,
                    user_input=user_input,
                    message_type=MessageType.INSTRUCTION,
                    metadata={'instruction_type': 'be_specific'}
                )
                
                messages = await self.dog_agent.respond(agent_context)
                return messages
            
            # Combine symptom and context for analysis
            symptom = session.active_symptom
            combined_input = f"Verhalten: {symptom}\nKontext: {user_input}"
            
            # Perform instinct analysis
            analysis_data = await self._analyze_instincts(symptom, user_input)
            
            # Generate diagnosis from dog perspective
            agent_context = AgentContext(
                session_id=session.session_id,
                user_input=combined_input,
                message_type=MessageType.RESPONSE,
                metadata={
                    'response_mode': 'diagnosis',
                    'analysis_data': analysis_data
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
            # Store feedback answer in session
            if not hasattr(session, 'feedback'):
                session.feedback = []
            
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
        logger.info(f"Handling feedback completion for session {session.session_id}")
        
        try:
            # Store final answer
            if not hasattr(session, 'feedback'):
                session.feedback = []
            
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
            instinct_results = await self.weaviate_service.vector_search(
                query=combined_query,
                collection_name="Instinkte",
                limit=5
            )
            
            # Use GPT to analyze and determine primary instinct
            if instinct_results:
                # Format instinct data for analysis
                instinct_descriptions = {}
                for result in instinct_results:
                    text = result.get('text', '')
                    if 'jagd' in text.lower():
                        instinct_descriptions['jagd'] = text
                    elif 'rudel' in text.lower():
                        instinct_descriptions['rudel'] = text
                    elif 'territorial' in text.lower():
                        instinct_descriptions['territorial'] = text
                    elif 'sexual' in text.lower():
                        instinct_descriptions['sexual'] = text
                
                # GPT analysis
                analysis_prompt = self.prompt_manager.get_prompt(
                    PromptType.COMBINED_INSTINCT,
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
            exercise_results = await self.weaviate_service.vector_search(
                query=symptom,
                collection_name="Erziehung",
                limit=3
            )
            
            if exercise_results and len(exercise_results) > 0:
                # Return best matching exercise
                best_exercise = exercise_results[0]
                return best_exercise.get('text', 'Keine spezifische Übung gefunden.')
            
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
            if not hasattr(session, 'feedback') or not session.feedback:
                return False
            
            # Prepare feedback data
            feedback_data = {
                'session_id': session.session_id,
                'symptom': getattr(session, 'active_symptom', ''),
                'responses': session.feedback,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            # Save to Redis
            if self.redis_service:
                success = self.redis_service.set(
                    f"feedback:{session.session_id}",
                    feedback_data,
                    expire=7776000  # 90 days
                )
            
            logger.info(f"Feedback saved for session {session.session_id}")
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
        return gpt_response[:100].strip()