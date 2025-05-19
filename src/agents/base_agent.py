# src/agents/base_agent.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from src.models.flow_models import AgentMessage

class BaseAgent(ABC):
    """Basisklasse für alle Agenten"""
    
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
    
    @abstractmethod
    async def respond(self, 
                     user_input: str, 
                     session_id: str, 
                     context: Optional[Dict[str, Any]] = None) -> List[AgentMessage]:
        """
        Verarbeitet eine Benutzereingabe und generiert Antworten.
        
        Args:
            user_input: Text des Benutzers
            session_id: ID der aktuellen Session
            context: Optionaler Kontext (z.B. ist_erste_nachricht)
            
        Returns:
            Liste von AgentMessage-Objekten als Antwort
        """
        pass