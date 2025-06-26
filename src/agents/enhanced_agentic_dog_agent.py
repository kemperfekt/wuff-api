# src/agents/enhanced_agentic_dog_agent.py

"""
Enhanced Agentic Dog Agent - Uses the new architecture components for natural conversation.

This agent replaces the original AgenticDogAgent with improved information extraction,
conversation memory, and adaptive planning for a more natural conversation flow.
"""

from typing import Optional, Dict, Any
import logging

from src.agents.base_agent import BaseAgent, AgentContext, MessageType, V2AgentMessage
from src.models.agentic_models import AgenticResponse, ConversationPhase, ToolResult
from src.models.unified_state import UnifiedConversationState, ConversationMode
from src.core.information_extractor import InformationExtractor
from src.core.adaptive_conversation_planner import AdaptiveConversationPlanner
from src.core.handoff_manager import HandoffManager
from src.tools.weaviate_perspective_tool import WeaviatePerspectiveTool
from src.core.exceptions import V2AgentError
from src.models.session_state import SessionState

logger = logging.getLogger(__name__)


class EnhancedAgenticDogAgent(BaseAgent):
    """
    Enhanced agentic dog agent using the new architecture components.
    
    Key improvements:
    - LLM-based information extraction
    - Conversation memory and context
    - Adaptive conversation planning
    - Seamless handoff management
    """
    
    def __init__(self, **kwargs):
        super().__init__(
            name="Balu",
            role="agentic_dog",
            **kwargs
        )
        
        # Initialize new components
        self.information_extractor = InformationExtractor(self.gpt_service)
        self.conversation_planner = AdaptiveConversationPlanner(
            self.gpt_service, 
            self.prompt_manager
        )
        self.handoff_manager = HandoffManager()
        self.perspective_tool = WeaviatePerspectiveTool(
            self.weaviate_service,
            self.gpt_service
        )
        
        # State management (temporary until session integration)
        self._conversation_states: Dict[str, UnifiedConversationState] = {}
        
        self.logger = logging.getLogger(f"{__name__}.EnhancedAgenticDogAgent")
    
    async def respond(self, context: AgentContext) -> AgenticResponse:
        """
        Generate enhanced agentic response.
        
        Args:
            context: Agent context with user input and session info
            
        Returns:
            AgenticResponse with message and metadata
        """
        try:
            # Get or create unified state
            state = self._get_unified_state(context)
            
            # Handle greeting specially
            if context.message_type == MessageType.GREETING:
                return await self._handle_greeting(state, context)
            
            # Handle different conversation phases
            if state.current_phase == ConversationPhase.COLLECTING:
                return await self._handle_collection_phase(state, context)
            elif state.current_phase == ConversationPhase.PERSPECTIVE:
                return await self._handle_perspective_phase(state, context)
            elif state.current_phase == ConversationPhase.HANDOFF:
                return await self._handle_handoff_phase(state, context)
            elif state.current_phase == ConversationPhase.INSTINCT_ANALYSIS:
                return await self._handle_instinct_analysis_phase(state, context)
            elif state.current_phase == ConversationPhase.EXERCISE_OFFER:
                return await self._handle_exercise_offer_phase(state, context)
            else:
                return self._create_completion_response(state)
                
        except Exception as e:
            self.logger.error(f"Enhanced agentic response failed: {e}", exc_info=True)
            return self._create_error_response(str(e))
    
    def _get_unified_state(self, context: AgentContext) -> UnifiedConversationState:
        """Get or create unified conversation state"""
        session_id = context.session_id
        
        if session_id not in self._conversation_states:
            # Create new state
            state = UnifiedConversationState(session_id=session_id)
            
            # Load existing information from session if available
            if 'session_state' in context.metadata:
                self._sync_from_session_state(state, context.metadata['session_state'])
            
            self._conversation_states[session_id] = state
        
        return self._conversation_states[session_id]
    
    def _sync_from_session_state(self, state: UnifiedConversationState, session_state: SessionState):
        """Sync unified state from existing session state"""
        if hasattr(session_state, 'user_dog_name') and session_state.user_dog_name:
            state.dog_name = session_state.user_dog_name
            state.confidence["dog_name"] = 0.9
        
        if hasattr(session_state, 'user_dog_breed') and session_state.user_dog_breed:
            state.dog_breed = session_state.user_dog_breed
            state.confidence["dog_breed"] = 0.9
        
        if hasattr(session_state, 'active_symptom') and session_state.active_symptom:
            state.main_concern = session_state.active_symptom
            state.confidence["main_concern"] = 0.9
        
        if hasattr(session_state, 'user_name') and session_state.user_name:
            state.user_name = session_state.user_name
            state.confidence["user_name"] = 0.9
    
    async def _handle_greeting(
        self, 
        state: UnifiedConversationState,
        context: AgentContext
    ) -> AgenticResponse:
        """Handle initial greeting"""
        
        greeting_message = await self._generate_greeting()
        
        # Add to conversation memory
        state.memory.add_turn(
            user_input="",
            agent_response=greeting_message,
            extracted_info={}
        )
        
        return AgenticResponse(
            message=greeting_message,
            phase=ConversationPhase.COLLECTING,
            information_collected=self._convert_to_information_status(state),
            should_transition=False,
            cost_info=self._get_cost_info(state)
        )
    
    async def _generate_greeting(self) -> str:
        """Generate a warm greeting"""
        greeting_prompt = """Du bist Balu, ein weiser und freundlicher Labrador, der Menschen hilft, ihre Hunde zu verstehen.

Generiere eine warmherzige Begrüßung, die:
1. Dich kurz als Balu vorstellt
2. Erklärt, dass du Hundeverhalten aus Hundeperspektive erklärst
3. Offen nach dem Problem fragt

Stil:
- Maximal EINE emotionale Beschreibung am Anfang: *neugierig*, *aufmerksam*, *interessiert*
- Keine Lautäußerungen wie "Wuff" oder ähnliches
- 2-3 Sätze für eine warme, einladende Begrüßung
- Authentisch und zurückhaltend

Beispiel: "*aufmerksam* Hallo! Ich bin Balu und helfe dir gerne zu verstehen, warum wir Hunde manchmal so handeln. Was beschäftigt dich denn mit deinem Vierbeiner?"

Deine Begrüßung:"""
        
        try:
            response = await self.gpt_service.complete(
                prompt=greeting_prompt,
                model="gpt-4o-mini",
                max_tokens=120,  # Allow for warmer greetings
                temperature=0.8
            )
            return response.strip()
        except Exception:
            # Fallback greeting
            return "*schwanzwedel* Hallo! Ich bin Balu und helfe dir gerne, das Verhalten deines Hundes zu verstehen. Was beschäftigt dich denn?"
    
    async def _handle_collection_phase(
        self,
        state: UnifiedConversationState,
        context: AgentContext
    ) -> AgenticResponse:
        """Handle information collection phase"""
        
        user_input = context.user_input
        
        # Extract information from user input
        extracted_info = await self.information_extractor.extract_from_input(
            user_input, 
            self._convert_to_conversation_context(state)
        )
        
        # Update state with extracted information
        state.update_from_extraction(extracted_info)
        
        # Generate acknowledgment if something was extracted
        acknowledgment = await self.conversation_planner.generate_acknowledgment(
            state, extracted_info
        )
        
        # Plan next response
        action_plan = await self.conversation_planner.plan_next_response(
            state, 
            extracted_info.get("reasoning")
        )
        
        # Add to conversation memory
        agent_response = acknowledgment + " " + action_plan.next_question if acknowledgment else action_plan.next_question
        state.memory.add_turn(
            user_input=user_input,
            agent_response=agent_response,
            extracted_info=extracted_info
        )
        
        # Check if ready for perspective - merge collection + perspective
        if state.is_ready_for_perspective() and not state.perspective_generated and state.main_concern:
            # Generate perspective immediately after symptom extraction
            try:
                perspective_result = await self.perspective_tool.execute(
                    symptom=state.main_concern,
                    dog_name=state.dog_name,
                    dog_breed=state.dog_breed,
                    user_name=state.user_name
                )
                
                if perspective_result.success:
                    state.dog_perspective = perspective_result.result
                    state.perspective_generated = True
                    
                    # Combine acknowledgment with perspective and ask if they want to know more
                    handoff_question = f"Möchtest du mehr darüber erfahren, warum {state.dog_name or 'dein Hund'} das macht?"
                    combined_message = f"{agent_response}\n\n{perspective_result.result}\n\n{handoff_question}"
                    
                    state.current_phase = ConversationPhase.HANDOFF
                    
                    return AgenticResponse(
                        message=combined_message,
                        phase=ConversationPhase.HANDOFF,
                        information_collected=self._convert_to_information_status(state),
                        should_transition=False,
                        tool_results=[perspective_result],
                        cost_info=self._get_cost_info(state)
                    )
                else:
                    # Perspective tool failed but returned structured error
                    self.logger.warning(f"Perspective tool failed: {perspective_result.error}")
                    # Continue with fallback below
                    
            except Exception as e:
                # Perspective tool had unhandled exception (e.g., Weaviate down)
                self.logger.error(f"Perspective tool exception: {e}")
                # Continue with fallback below
            
            # Fallback: Generate simple perspective without Weaviate
            fallback_perspective = f"Das Verhalten von {state.dog_name or 'deinem Hund'} ist sehr typisch für uns Hunde. Es gibt meist gute Gründe dafür, auch wenn Menschen sie nicht sofort verstehen."
            handoff_question = f"Möchtest du mehr darüber erfahren, warum {state.dog_name or 'dein Hund'} das macht?"
            combined_message = f"{agent_response}\n\n{fallback_perspective}\n\n{handoff_question}"
            
            state.dog_perspective = fallback_perspective
            state.perspective_generated = True
            state.current_phase = ConversationPhase.HANDOFF
            
            return AgenticResponse(
                message=combined_message,
                phase=ConversationPhase.HANDOFF,
                information_collected=self._convert_to_information_status(state),
                should_transition=False,
                cost_info=self._get_cost_info(state)
            )
        
        return AgenticResponse(
            message=agent_response,
            phase=ConversationPhase.COLLECTING,
            information_collected=self._convert_to_information_status(state),
            should_transition=action_plan.should_handoff,
            cost_info=self._get_cost_info(state)
        )
    
    async def _handle_perspective_phase(
        self,
        state: UnifiedConversationState,
        context: AgentContext
    ) -> AgenticResponse:
        """Handle dog perspective generation"""
        
        # Generate perspective using the tool
        perspective_result = await self.perspective_tool.execute(
            symptom=state.main_concern,
            dog_name=state.dog_name,
            dog_breed=state.dog_breed,
            user_name=state.user_name
        )
        
        if perspective_result.success:
            # Store perspective
            state.dog_perspective = perspective_result.result
            state.perspective_generated = True
            state.current_phase = ConversationPhase.HANDOFF
            
            # Generate handoff question
            action_plan = self.conversation_planner._plan_handoff_question(state)
            
            # Combine perspective with handoff question
            combined_message = f"{perspective_result.result}\n\n{action_plan.next_question}"
            
            return AgenticResponse(
                message=combined_message,
                phase=ConversationPhase.HANDOFF,
                information_collected=self._convert_to_information_status(state),
                should_transition=False,
                tool_results=[perspective_result],
                cost_info=self._get_cost_info(state)
            )
        else:
            # Error in perspective generation
            error_msg = "*nachdenklich* Entschuldige, lass mich einen Moment überlegen..."
            return AgenticResponse(
                message=error_msg,
                phase=ConversationPhase.PERSPECTIVE,
                information_collected=self._convert_to_information_status(state),
                should_transition=False,
                cost_info=self._get_cost_info(state)
            )
    
    async def _handle_handoff_phase(
        self,
        state: UnifiedConversationState,
        context: AgentContext
    ) -> AgenticResponse:
        """Handle handoff decision phase - now leads to instinct analysis"""
        
        user_input = context.user_input.lower()
        
        # Check for positive response
        if any(word in user_input for word in ["ja", "yes", "gerne", "weiter", "mehr"]):
            # User wants to continue - move to instinct analysis
            state.current_phase = ConversationPhase.INSTINCT_ANALYSIS
            
            # Generate context-gathering question
            context_question = "Gut, dann brauche ich noch ein paar Informationen. Wie kam es zu der Situation? Wer war dabei und wo ist es passiert?"
            
            return AgenticResponse(
                message=context_question,
                phase=ConversationPhase.INSTINCT_ANALYSIS,
                information_collected=self._convert_to_information_status(state),
                should_transition=False,
                cost_info=self._get_cost_info(state)
            )
        
        elif any(word in user_input for word in ["nein", "no", "nicht", "später"]):
            # User doesn't want to continue
            return AgenticResponse(
                message="*verständnisvoll* Das ist völlig in Ordnung. Falls du später Fragen hast, bin ich da.",
                phase=ConversationPhase.COMPLETED,
                information_collected=self._convert_to_information_status(state),
                should_transition=False,
                cost_info=self._get_cost_info(state)
            )
        
        else:
            # Ask handoff question
            action_plan = self.conversation_planner._plan_handoff_question(state)
            return AgenticResponse(
                message=action_plan.next_question,
                phase=ConversationPhase.HANDOFF,
                information_collected=self._convert_to_information_status(state),
                should_transition=False,
                cost_info=self._get_cost_info(state)
            )
    
    def _convert_to_information_status(self, state: UnifiedConversationState):
        """Convert unified state to old InformationStatus for compatibility"""
        from src.models.agentic_models import InformationStatus
        
        info_status = InformationStatus()
        info_status.user_name = state.user_name
        info_status.dog_name = state.dog_name
        info_status.dog_breed = state.dog_breed
        info_status.main_concern = state.main_concern
        info_status.perspective_given = state.perspective_generated
        info_status.ready_for_handoff = state.handoff_ready
        
        return info_status
    
    def _convert_to_conversation_context(self, state: UnifiedConversationState):
        """Convert unified state to old ConversationContext for compatibility"""
        from src.models.agentic_models import ConversationContext
        
        context = ConversationContext()
        context.information_status = self._convert_to_information_status(state)
        context.llm_calls_made = state.llm_calls_count
        context.total_tokens_used = state.total_tokens_used
        
        # Convert memory to message history
        for turn in state.memory.turns:
            context.message_history.append({
                "role": "user",
                "content": turn.user_input
            })
            context.message_history.append({
                "role": "assistant", 
                "content": turn.agent_response
            })
        
        return context
    
    def _create_completion_response(self, state: UnifiedConversationState) -> AgenticResponse:
        """Create response for completed conversation"""
        return AgenticResponse(
            message="*zufrieden* Ich freue mich, dass ich dir helfen konnte!",
            phase=ConversationPhase.COMPLETED,
            information_collected=self._convert_to_information_status(state),
            should_transition=True,
            next_flow_step="WAIT_FOR_SYMPTOM",
            cost_info=self._get_cost_info(state)
        )
    
    def _create_error_response(self, error_msg: str) -> AgenticResponse:
        """Create error response"""
        from src.models.agentic_models import InformationStatus
        
        return AgenticResponse(
            message="*verwirrt* Entschuldige, da ist etwas schiefgelaufen. Könntest du das nochmal sagen?",
            phase=ConversationPhase.COLLECTING,
            information_collected=InformationStatus(),
            should_transition=False
        )
    
    def _get_cost_info(self, state: UnifiedConversationState) -> Dict[str, Any]:
        """Get cost information"""
        return {
            "llm_calls": state.llm_calls_count,
            "tokens_used": state.total_tokens_used,
            "estimated_cost_euros": state.get_cost_estimate()
        }
    
    async def _handle_instinct_analysis_phase(
        self,
        state: UnifiedConversationState,
        context: AgentContext
    ) -> AgenticResponse:
        """Handle instinct analysis phase - analyze context and provide diagnosis"""
        
        # Import the flow handlers to access existing analysis logic
        from src.core.enhanced_flow_handlers import EnhancedFlowHandlers
        from src.core.prompt_manager import PromptType
        
        # Create temporary handlers instance to use existing methods
        handlers = EnhancedFlowHandlers(
            gpt_service=self.gpt_service,
            weaviate_service=self.weaviate_service,
            prompt_manager=self.prompt_manager
        )
        
        # Analyze instincts using existing logic
        analysis_data = await handlers._analyze_instincts(
            state.main_concern,
            context.user_input  # This is the context info
        )
        
        # Generate diagnosis using the dog agent format
        diagnosis_prompt = self.prompt_manager.get_prompt(
            PromptType.DOG_INSTINCT_DIAGNOSIS,
            symptom=state.main_concern,
            context=context.user_input,
            jagd=analysis_data['all_instincts'].get('jagd', ''),
            rudel=analysis_data['all_instincts'].get('rudel', ''),
            territorial=analysis_data['all_instincts'].get('territorial', ''),
            sexual=analysis_data['all_instincts'].get('sexual', '')
        )
        
        diagnosis = await self.gpt_service.complete(
            prompt=diagnosis_prompt,
            system_prompt=self.prompt_manager.get_prompt(PromptType.BALU_AGENT_SYSTEM),
            max_tokens=400
        )
        
        # Ask if they want an exercise
        exercise_question = f"\n\nMöchtest du eine Anleitung, wie du mit {state.dog_name or 'deinem Hund'} üben kannst, dass sich das verbessert?"
        
        state.current_phase = ConversationPhase.EXERCISE_OFFER
        state.instinct_analysis = analysis_data
        
        return AgenticResponse(
            message=diagnosis + exercise_question,
            phase=ConversationPhase.EXERCISE_OFFER,
            information_collected=self._convert_to_information_status(state),
            should_transition=False,
            metadata={"instinct_analysis": analysis_data},
            cost_info=self._get_cost_info(state)
        )
    
    async def _handle_exercise_offer_phase(
        self,
        state: UnifiedConversationState,
        context: AgentContext
    ) -> AgenticResponse:
        """Handle exercise offer - provide training plan if requested"""
        
        user_input = context.user_input.lower()
        
        if any(word in user_input for word in ["ja", "yes", "gerne", "bitte"]):
            # User wants exercise - use existing logic
            from src.core.enhanced_flow_handlers import EnhancedFlowHandlers
            from src.core.prompt_manager import PromptType
            
            handlers = EnhancedFlowHandlers(
                gpt_service=self.gpt_service,
                weaviate_service=self.weaviate_service,
                prompt_manager=self.prompt_manager
            )
            
            # Find exercise using existing method
            exercise_text = await handlers._find_exercise(state.main_concern)
            
            # Format from dog perspective
            exercise_prompt = self.prompt_manager.get_prompt(
                PromptType.EXERCISE_TEMPLATE,
                symptom=state.main_concern,
                exercise_content=exercise_text
            )
            
            exercise_response = await self.gpt_service.complete(
                prompt=exercise_prompt,
                system_prompt=self.prompt_manager.get_prompt(PromptType.EXERCISE_SYSTEM),
                max_tokens=300
            )
            
            # Mark as completed
            state.current_phase = ConversationPhase.COMPLETED
            
            completion_msg = f"{exercise_response}\n\n*zufrieden* Das war's für heute! Viel Erfolg beim Üben!"
            
            return AgenticResponse(
                message=completion_msg,
                phase=ConversationPhase.COMPLETED,
                information_collected=self._convert_to_information_status(state),
                should_transition=False,
                cost_info=self._get_cost_info(state)
            )
        else:
            # User doesn't want exercise
            state.current_phase = ConversationPhase.COMPLETED
            
            return AgenticResponse(
                message="*verständnisvoll* Kein Problem! Ich hoffe, ich konnte dir trotzdem helfen. *schwanzwedel*",
                phase=ConversationPhase.COMPLETED,
                information_collected=self._convert_to_information_status(state),
                should_transition=False,
                cost_info=self._get_cost_info(state)
            )
    
    def get_supported_message_types(self):
        """Return supported message types"""
        return [
            MessageType.GREETING,
            MessageType.QUESTION,
            MessageType.RESPONSE,
            MessageType.ERROR
        ]
    
    async def prepare_handoff(self, session_id: str) -> Dict[str, Any]:
        """
        Prepare handoff package for session.
        
        Args:
            session_id: Session to prepare handoff for
            
        Returns:
            Handoff package as dict
        """
        if session_id not in self._conversation_states:
            raise V2AgentError(f"No conversation state found for session {session_id}")
        
        state = self._conversation_states[session_id]
        
        try:
            package = await self.handoff_manager.prepare_handoff(state)
            return package.to_dict()
        except Exception as e:
            self.logger.error(f"Handoff preparation failed: {e}")
            raise V2AgentError(f"Failed to prepare handoff: {str(e)}")
    
    def get_conversation_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation state for debugging/monitoring"""
        if session_id not in self._conversation_states:
            return None
        
        state = self._conversation_states[session_id]
        return {
            "session_id": state.session_id,
            "phase": state.current_phase.value,
            "completion_percentage": state.get_completion_percentage(),
            "missing_fields": state.get_missing_fields(),
            "confidence": state.confidence,
            "memory_summary": state.memory.to_dict(),
            "handoff_ready": state.is_ready_for_handoff()
        }