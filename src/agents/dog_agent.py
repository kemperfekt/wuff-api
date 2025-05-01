# src/agents/dog_agent.py

import os
from typing import List, Dict, Any
from openai import OpenAI
from pydantic import BaseModel

from src.prompts.prompt_hundliche_wahrnehmung import hundliche_wahrnehmung

class DogResponse(BaseModel):
    """
    Antwort des Hund-Agenten in Hundeperspektive.
    Wird als {'text': str} serialisiert.
    """
    text: str

def init_openai_client() -> OpenAI:
    """
    Initialisiert den OpenAI-Client mit der Umgebungsvariable OPENAI_APIKEY.
    Wirft einen Fehler, wenn der Key nicht gesetzt ist.
    """
    api_key = os.getenv("OPENAI_APIKEY")
    if not api_key:
        raise RuntimeError("OpenAI APIKEY nicht gesetzt")
    return OpenAI(api_key=api_key)

def run_dog_agent(
    history: List[Dict[str, Any]],
    symptom_input: str
) -> Dict[str, Any]:
    """
    Führt den Hund-Agenten aus:
    - history: bisherige Conversation-History (role, content) – kann für Kontext genutzt werden
    - symptom_input: Beschreibung des Verhaltens durch den Menschen

    Gibt ein Dictionary {'text': ...} zurück, das die Erlebniserklärung des Hundes enthält.
    """
    client = init_openai_client()

    # System-Prompt mit Hundeperspektive
    messages = [
        {"role": "system", "content": hundliche_wahrnehmung},
        {"role": "user",   "content": symptom_input},
    ]

    # API-Call
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=messages,
    )

    # Erster Choice-Text
    text = response.choices[0].message.content.strip()
    return DogResponse(text=text).dict()
