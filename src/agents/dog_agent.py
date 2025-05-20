# src/agents/dog_agent.py
from typing import List, Dict, Optional, Any
from src.agents.base_agent import BaseAgent
from src.models.flow_models import AgentMessage
from src.services.gpt_service import ask_gpt
from src.services.retrieval import get_symptom_info
from src.services.rag_service import RAGService
from src.state.session_state import sessions
from src.config.prompts import DOG_PERSPECTIVE_TEMPLATE, EXERCISE_TEMPLATE
from src.core.error_handling import with_error_handling, GPTServiceError, RAGServiceError

class DogAgent(BaseAgent):
    """Agent, der aus Hundeperspektive antwortet"""
    
    def __init__(self):
        super().__init__(name="Hund", role="dog")
        self.greeting_text = "Wuff! Schön, dass Du da bist. Bitte nenne mir ein Verhalten und ich schildere dir, wie ich es erlebe."
    
    async def respond(self, 
                     user_input: str, 
                     session_id: str, 
                     context: Optional[Dict[str, Any]] = None) -> List[AgentMessage]:
        """
        Verarbeitet eine Benutzereingabe und generiert Antworten.
        """
        context = context or {}
        messages = []
        
        # Session-Zustand abrufen
        state = sessions.get_or_create(session_id)
        is_first_message = context.get("is_first_message", False)
        
        # Begrüßung bei erster Nachricht
        if is_first_message:
            return self._get_greeting_messages()
        
        # Prüfe, ob Nutzer "ja" antwortet auf "Nochmal von vorne?"
        if user_input.lower() == "ja" and getattr(self, 'last_bot_message', "") == "Nochmal von vorne?":
            return self._get_greeting_messages()
            
        try:
            # Schritt 1: Symptomprüfung durchführen
            symptom_info = await self._check_symptom(user_input)
            
            if not symptom_info:
                # Kein bekanntes Verhalten gefunden
                messages.append(AgentMessage(
                    sender=self.role,
                    text="Hm, das klingt für mich nicht nach typischem Hundeverhalten. Magst du es nochmal anders beschreiben?"
                ))
                return messages + self._get_greeting_messages()
            
            # Schritt 2: Umfassende RAG-Analyse durchführen
            context_text = context.get("additional_context", "")
            analysis = await RAGService.get_comprehensive_analysis(user_input, context_text)
            
            # Schritt 3: Hundeperspektive generieren
            dog_view = await RAGService.generate_dog_perspective(user_input, analysis)
            messages.append(AgentMessage(sender=self.role, text=dog_view))
            
            # Schritt 4: Übung vorschlagen
            exercise = analysis.get("exercise", "Keine passende Übung gefunden")
            messages.append(AgentMessage(
                sender=self.role,
                text=f"Hier ist eine Übung, die zu deinem Fall passt: {exercise}. Gibt es ein weiteres Verhalten, das Du mit mir besprechen möchtest?"
            ))
            
            # Diagnose-Angebot
            messages.append(AgentMessage(
                sender=self.role,
                text="Nochmal von vorne?"
            ))
            
            # Session-State aktualisieren
            if state:
                state.active_symptom = user_input
            
            # Letzte Nachricht speichern
            self.last_bot_message = "Nochmal von vorne?"
            
        except Exception as e:
            print(f"❌ Fehler bei der Verarbeitung: {e}")
            messages.append(AgentMessage(
                sender=self.role,
                text="Es tut mir leid, ich habe gerade ein technisches Problem. Kannst du es später noch einmal versuchen?"
            ))
        
        return messages
    
    def _get_greeting_messages(self) -> List[AgentMessage]:
        """Gibt die Begrüßungsnachrichten zurück"""
        return [
            AgentMessage(sender=self.role, text=self.greeting_text),
            AgentMessage(sender=self.role, text="Was ist los? Beschreib mir bitte, was du beobachtet hast.")
        ]
    
    @with_error_handling(RAGServiceError, "Ich habe keine spezifischen Informationen zu diesem Verhalten, aber ich versuche, es aus Hundesicht zu verstehen.")
    async def _check_symptom(self, symptom: str) -> str:
        """Prüft, ob das Symptom bekannt ist (mit async)"""
        result = await get_symptom_info(symptom)
        return result
    
    @with_error_handling(GPTServiceError, "Als Hund fühle ich mich manchmal unsicher und verwirrt. In dieser Situation würde ich mich wahrscheinlich ähnlich fühlen.")
    async def _generate_dog_perspective(self, match: str, symptom: str) -> str:
        """Generiert die Hundeperspektive (mit async)"""
        # Verwende den Prompt aus der Konfiguration
        prompt = DOG_PERSPECTIVE_TEMPLATE.format(symptom=symptom, match=match)
        return await ask_gpt(prompt)
    
    @with_error_handling(GPTServiceError, "Versuche, klare Grenzen zu setzen und dem Hund alternative Beschäftigungsmöglichkeiten anzubieten.")
    async def _generate_exercise(self, match: str, symptom: str) -> str:
        """Generiert einen Übungsvorschlag (mit async)"""
        # Verwende den Prompt aus der Konfiguration
        prompt = EXERCISE_TEMPLATE.format(symptom=symptom, match=match)
        return await ask_gpt(prompt)