# src/agents/agentic_dog_agent.py

"""
Agentic Dog Agent - LLM-driven conversation management for information collection.

This agent uses the ConversationPlanner and WeaviatePerspectiveTool to conduct
natural conversations that collect user information and provide dog perspectives.
"""

from typing import Optional, Dict, Any
import logging
from src.agents.base_agent import BaseAgent, AgentContext, MessageType, V2AgentMessage
from src.models.agentic_models import (
    ConversationContext, 
    InformationStatus, 
    AgenticResponse,
    ConversationPhase,
    ToolResult
)
from src.core.conversation_planner import ConversationPlanner
from src.tools.weaviate_perspective_tool import WeaviatePerspectiveTool
from src.core.exceptions import V2AgentError
from src.models.session_state import SessionState

logger = logging.getLogger(__name__)


class AgenticDogAgent(BaseAgent):
    """
    Agentic dog agent that uses LLM planning for natural information collection.
    
    Workflow:
    1. COLLECTING phase: Natural conversation to gather dog info
    2. PERSPECTIVE phase: Generate dog perspective using Weaviate + GPT
    3. HANDOFF phase: Ask if user wants to continue to static flow
    """
    
    def __init__(self, **kwargs):
        super().__init__(
            name="Balu",
            role="agentic_dog",
            **kwargs
        )
        
        # Initialize agentic components
        self.conversation_planner = ConversationPlanner(self.gpt_service)
        self.perspective_tool = WeaviatePerspectiveTool(
            self.weaviate_service, 
            self.gpt_service
        )
        
        self.logger = logging.getLogger(f"{__name__}.AgenticDogAgent")
    
    async def respond(self, context: AgentContext) -> AgenticResponse:
        """
        Generate agentic response based on conversation context.
        
        Args:
            context: Agent context with user input and session info
            
        Returns:
            AgenticResponse with message and metadata
        """
        try:
            # Build conversation context from session
            conv_context = self._build_conversation_context(context)
            
            # Handle greeting specially
            if context.message_type == MessageType.GREETING:
                return await self._handle_greeting(conv_context, context)
            
            # Determine current phase and respond accordingly
            current_phase = conv_context.information_status.get_current_phase()
            
            if current_phase == ConversationPhase.COLLECTING:
                return await self._handle_collection_phase(conv_context, context)
                
            elif current_phase == ConversationPhase.PERSPECTIVE:
                return await self._handle_perspective_phase(conv_context, context)
                
            elif current_phase == ConversationPhase.HANDOFF:
                return await self._handle_handoff_phase(conv_context, context)
                
            else:
                # Phase completed, should transition to static flow
                return self._create_transition_response(conv_context)
                
        except Exception as e:
            self.logger.error(f"Agentic response generation failed: {e}", exc_info=True)
            return self._create_error_response(str(e))
    
    async def _handle_greeting(self,
                             conv_context: ConversationContext,
                             agent_context: AgentContext) -> AgenticResponse:
        """Handle initial greeting with proper introduction"""
        
        # Generate a proper greeting introducing Balu and asking about the problem
        greeting_prompt = """Du bist Balu, ein freundlicher Labrador-Rüde der Hundeverhalten aus Hundeperspektive erklärt.
        
Generiere eine freundliche Begrüßung in der du:
1. Dich kurz als Balu vorstellst
2. Erklärst, dass du Hundeverhalten aus der Hundeperspektive erklärst
3. Fragst, was bei ihnen los ist oder was sie beschäftigt

Die Begrüßung sollte authentisch, warm und einladend sein.
Verwende *Aktionen* in Sternchen für Hundeaktionen.
Halte es kurz (max. 2 Sätze).

Beispiel-Stil:
*schwanzwedel* Hallo! Ich bin Balu und erkläre dir gerne, warum wir Hunde uns manchmal so seltsam verhalten. Was beschäftigt dich denn mit deinem Vierbeiner?"""
        
        try:
            greeting = await self.gpt_service.complete(
                prompt=greeting_prompt,
                model="gpt-4o-mini",
                max_tokens=100,
                temperature=0.8
            )
            
            conv_context.track_llm_call(tokens_used=100)
            
            return AgenticResponse(
                message=greeting.strip(),
                phase=ConversationPhase.COLLECTING,
                information_collected=conv_context.information_status,
                should_transition=False,
                cost_info=self._get_cost_info(conv_context)
            )
            
        except Exception as e:
            self.logger.error(f"Greeting generation failed: {e}")
            # Fallback greeting
            return AgenticResponse(
                message="*schwanzwedel* Hallo! Ich bin Balu und helfe dir, das Verhalten deines Hundes zu verstehen. Was beschäftigt dich denn?",
                phase=ConversationPhase.COLLECTING,
                information_collected=conv_context.information_status,
                should_transition=False,
                cost_info=self._get_cost_info(conv_context)
            )
    
    async def _handle_collection_phase(self, 
                                     conv_context: ConversationContext,
                                     agent_context: AgentContext) -> AgenticResponse:
        """Handle information collection phase"""
        
        # Process user input to extract information
        await self._extract_information_from_input(conv_context, agent_context)
        
        # Debug logging for information status
        info = conv_context.information_status
        self.logger.info(f"Information status after extraction: dog_name={info.dog_name}, dog_breed={info.dog_breed}, main_concern={info.main_concern}")
        self.logger.info(f"All required collected: {info.all_required_collected()}")
        
        # Check if we now have all information
        if conv_context.information_status.all_required_collected():
            self.logger.info("All information collected, transitioning to perspective phase")
            # Move to perspective phase
            conv_context.information_status.perspective_given = False
            conv_context.update_phase()
            return await self._handle_perspective_phase(conv_context, agent_context)
        
        # Still need more information, plan next question
        self.logger.info(f"Still missing information: {info.get_missing_information()}")
        action_plan = await self.conversation_planner.plan_next_step(conv_context)
        
        return AgenticResponse(
            message=action_plan.next_question,
            phase=ConversationPhase.COLLECTING,
            information_collected=conv_context.information_status,
            should_transition=False,
            cost_info=self._get_cost_info(conv_context)
        )
    
    async def _handle_perspective_phase(self,
                                      conv_context: ConversationContext,
                                      agent_context: AgentContext) -> AgenticResponse:
        """Handle dog perspective generation phase"""
        
        info = conv_context.information_status
        
        # Generate dog perspective using the tool
        perspective_result = await self.perspective_tool.execute(
            symptom=info.main_concern,
            dog_name=info.dog_name,
            dog_breed=info.dog_breed,
            user_name=info.user_name
        )
        
        if perspective_result.success:
            # Mark perspective as given and move to handoff
            info.perspective_given = True
            conv_context.update_phase()
            
            return AgenticResponse(
                message=perspective_result.result,
                phase=ConversationPhase.PERSPECTIVE,
                information_collected=info,
                should_transition=False,
                tool_results=[perspective_result],
                cost_info=self._get_cost_info(conv_context)
            )
        else:
            # Perspective generation failed, return error
            error_msg = f"*nachdenklich* Entschuldige, ich brauche einen Moment... {perspective_result.error}"
            return self._create_error_response(error_msg)
    
    async def _handle_handoff_phase(self,
                                  conv_context: ConversationContext, 
                                  agent_context: AgentContext) -> AgenticResponse:
        """Handle handoff decision phase"""
        
        # Check user response for handoff decision
        user_input = agent_context.user_input.lower()
        
        if any(word in user_input for word in ["ja", "yes", "gerne", "weiter", "mehr"]):
            # User wants to continue - ready for handoff
            conv_context.information_status.ready_for_handoff = True
            conv_context.update_phase()
            
            return AgenticResponse(
                message="*schwanzwedel* Wunderbar! Dann schauen wir uns das genauer an...",
                phase=ConversationPhase.COMPLETED,
                information_collected=conv_context.information_status,
                should_transition=True,
                next_flow_step="WAIT_FOR_SYMPTOM",  # Transition to static flow
                cost_info=self._get_cost_info(conv_context)
            )
        
        elif any(word in user_input for word in ["nein", "no", "nicht", "später"]):
            # User doesn't want to continue
            return AgenticResponse(
                message="*verständnisvoll* Das ist völlig in Ordnung. Falls du später Fragen hast, bin ich da.",
                phase=ConversationPhase.COMPLETED,
                information_collected=conv_context.information_status,
                should_transition=False,
                cost_info=self._get_cost_info(conv_context)
            )
        
        else:
            # Ask the handoff question
            action_plan = self.conversation_planner.plan_handoff_question()
            return AgenticResponse(
                message=action_plan.next_question,
                phase=ConversationPhase.HANDOFF,
                information_collected=conv_context.information_status,
                should_transition=False,
                cost_info=self._get_cost_info(conv_context)
            )
    
    async def _extract_information_from_input(self,
                                            conv_context: ConversationContext,
                                            agent_context: AgentContext):
        """Extract information from user input and update context"""
        
        user_input = agent_context.user_input
        info = conv_context.information_status
        
        # Simple extraction logic (could be enhanced with NLP)
        input_lower = user_input.lower()
        
        # Extract dog name (look for patterns like "heißt X" or "ist X" or just a name)
        if not info.dog_name:
            # First check if it's a simple one-word name response
            words = user_input.split()
            if len(words) <= 3 and len(words) >= 1:
                # Check if it's likely just a name (capitalized, alphabetic)
                potential_name = words[0].strip(".,!?")
                if len(potential_name) > 1 and potential_name[0].isupper() and potential_name.isalpha():
                    info.dog_name = potential_name
                    self.logger.info(f"Extracted simple name: {potential_name}")
                    return  # Early return for simple name
            
            # Otherwise look for patterns
            name_patterns = ["heißt", "ist", "name", "mein hund"]
            for pattern in name_patterns:
                if pattern in input_lower:
                    # Simple name extraction (could be improved)
                    words = user_input.split()
                    for i, word in enumerate(words):
                        if pattern in word.lower() and i + 1 < len(words):
                            potential_name = words[i + 1].strip(".,!?")
                            if len(potential_name) > 1 and potential_name.isalpha():
                                info.dog_name = potential_name.capitalize()
                                break
        
        # Extract breed information
        if not info.dog_breed:
            # Common breeds (simple approach) - check longer names first
            breeds = [
                ("siberian husky", "Siberian Husky"),
                ("golden retriever", "Golden Retriever"), 
                ("border collie", "Border Collie"),
                ("deutscher schäferhund", "Deutscher Schäferhund"),
                ("labrador", "Labrador"),
                ("schäferhund", "Schäferhund"), 
                ("pudel", "Pudel"), 
                ("beagle", "Beagle"), 
                ("dackel", "Dackel"), 
                ("husky", "Husky"), 
                ("collie", "Collie"), 
                ("retriever", "Retriever"), 
                ("mischling", "Mischling"),
                ("terrier", "Terrier"), 
                ("spitz", "Spitz"), 
                ("bulldogge", "Bulldogge"), 
                ("boxer", "Boxer"), 
                ("rottweiler", "Rottweiler")
            ]
            for breed_key, breed_name in breeds:
                if breed_key in input_lower:
                    info.dog_breed = breed_name
                    self.logger.info(f"Extracted breed: {breed_name}")
                    break
        
        # Extract main concern (if it looks like a behavioral description)
        if not info.main_concern and len(user_input) > 20:
            # Behavioral keywords
            behavior_indicators = [
                "bellt", "zieht", "springt", "beißt", "knurrt", "jault",
                "macht", "problem", "schwierig", "sorge", "ängstlich"
            ]
            
            if any(indicator in input_lower for indicator in behavior_indicators):
                info.main_concern = user_input
        
        # Add message to conversation history
        conv_context.add_message("user", user_input)
    
    def _build_conversation_context(self, agent_context: AgentContext) -> ConversationContext:
        """Build conversation context from agent context and session"""
        
        # Create conversation context
        context = ConversationContext()
        
        # Initialize with basic information status
        context.information_status = InformationStatus()
        
        # Load existing information from agent context metadata if available
        # This will be populated by the flow handler with session data
        if 'session_state' in agent_context.metadata:
            session_state = agent_context.metadata['session_state']
            
            # Map session state fields to information status
            if hasattr(session_state, 'user_dog_name') and session_state.user_dog_name:
                context.information_status.dog_name = session_state.user_dog_name
            if hasattr(session_state, 'user_dog_breed') and session_state.user_dog_breed:
                context.information_status.dog_breed = session_state.user_dog_breed
            if hasattr(session_state, 'active_symptom') and session_state.active_symptom:
                context.information_status.main_concern = session_state.active_symptom
        
        return context
    
    def _create_transition_response(self, conv_context: ConversationContext) -> AgenticResponse:
        """Create response for transitioning to static flow"""
        return AgenticResponse(
            message="*aufgeregt* Dann lass uns schauen, wie wir dir und deinem Hund helfen können!",
            phase=ConversationPhase.COMPLETED,
            information_collected=conv_context.information_status,
            should_transition=True,
            next_flow_step="WAIT_FOR_SYMPTOM"
        )
    
    def _create_error_response(self, error_message: str) -> AgenticResponse:
        """Create error response"""
        return AgenticResponse(
            message=f"*nachdenklich* Entschuldige, da ist etwas schiefgelaufen. Könntest du es nochmal versuchen?",
            phase=ConversationPhase.COLLECTING,
            information_collected=InformationStatus(),
            should_transition=False
        )
    
    def get_supported_message_types(self):
        """Return list of message types this agent can generate."""
        from typing import List
        return [
            MessageType.GREETING,
            MessageType.QUESTION,
            MessageType.RESPONSE,
            MessageType.ERROR
        ]
    
    def _get_cost_info(self, conv_context: ConversationContext) -> Dict[str, Any]:
        """Get cost information for monitoring"""
        # Rough cost estimation for GPT-4o-mini
        # Input: ~$0.00015 per 1K tokens, Output: ~$0.0006 per 1K tokens
        estimated_cost_euros = (conv_context.total_tokens_used / 1000) * 0.0008
        
        return {
            "llm_calls": conv_context.llm_calls_made,
            "tokens_used": conv_context.total_tokens_used,
            "estimated_cost_euros": round(estimated_cost_euros, 4)
        }