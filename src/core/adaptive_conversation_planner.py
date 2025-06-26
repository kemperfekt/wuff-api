# src/core/adaptive_conversation_planner.py

"""
Adaptive Conversation Planner - Natural conversation flow management.

This module replaces the rigid ConversationPlanner with an adaptive system that
generates natural follow-up questions based on conversation context and missing information.
"""

import logging
from typing import List, Dict, Any, Optional
from src.models.agentic_models import ActionPlan, ConversationPhase
from src.models.unified_state import UnifiedConversationState
from src.services.gpt_service import GPTService
from src.core.prompt_manager import PromptManager, PromptType
from src.core.conversation_memory import ConversationMemory

logger = logging.getLogger(__name__)


class AdaptiveConversationPlanner:
    """
    Plans natural conversation flow based on context and missing information.
    
    Features:
    - Context-aware question generation
    - Priority-based information collection
    - Natural conversation transitions
    - Adaptive response to partial information
    """
    
    def __init__(self, gpt_service: GPTService, prompt_manager: Optional[PromptManager] = None):
        self.gpt = gpt_service
        self.prompt_manager = prompt_manager or PromptManager()
        self.logger = logging.getLogger(f"{__name__}.AdaptiveConversationPlanner")
        
        # Question templates for fallback (if LLM fails)
        self.fallback_questions = {
            "dog_name": [
                "*neugierig* Wie heißt denn dein Hund?",
                "*aufmerksam* Darf ich fragen, wie dein Fellfreund heißt?",
                "*freundlich* Und wie ist der Name deines Hundes?"
            ],
            "dog_breed": [
                "*interessiert* Welche Rasse ist {dog_name}?",
                "*neugierig-schnüffel* Was für eine Rasse ist dein Hund denn?",
                "*aufmerksam* Darf ich fragen, welche Rasse {dog_name} ist?"
            ],
            "main_concern": [
                "*mitfühlend* Was genau bereitet dir Sorgen bei {dog_name}?",
                "*verständnisvoll* Erzähl mir, was {dog_name} macht, das dich beunruhigt.",
                "*aufmerksam-ohren-spitz* Was ist denn das Verhalten, das dich beschäftigt?"
            ],
            "clarification": [
                "*nachdenklich* Kannst du mir das noch etwas genauer beschreiben?",
                "*interessiert* Erzähl mir mehr darüber...",
                "*aufmerksam* Das klingt wichtig - magst du es genauer erklären?"
            ]
        }
    
    async def plan_next_response(
        self, 
        state: UnifiedConversationState,
        last_extraction_reasoning: Optional[str] = None
    ) -> ActionPlan:
        """
        Plan the next response based on unified conversation state.
        
        Args:
            state: Current unified conversation state
            last_extraction_reasoning: Reasoning from last extraction (for context)
            
        Returns:
            ActionPlan with next question and metadata
        """
        try:
            # Check conversation phase
            if state.current_phase == ConversationPhase.COLLECTING:
                return await self._plan_collection_response(state, last_extraction_reasoning)
            elif state.current_phase == ConversationPhase.HANDOFF:
                return self._plan_handoff_question(state)
            else:
                # Should not happen in normal flow
                return self._plan_error_recovery()
                
        except Exception as e:
            self.logger.error(f"Planning failed: {e}", exc_info=True)
            return self._plan_error_recovery()
    
    async def _plan_collection_response(
        self,
        state: UnifiedConversationState,
        last_extraction_reasoning: Optional[str]
    ) -> ActionPlan:
        """Plan response for information collection phase"""
        
        missing_fields = state.get_missing_fields()
        
        if not missing_fields:
            # All information collected
            return ActionPlan(
                next_question="",
                information_needed="complete",
                confidence=1.0,
                should_handoff=True,
                reasoning="All required information has been collected"
            )
        
        # Check if we need clarification
        clarifications = state.memory.needs_clarification()
        if clarifications:
            field_to_clarify, reason = clarifications[0]
            return await self._generate_clarification_question(state, field_to_clarify, reason)
        
        # Determine priority field
        priority_field = self._prioritize_missing_field(missing_fields, state)
        
        # Generate natural question
        question = await self._generate_natural_question(state, priority_field, last_extraction_reasoning)
        
        return ActionPlan(
            next_question=question,
            information_needed=priority_field,
            confidence=0.9,
            should_handoff=False,
            reasoning=f"Asking for {priority_field} - still missing: {', '.join(missing_fields)}"
        )
    
    def _prioritize_missing_field(
        self, 
        missing_fields: List[str],
        state: UnifiedConversationState
    ) -> str:
        """
        Determine which field to ask for next based on conversation flow.
        
        Priority logic:
        1. If we have a concern but no dog info, get dog name first
        2. If we have dog name but no breed, get breed
        3. Otherwise, get the main concern
        """
        # If user already described a problem but we don't know the dog's name
        if "main_concern" not in missing_fields and "dog_name" in missing_fields:
            return "dog_name"
        
        # Natural order: name -> breed -> concern
        priority_order = ["dog_name", "dog_breed", "main_concern"]
        
        for field in priority_order:
            if field in missing_fields:
                return field
        
        return missing_fields[0]
    
    async def _generate_natural_question(
        self,
        state: UnifiedConversationState,
        target_field: str,
        last_extraction_reasoning: Optional[str]
    ) -> str:
        """Generate a natural question for the target field"""
        
        # Build context from state
        context_parts = []
        
        # Add what we know
        if state.dog_name:
            context_parts.append(f"Hund heißt: {state.dog_name}")
        if state.dog_breed:
            context_parts.append(f"Rasse: {state.dog_breed}")
        if state.main_concern:
            concern_preview = state.main_concern[:50] + "..." if len(state.main_concern) > 50 else state.main_concern
            context_parts.append(f"Problem: {concern_preview}")
        
        # Add conversation context
        last_user = state.memory.get_last_user_input()
        if last_user:
            context_parts.append(f"Letzte Nachricht: {last_user}")
        
        context = " | ".join(context_parts) if context_parts else "Gesprächsbeginn"
        
        # Add extraction reasoning if available
        if last_extraction_reasoning:
            context += f"\nExtraction notes: {last_extraction_reasoning}"
        
        # Build prompt
        prompt = self._build_question_generation_prompt(target_field, context, state)
        
        try:
            response = await self.gpt.complete(
                prompt=prompt,
                model="gpt-4o-mini",
                max_tokens=400,  # Allow for natural, empathetic responses
                temperature=0.85  # Natural but consistent
            )
            
            # Track usage
            state.track_llm_usage(tokens=400)
            
            question = response.strip()
            
            # Allow natural responses - don't force question marks
            return question
            
        except Exception as e:
            self.logger.warning(f"LLM question generation failed: {e}")
            return self._get_fallback_question(target_field, state)
    
    def _build_question_generation_prompt(
        self,
        target_field: str,
        context: str,
        state: UnifiedConversationState
    ) -> str:
        """Build prompt for natural question generation"""
        
        field_descriptions = {
            "dog_name": "den Namen des Hundes",
            "dog_breed": "die Rasse des Hundes",
            "main_concern": "das konkrete Verhaltensproblem oder die Sorge"
        }
        
        field_desc = field_descriptions.get(target_field, target_field)
        
        # Get conversation tone from recent messages
        conversation_style = "warm und freundlich"
        if state.memory.turn_counter > 2:
            conversation_style = "vertraut und entspannt"
        
        prompt = f"""Du bist Balu, ein weiser und freundlicher Labrador, der Menschen hilft, ihre Hunde zu verstehen.

Kontext: {context}
Gesprächston: {conversation_style}
Anzahl bisheriger Nachrichten: {state.memory.turn_counter}

Deine Aufgabe: Frage natürlich nach {field_desc}.

Wichtige Regeln:
- Nutze Hundeaktionen in *Sternchen* (z.B. *schwanzwedel*, *neugierig-schnüffel*)
- Sei warmherzig und empathisch  
- Führe eine natürliche, empathische Unterhaltung. Zeige Verständnis, stelle Rückfragen wo nötig, und baue auf dem auf, was der Nutzer gesagt hat.
- ERST reagiere auf das Gesagte, DANN leite natürlich zur fehlenden Info über
- Zeige echtes Interesse und Verständnis für die Situation
- Verwende bereits bekannte Namen natürlich im Gespräch
- Baue auf dem Gesprächsverlauf auf
- Stelle Fragen beiläufig, nicht wie in einem Interview
- Du kannst sowohl Aussagen als auch Fragen machen - folge dem natürlichen Gesprächsfluss
- Beispiel: "*verständnisvoll* Das klingt wirklich herausfordernd! Gerade bei längeren Spaziergängen kann das anstrengend werden. Wie heißt denn dein Vierbeiner?"

"""

        # Add specific guidance based on field
        if target_field == "dog_name" and state.main_concern:
            prompt += "\nHinweis: Der Nutzer hat bereits ein Problem beschrieben. Frage beiläufig nach dem Namen, während du Verständnis zeigst."
        elif target_field == "dog_breed" and state.dog_name:
            prompt += f"\nHinweis: Verwende den Namen '{state.dog_name}' in deiner Frage."
        elif target_field == "main_concern" and state.dog_name:
            prompt += f"\nHinweis: Sprich {state.dog_name} beim Namen an und zeige echtes Interesse."
        
        prompt += "\n\nDeine Frage:"
        
        return prompt
    
    async def _generate_clarification_question(
        self,
        state: UnifiedConversationState,
        field: str,
        reason: str
    ) -> ActionPlan:
        """Generate a clarification question for low-confidence information"""
        
        current_value = getattr(state, field, None)
        
        prompt = f"""Du bist Balu. Du bist dir nicht sicher, ob du etwas richtig verstanden hast.

Was du verstanden hast: {field} = "{current_value}"
Grund für Unsicherheit: {reason}

Frage freundlich nach, ob du es richtig verstanden hast. Sei vorsichtig und nicht aufdringlich.
Maximal 1-2 Sätze mit *Hundeaktion*.

Deine Nachfrage:"""
        
        try:
            response = await self.gpt.complete(
                prompt=prompt,
                model="gpt-4o-mini",
                max_tokens=150,  # Allow for more natural clarifications
                temperature=0.7
            )
            
            state.track_llm_usage(tokens=150)
            
            return ActionPlan(
                next_question=response.strip(),
                information_needed=f"clarify_{field}",
                confidence=0.7,
                should_handoff=False,
                reasoning=f"Clarifying {field}: {reason}"
            )
            
        except Exception:
            # Fallback clarification
            return ActionPlan(
                next_question="*unsicher* Habe ich das richtig verstanden?",
                information_needed=f"clarify_{field}",
                confidence=0.5,
                should_handoff=False,
                reasoning="Fallback clarification"
            )
    
    def _get_fallback_question(self, target_field: str, state: UnifiedConversationState) -> str:
        """Get fallback question if LLM fails"""
        import random
        
        questions = self.fallback_questions.get(target_field, self.fallback_questions["clarification"])
        question = random.choice(questions)
        
        # Personalize with known information
        if "{dog_name}" in question and state.dog_name:
            question = question.replace("{dog_name}", state.dog_name)
        
        return question
    
    def _plan_handoff_question(self, state: UnifiedConversationState) -> ActionPlan:
        """Plan the handoff question after perspective generation"""
        
        # Personalized handoff question
        if state.dog_name:
            question = f"*hoffnungsvoll* Möchtest du mehr darüber erfahren, wie du {state.dog_name} bei diesem Verhalten helfen kannst?"
        else:
            question = "*hoffnungsvoll* Möchtest du mehr über dieses Verhalten erfahren und wie du deinem Hund helfen kannst?"
        
        return ActionPlan(
            next_question=question,
            information_needed="handoff_decision",
            confidence=1.0,
            should_handoff=True,
            reasoning="Ready for handoff to detailed diagnostic flow"
        )
    
    def _plan_error_recovery(self) -> ActionPlan:
        """Plan recovery from errors"""
        return ActionPlan(
            next_question="*verwirrt* Entschuldige, da ist etwas schiefgelaufen. Kannst du das nochmal sagen?",
            information_needed="error_recovery",
            confidence=0.3,
            should_handoff=False,
            reasoning="Error recovery"
        )
    
    async def generate_acknowledgment(
        self,
        state: UnifiedConversationState,
        extracted_info: Dict[str, Any]
    ) -> Optional[str]:
        """
        Generate a brief acknowledgment when information is extracted.
        
        This helps make the conversation feel more natural by acknowledging
        what was understood before asking the next question.
        """
        # Only acknowledge if we extracted something significant
        extracted_facts = [
            k for k in ["dog_name", "dog_breed", "main_concern"]
            if extracted_info.get(k) and extracted_info.get("confidence", {}).get(k, 0) > 0.7
        ]
        
        if not extracted_facts:
            return None
        
        # Build acknowledgment prompt
        ack_parts = []
        if "dog_name" in extracted_facts:
            ack_parts.append(f"Name: {extracted_info['dog_name']}")
        if "dog_breed" in extracted_facts:
            ack_parts.append(f"Rasse: {extracted_info['dog_breed']}")
        if "main_concern" in extracted_facts:
            ack_parts.append("Verhalten verstanden")
        
        prompt = f"""Du bist Balu. Du hast gerade etwas Neues über den Hund erfahren:
{', '.join(ack_parts)}

Zeige kurz, dass du verstanden hast. Verwende maximal eine einfache Emotion.

Beispiele:
- "*aufmerksam* Ah, {extracted_info.get('dog_name', 'verstehe')}!"
- "Ein {extracted_info.get('dog_breed', 'toller Hund')} - die sind oft so!"
- "Das klingt herausfordernd."

Deine kurze Reaktion:"""
        
        try:
            response = await self.gpt.complete(
                prompt=prompt,
                model="gpt-4o-mini",
                max_tokens=50,  # Allow for natural acknowledgments
                temperature=0.9
            )
            
            return response.strip()
            
        except Exception:
            # Skip acknowledgment on error
            return None
    
    def _plan_handoff_question(self, state: UnifiedConversationState) -> ActionPlan:
        """Generate the handoff question for transitioning to static flow"""
        
        # Use consistent handoff question
        question = "*schwanzwedel* Möchtest du mehr darüber erfahren, warum {} das macht und wie ihr gemeinsam daran arbeiten könnt?".format(
            state.dog_name or "dein Hund"
        )
        
        return ActionPlan(
            next_question=question,
            information_needed="handoff_decision",
            confidence=1.0,  # High confidence - all required information collected
            should_handoff=True,
            reasoning="All information collected, offering detailed analysis"
        )