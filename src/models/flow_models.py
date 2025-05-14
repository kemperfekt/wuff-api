# src/models/flow_models.py

from pydantic import BaseModel
from typing import Dict


class AgentMessage(BaseModel):
    sender: str  # z. B. "coach", "dog", "mentor"
    text: str


class SymptomState(BaseModel):
    asked_instincts: Dict[str, bool] = {}  # z. B. "jagd": True
    instinct_answers: Dict[str, str] = {}  # Antwort des Menschen je Instinkt