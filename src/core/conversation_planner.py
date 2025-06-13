# src/core/conversation_planner.py

from typing import List, Dict, Any, Optional
import logging
import json
from src.models.agentic_models import (
    InformationStatus, 
    ActionPlan, 
    ConversationPhase,
    ConversationContext
)
from src.services.gpt_service import GPTService
from src.core.exceptions import V2ServiceError

logger = logging.getLogger(__name__)


class ConversationPlanner:
    """
    LLM-driven conversation planning for agentic information collection.
    
    Uses GPT-4o-mini to plan natural conversation steps based on what 
    information still needs to be collected and conversation context.
    """
    
    def __init__(self, gpt_service: GPTService):
        self.gpt = gpt_service
        self.logger = logging.getLogger(f"{__name__}.ConversationPlanner")
    
    async def plan_next_step(self, 
                           context: ConversationContext) -> ActionPlan:
        """
        Plan the next conversation step based on current context.
        
        Args:
            context: Current conversation context with history and information status
        
        Returns:
            ActionPlan with next question and metadata
        """
        try:
            # Check what information is still missing
            missing_info = context.information_status.get_missing_information()
            current_phase = context.information_status.get_current_phase()
            
            self.logger.debug(f"Planning for phase: {current_phase}, missing: {missing_info}")
            
            # Handle different conversation phases
            if current_phase == ConversationPhase.COLLECTING:
                return await self._plan_information_collection(context, missing_info)
            elif current_phase == ConversationPhase.HANDOFF:
                return self._plan_handoff_question()
            else:
                # Should not reach here in normal flow
                return self._plan_error_recovery()
                
        except Exception as e:
            self.logger.error(f"Planning failed: {e}", exc_info=True)
            return self._plan_error_recovery()
    
    async def _plan_information_collection(self, 
                                         context: ConversationContext,
                                         missing_info: List[str]) -> ActionPlan:
        """Plan next question for information collection phase"""
        
        if not missing_info:
            # All information collected, should not happen in this phase
            return self._plan_error_recovery()
        
        # Determine which information to ask for next
        next_info = self._prioritize_missing_information(missing_info, context)
        
        # Generate natural question using LLM
        question = await self._generate_natural_question(
            information_needed=next_info,
            context=context
        )
        
        return ActionPlan(
            next_question=question,
            information_needed=next_info,
            confidence=0.8,  # Good confidence for planned questions
            should_handoff=False,
            reasoning=f"Collecting missing information: {next_info}"
        )
    
    def _prioritize_missing_information(self, 
                                      missing_info: List[str],
                                      context: ConversationContext) -> str:
        """
        Decide which piece of missing information to ask for next.
        
        Priority order:
        1. dog_name (most personal, builds rapport)
        2. dog_breed (helps with context)
        3. main_concern (the actual problem to solve)
        """
        priority_order = ["dog_name", "dog_breed", "main_concern"]
        
        for priority_item in priority_order:
            if priority_item in missing_info:
                return priority_item
        
        # Fallback to first missing item
        return missing_info[0]
    
    async def _generate_natural_question(self, 
                                       information_needed: str,
                                       context: ConversationContext) -> str:
        """Generate a natural question using GPT for the needed information"""
        
        # Build context for the LLM
        conversation_context = self._build_conversation_context(context)
        
        # Create prompt for natural question generation
        prompt = self._build_question_prompt(information_needed, conversation_context)
        
        try:
            # Use GPT-4o-mini for cost efficiency
            response = await self.gpt.complete(
                prompt=prompt,
                model="gpt-4o-mini",
                max_tokens=100,
                temperature=0.7
            )
            
            # Track LLM usage for cost monitoring
            context.track_llm_call(tokens_used=100)  # Approximate
            
            # Clean up the response
            question = response.strip()
            if not question.endswith('?'):
                question += '?'
            
            return question
            
        except Exception as e:
            self.logger.warning(f"LLM question generation failed: {e}")
            # Fallback to predefined questions
            return self._get_fallback_question(information_needed)
    
    def _build_conversation_context(self, context: ConversationContext) -> str:
        """Build a summary of the conversation for the LLM"""
        
        # Get the last few messages for context
        recent_messages = context.message_history[-4:] if context.message_history else []
        
        context_parts = []
        
        # Add information status
        info = context.information_status
        if info.dog_name:
            context_parts.append(f"Hund heißt: {info.dog_name}")
        if info.dog_breed:
            context_parts.append(f"Rasse: {info.dog_breed}")
        if info.main_concern:
            context_parts.append(f"Problem: {info.main_concern}")
        
        # Add recent conversation
        if recent_messages:
            context_parts.append("Letzte Nachrichten:")
            for msg in recent_messages[-2:]:  # Just last 2 for brevity
                role = "Ich" if msg["role"] == "assistant" else "Mensch"
                context_parts.append(f"{role}: {msg['content']}")
        
        return " | ".join(context_parts) if context_parts else "Gesprächsbeginn"
    
    def _build_question_prompt(self, information_needed: str, conversation_context: str) -> str:
        """Build prompt for natural question generation"""
        
        # Define what we're asking for
        info_descriptions = {
            "dog_name": "den Namen des Hundes",
            "dog_breed": "die Rasse des Hundes", 
            "main_concern": "das Verhaltensproblem oder die Sorge"
        }
        
        info_desc = info_descriptions.get(information_needed, information_needed)
        
        prompt = f"""Du bist Balu, ein ruhiger und weiser Labrador. Du führst ein natürliches Gespräch mit einem Menschen über seinen Hund.

Kontext: {conversation_context}

Deine Aufgabe: Frage natürlich und warmherzig nach {info_desc}.

Regeln:
- Verwende Präsenz-Marker wie *aufmerksam-blick* oder *neugierig*
- Bleibe bei max. 1-2 Sätzen
- Klingt interessiert, nicht wie ein Formular
- Verwende bereits bekannte Informationen

Beispiele für gute Fragen:
- "*neugierig-schnüffel* Wie heißt denn dein Fellfreund?"
- "*aufmerksam* Welche Rasse ist Max denn?"
- "*mitfühlend* Was bereitet dir Sorgen bei Max?"

Deine Frage nach {info_desc}:"""

        return prompt
    
    def _get_fallback_question(self, information_needed: str) -> str:
        """Fallback questions if LLM generation fails"""
        fallback_questions = {
            "dog_name": "*neugierig* Wie heißt denn dein Hund?",
            "dog_breed": "*aufmerksam* Welche Rasse ist dein Hund?",
            "main_concern": "*mitfühlend* Was beschäftigt dich bei deinem Hund?"
        }
        
        return fallback_questions.get(
            information_needed, 
            "*aufmerksam* Erzähl mir mehr..."
        )
    
    def _plan_handoff_question(self) -> ActionPlan:
        """Plan the handoff question after information collection"""
        return ActionPlan(
            next_question="*hoffnungsvoll* Möchtest du mehr über das Verhalten deines Hundes erfahren?",
            information_needed="handoff_decision",
            confidence=1.0,
            should_handoff=True,
            reasoning="All information collected, asking for handoff to static flow"
        )
    
    def _plan_error_recovery(self) -> ActionPlan:
        """Plan recovery from planning errors"""
        return ActionPlan(
            next_question="*nachdenklich* Entschuldige, könntest du das nochmal sagen?",
            information_needed="clarification",
            confidence=0.3,
            should_handoff=False,
            reasoning="Error recovery - asking for clarification"
        )