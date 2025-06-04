# src/v2/models/session_state.py

from typing import Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field
from src.models.flow_models import FlowStep, AgentMessage


class AgentStatus(BaseModel):
    is_first_message: bool = True


class SymptomState(BaseModel):
    name: str
    asked_instincts: Dict[str, bool] = Field(default_factory=dict)
    instinct_answers: Dict[str, List[str]] = Field(default_factory=dict)
    diagnosis: Optional[str] = None
    diagnosis_set: bool = False


class SessionState(BaseModel):
    """
    Speichert den Zustand einer aktiven Sitzung – inkl. Agentenzustand, aktivem Symptom
    und Detailinformationen pro Symptom (z.B. gestellte Rückfragen, Antworten, Diagnose).
    """
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    agent_status: Dict[str, AgentStatus] = Field(default_factory=dict)
    active_symptom: str = ""
    symptoms: Dict[str, SymptomState] = Field(default_factory=dict)
    awaiting_diagnosis_confirmation: bool = False
    diagnosis_confirmed: bool = False
    current_step: FlowStep = FlowStep.GREETING
    feedback: List[str] = Field(default_factory=list)
    messages: List[AgentMessage] = Field(default_factory=list)
    match_distance: Optional[float] = None


class SessionStore:
    """
    Einfache In-Memory-Verwaltung mehrerer Sitzungen (z. B. pro Nutzer).
    """
    def __init__(self):
        self.sessions: Dict[str, SessionState] = {}

    def create_session(self) -> SessionState:
        session = SessionState()
        self.sessions[session.session_id] = session
        return session

    def get_or_create(self, session_id: str) -> SessionState:
        if session_id not in self.sessions:
            session = SessionState()
            session.session_id = session_id  # Use the provided session_id
            self.sessions[session_id] = session
            return session
        return self.sessions[session_id]


# Globale Session-Verwaltung aktivieren (z. B. Zugriff über sessions["debug"])
sessions = SessionStore()
