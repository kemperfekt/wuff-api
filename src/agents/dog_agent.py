# src/agents/dog_agent.py
from typing import List, Dict, Optional, Any
from src.agents.base_agent import BaseAgent
from src.models.flow_models import AgentMessage
from src.services.gpt_service import ask_gpt
from src.services.retrieval import get_symptom_info
from src.state.session_state import sessions

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
            
        # Symptomprüfung durchführen
        match = await self._check_symptom(user_input)
        
        if not match:
            # Kein bekanntes Verhalten gefunden
            messages.append(AgentMessage(
                sender=self.role,
                text="Hm, das klingt für mich nicht nach typischem Hundeverhalten. Magst du es nochmal anders beschreiben?"
            ))
            return messages + self._get_greeting_messages()
        
        # Hundeperspektive generieren
        dog_view = await self._generate_dog_perspective(match, user_input)
        messages.append(AgentMessage(sender=self.role, text=dog_view))
        
        # Übungsvorschlag generieren
        exercise = await self._generate_exercise(match, user_input)
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
        
        return messages
    
    def _get_greeting_messages(self) -> List[AgentMessage]:
        """Gibt die Begrüßungsnachrichten zurück"""
        return [
            AgentMessage(sender=self.role, text=self.greeting_text),
            AgentMessage(sender=self.role, text="Was ist los? Beschreib mir bitte, was du beobachtet hast.")
        ]
    
    async def _check_symptom(self, symptom: str) -> str:
        """Prüft, ob das Symptom bekannt ist (mit async)"""
        # Hier könntest du die get_symptom_info-Funktion async machen
        # Für jetzt verwenden wir die bestehende Funktion
        return get_symptom_info(symptom)
    
    async def _generate_dog_perspective(self, match: str, symptom: str) -> str:
        """Generiert die Hundeperspektive (mit async)"""
        prompt = (
            f"Ich bin ein Hund und habe dieses Verhalten gezeigt:\n'{symptom}'\n\n"
            "Hier ist eine Beschreibung aus ähnlichen Situationen:\n"
            f"{match}\n\n"
            "Du bist ein Hund. Beschreibe ruhig und klar, wie du dieses Verhalten aus deiner Sicht erlebt hast. "
            "Sprich nicht über Menschen oder Trainingsmethoden. Nenne keine Instinkte beim Namen. Keine Fantasie. Keine Fachbegriffe."
        )
        # Hier könntest du ask_gpt async machen
        return ask_gpt(prompt)
    
    async def _generate_exercise(self, match: str, symptom: str) -> str:
        """Generiert einen Übungsvorschlag (mit async)"""
        prompt = (
            f"Für folgendes Hundeverhalten:\n'{symptom}'\n\n"
            "Und folgende Beschreibung:\n"
            f"{match}\n\n"
            "Generiere eine kurze, praktische Übung (2-3 Sätze), die einem Hundebesitzer helfen kann, "
            "dieses Verhalten besser zu verstehen oder positiv zu beeinflussen."
        )
        # Hier könntest du ask_gpt async machen
        return ask_gpt(prompt)