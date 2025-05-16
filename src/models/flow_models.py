# src/models/flow_models.py
# src/models/flow_models.py

from enum import Enum

class FlowStep(str, Enum):
    GREETING = "greeting"
    WAIT_FOR_SYMPTOM = "wait_for_symptom"
    SYMPTOM_ACK = "symptom_ack"
    ASK_DIAGNOSE = "ask_diagnose"
    WAIT_FOR_CONFIRMATION = "wait_for_confirmation"
    ASK_CONTEXT = "ask_context"
    WAIT_FOR_CONTEXT = "wait_for_context"
    FINAL_DIAGNOSIS = "final_diagnosis"
    END_OR_RESTART = "end_or_restart"
    FEEDBACK = "feedback"

from pydantic import BaseModel
from typing import Dict


class AgentMessage(BaseModel):
    sender: str  # z. B. "coach", "dog", "mentor"
    text: str


class SymptomState(BaseModel):
    asked_instincts: Dict[str, bool] = {}  # z. B. "jagd": True
    instinct_answers: Dict[str, str] = {}  # Antwort des Menschen je Instinkt</file>