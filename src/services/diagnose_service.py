import os
import json
from typing import List, Dict, Any
import openai
from pydantic import BaseModel, Field, ValidationError

# Umgebungsvariable für OpenAI-Key
openai.api_key = os.getenv("OPENAI_APIKEY")

class FinalDiagnosisResponse(BaseModel):
    """
    Pydantic-Modell für die finale Diagnose-Antwort.
    Erwartet ein JSON-Objekt mit den Feldern:
      - message: Text der Diagnose
      - details: optionale strukturierte Zusatzinformationen
    """
    message: str = Field(..., description="Finale Diagnose-Nachricht für den Nutzer")
    details: Dict[str, Any] = Field(default_factory=dict, description="Optionale strukturierte Details zur Diagnose")


def get_final_diagnosis(session_log: List[Dict[str, Any]], known_facts: Dict[str, Any]) -> FinalDiagnosisResponse:
    """
    Baut das Prompt aus Session-Log und bekannten Fakten,
    führt den OpenAI-Call aus und validiert das Ergebnis.

    :param session_log: Liste der bisherigen Nachrichten aller Rollen
    :param known_facts: Dictionary mit gesammelten Fakten (z.B. Instinkte, Symptomdaten)
    :return: FinalDiagnosisResponse-Objekt mit message und details
    :raises RuntimeError: bei JSON-Parsing- oder Validierungsfehlern
    """
    # Prompt zusammenstellen
    instructions = (
        "Du bist ein empathischer Diagnostik-Assistent. "
        "Basierend auf dem bisherigen Gesprächsverlauf und bekannten Fakten "
        "formuliere eine abschließende Diagnose im JSON-Format mit den Feldern 'message' und 'details'."
    )
    prompt_content = {
        "session_log": session_log,
        "known_facts": known_facts,
        "instructions": instructions
    }

    messages = [
        {"role": "system", "content": "Du bist ein diagnostischer Assistent, der Diagnosen strukturiert liefert."},
        {"role": "user", "content": json.dumps(prompt_content, ensure_ascii=False)}
    ]

    # OpenAI-Request
    response = openai.ChatCompletion.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=messages,
        temperature=0.5,
    )
    raw = response.choices[0].message.content

    # JSON parsen und validieren
    try:
        parsed = json.loads(raw)
        return FinalDiagnosisResponse(**parsed)
    except (json.JSONDecodeError, ValidationError) as e:
        raise RuntimeError(
            f"Fehler bei Verarbeitung der Diagnose-Antwort: {e}\nRaw content: {raw}"
        )
