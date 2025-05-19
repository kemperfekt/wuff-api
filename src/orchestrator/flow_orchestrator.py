# src/flow/flow_orchestrator.py
from typing import List, Dict, Any
from src.models.flow_models import AgentMessage, FlowStep
from src.state.session_state import SessionState, sessions
from src.agents.dog_agent import DogAgent
from src.agents.companion_agent import CompanionAgent
from src.flow.state_machine import StateMachine
from src.services.gpt_service import validate_user_input

class FlowOrchestrator:
    """Orchestriert den Konversationsfluss"""
    
    def __init__(self):
        self.dog_agent = DogAgent()
        self.companion_agent = CompanionAgent()
        self.state_machine = StateMachine()
        
        # State Machine konfigurieren
        self._setup_state_machine()
    
    def _setup_state_machine(self):
        """Konfiguriert die State Machine mit allen Übergängen"""
        
        # GREETING -> WAIT_FOR_SYMPTOM
        self.state_machine.add_transition(
            FlowStep.GREETING,
            "START",
            FlowStep.WAIT_FOR_SYMPTOM,
            self._handle_greeting
        )
        
        # WAIT_FOR_SYMPTOM -> Übergänge
        self.state_machine.add_transition(
            FlowStep.WAIT_FOR_SYMPTOM,
            "VALID_SYMPTOM",
            FlowStep.WAIT_FOR_CONFIRMATION,
            self._handle_valid_symptom
        )
        
        self.state_machine.add_transition(
            FlowStep.WAIT_FOR_SYMPTOM,
            "INVALID_SYMPTOM",
            FlowStep.WAIT_FOR_SYMPTOM,
            self._handle_invalid_symptom
        )
        
        # WAIT_FOR_CONFIRMATION -> Übergänge
        self.state_machine.add_transition(
            FlowStep.WAIT_FOR_CONFIRMATION,
            "CONFIRMED",
            FlowStep.WAIT_FOR_CONTEXT,
            self._handle_confirmation
        )
        
        self.state_machine.add_transition(
            FlowStep.WAIT_FOR_CONFIRMATION,
            "REJECTED",
            FlowStep.END_OR_RESTART,
            self._handle_rejection
        )
        
        # Weitere Übergänge...
    
    def _handle_greeting(self, session: SessionState, data: Dict[str, Any]):
        """Handler für den Übergang von GREETING zu WAIT_FOR_SYMPTOM"""
        messages = self.dog_agent.respond("", session.session_id, {"is_first_message": True})
        for msg in messages:
            session.messages.append(msg)
    
    def _handle_valid_symptom(self, session: SessionState, data: Dict[str, Any]):
        """Handler für gültiges Symptom"""
        user_input = data.get("user_input", "")
        session.active_symptom = user_input
        
        # Hundeperspektive generieren und zur Session hinzufügen
        messages = self.dog_agent.respond(user_input, session.session_id)
        for msg in messages:
            session.messages.append(msg)
    
    # Weitere Handler-Methoden...
    
    async def handle_message(self, session_id: str, user_input: str) -> List[AgentMessage]:
        """
        Verarbeitet eine Benutzernachricht.
        
        Args:
            session_id: ID der Session
            user_input: Nachricht des Benutzers
            
        Returns:
            Liste von Antwort-Nachrichten
        """
        # Session holen
        session = sessions.get_or_create(session_id)
        
        # Benutzernachricht speichern
        session.messages.append(AgentMessage(sender="user", text=user_input))
        
        # Restart-Befehle abfangen
        if user_input.lower() in ["neu", "restart", "von vorne"]:
            session.current_step = FlowStep.GREETING
            session.active_symptom = ""
            
            # Event auslösen
            self.state_machine.process_event(session, "START", {})
            
            # Antworten zurückgeben
            return [msg for msg in session.messages if msg.sender != "user"][-len(session.messages):]
        
        # Event basierend auf aktuellem Zustand bestimmen
        event = self._determine_event(session, user_input)
        
        # Event verarbeiten
        success = self.state_machine.process_event(
            session=session,
            event=event,
            data={"user_input": user_input}
        )
        
        if not success:
            # Fallback, wenn keine passende Transition gefunden wurde
            session.messages.append(AgentMessage(
                sender=self.dog_agent.role,
                text="Ich bin kurz verwirrt... lass uns neu starten."
            ))
            session.current_step = FlowStep.GREETING
            self.state_machine.process_event(session, "START", {})
        
        # Nur die neuen Nachrichten zurückgeben (seit der letzten Benutzereingabe)
        response_start_idx = len(session.messages) - 1  # -1 für die Benutzereingabe
        while response_start_idx > 0 and session.messages[response_start_idx-1].sender == "user":
            response_start_idx -= 1
        
        return session.messages[response_start_idx:]
    
    def _determine_event(self, session: SessionState, user_input: str) -> str:
        """Bestimmt das Event basierend auf Zustand und Eingabe"""
        current_step = session.current_step
        
        if current_step == FlowStep.WAIT_FOR_SYMPTOM:
            if len(user_input) < 10:
                return "INVALID_SYMPTOM"
            if not validate_user_input(user_input):
                return "INVALID_SYMPTOM"
            return "VALID_SYMPTOM"
        
        elif current_step == FlowStep.WAIT_FOR_CONFIRMATION:
            if "ja" in user_input.lower():
                return "CONFIRMED"
            elif "nein" in user_input.lower():
                return "REJECTED"
            return "UNCLEAR"
        
        # Weitere Zustandsprüfungen...
        
        return "DEFAULT"  # Fallback-Event