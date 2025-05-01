# src/agents/coach_agent.py

import os
import json
from typing import Dict, Any, List
from openai import OpenAI
from pydantic import BaseModel, ValidationError

from src.prompts.system_prompt_coach import coach_prompt

# -----------------------------
# Pydantic-Modelle
# -----------------------------
class CoachQuestionResponse(BaseModel):
    question: str

class CoachDiagnosisResponse(BaseModel):
    diagnosis: Dict[str, Any]
    needs_background: bool = False  # ob nochmal Mentor ran muss

CoachResponse = CoachQuestionResponse | CoachDiagnosisResponse

# -----------------------------
# OpenAI-Client
# -----------------------------
def init_openai_client() -> OpenAI:
    key = os.getenv("OPENAI_APIKEY")
    if not key:
        raise RuntimeError("OpenAI APIKEY nicht gesetzt")
    return OpenAI(api_key=key)

# -----------------------------
# Coach-Agent
# -----------------------------
def run_coach_agent(
    history: List[Dict[str, Any]],
    dog_explanation: str
) -> Dict[str, Any]:
    """
    1) Nutzt dog_explanation + history, um gezielte Rückfragen
       (CoachQuestionResponse) oder finale Diagnose (CoachDiagnosisResponse) zu liefern.
    2) Wenn Diagnose, ggf. needs_background=True setzen.
    """
    client = init_openai_client()
    # Prompt zusammenbauen
    messages = [
        {"role":"system", "content": coach_prompt},
        {"role":"assistant_dog", "content": dog_explanation},
        *[m for m in history if m["role"].startswith("assistant_coach")]
    ]
    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL","gpt-4o-mini"),
        messages=messages
    )
    text = resp.choices[0].message.content
    # Versuch, JSON zu parsen
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        raise RuntimeError("Coach-Agent: Ungültige JSON-Antwort")
    # Entscheide nach Shapes
    if "question" in payload:
        return CoachQuestionResponse(**payload).dict()
    else:
        return CoachDiagnosisResponse(**payload).dict()
