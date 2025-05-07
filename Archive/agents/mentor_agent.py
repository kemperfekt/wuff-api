# src/agents/mentor_agent.py

import os
import json
from typing import Dict, Any, List
from openai import OpenAI
from pydantic import BaseModel

from src.prompts.system_prompt_mentor import mentor_prompt

class MentorResponse(BaseModel):
    explanation: str

def init_openai_client() -> OpenAI:
    key = os.getenv("OPENAI_APIKEY")
    if not key:
        raise RuntimeError("OpenAI APIKEY nicht gesetzt")
    return OpenAI(api_key=key)

def run_mentor_agent(
    history: List[Dict[str, Any]],
    coach_resp: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Liefert eine Hintergrund-Erklärung (Mentor) basierend auf bisherigen 
    History und der Coach-Diagnose oder -Frage.
    """
    client = init_openai_client()
    messages = [
        {"role":"system","content": mentor_prompt},
        {"role":"assistant_coach","content": json.dumps(coach_resp)},
    ]
    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL","gpt-4o-mini"),
        messages=messages
    )
    text = resp.choices[0].message.content
    return MentorResponse(explanation=text).dict()
