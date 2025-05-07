from pydantic import BaseModel
from typing import Dict


class AgentStatus(BaseModel):
    is_first_message: bool = True


class SymptomState(BaseModel):
    name: str
    asked_instincts: Dict[str, bool] = {}
    diagnosis_set: bool = False


class SessionState(BaseModel):
    """
    Speichert den Zustand einer aktiven Sitzung – inkl. Agentenzustand, aktivem Symptom
    und Detailinformationen pro Symptom (z. B. gestellte Rückfragen, Diagnose).
    """
    agent_status: Dict[str, AgentStatus] = {}
    active_symptom: str = ""
    symptoms: Dict[str, SymptomState] = {}