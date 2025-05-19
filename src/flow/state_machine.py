# src/flow/state_machine.py
from typing import Dict, Any, Callable, Optional
from src.models.flow_models import FlowStep
from src.state.session_state import SessionState

class StateMachine:
    """Zustandsautomat für Konversationsfluss"""
    
    def __init__(self):
        # Event-Handler: {current_state: {event: (next_state, handler)}}
        self.transitions = {}
    
    def add_transition(self, 
                      current_state: FlowStep, 
                      event: str, 
                      next_state: FlowStep, 
                      handler: Optional[Callable[[SessionState, Dict[str, Any]], Any]] = None):
        """Fügt eine Transition hinzu"""
        if current_state not in self.transitions:
            self.transitions[current_state] = {}
        
        self.transitions[current_state][event] = (next_state, handler)
    
    def process_event(self, 
                    session: SessionState, 
                    event: str, 
                    data: Optional[Dict[str, Any]] = None) -> bool:
        """Verarbeitet ein Event und führt Zustandsübergang durch"""
        current_state = session.current_step
        data = data or {}
        
        # Prüfe, ob eine Transition existiert
        if current_state in self.transitions and event in self.transitions[current_state]:
            next_state, handler = self.transitions[current_state][event]
            
            # Zustand aktualisieren
            session.current_step = next_state
            
            # Handler ausführen, falls vorhanden
            if handler:
                handler(session, data)
            
            return True
        
        return False  # Keine passende Transition