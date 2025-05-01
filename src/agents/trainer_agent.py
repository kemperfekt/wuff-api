# src/agents/trainer_agent.py

import os
import json
from typing import Dict, Any, List
from openai import OpenAI
from pydantic import BaseModel

from src.prompts.system_prompt_trainer import trainer_prompt

class TrainingPlan(BaseModel):
    plan: str
    tips: List[str]

def init_openai_client() -> OpenAI:
    key = os.getenv("OPENAI_APIKEY")
    if not key:
        raise RuntimeError("OpenAI APIKEY nicht gesetzt")
    return OpenAI(api_key=key)

def run_trainer_agent(
    history: List[Dict[str, Any]],
    mentor_resp: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Erzeugt Trainingsplan und Tipps basierend auf gesamter Diskussion (history)
    und der Mentor-Erklärung.
    """
    client = init_openai_client()
    messages = [
        {"role":"system","content": trainer_prompt},
        {"role":"assistant_mentor","content": json.dumps(mentor_resp)},
    ]
    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL","gpt-4o-mini"),
        messages=messages
    )
    # Parse JSON
    payload = json.loads(resp.choices[0].message.content)
    return TrainingPlan(**payload).dict()
