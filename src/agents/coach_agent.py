# src/agents/coach_agent.py

import os
import json
from typing import Any, Dict, List
from openai import OpenAI
from pydantic import BaseModel

from src.prompts.system_prompt_coach import coach_prompt
from src.services.retrieval import get_symptom_info, get_breed_info, get_instinkt_profile
from src.services.diagnose_service import get_final_diagnosis, FinalDiagnosisResponse

# -----------------------------
# Pydantic-Modelle
# -----------------------------
class CoachQuestionResponse(BaseModel):
    question: str

class CoachDiagnosisResponse(BaseModel):
    message: str
    details: Dict[str, Any]
    needs_background: bool = False

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
    dog_explanation: str,
    symptom_input: str,
    user_breed: str = None
) -> Dict[str, Any]:
    client = init_openai_client()

    # --- 1) RAG-Fakten holen (stubs in Tests überlagern diese Aufrufe) ---
    symptom = get_symptom_info(symptom_input)
    if user_breed:
        breed = get_breed_info(user_breed)
        instinct_profile = get_instinkt_profile(breed.gruppen_code)
    else:
        # sicherer Zugriff auf ersten Instinkt-Namen
        first_instinct = next(iter(symptom.instinkt_varianten), None)
        instinct_profile = get_instinkt_profile(first_instinct) if first_instinct else None

    # --- 2) Prompt-Kontext bauen ---
    ctx_lines = [
        f"**Hund erklärt:** {dog_explanation}",
        f"**Symptombeschreibung:** {symptom.beschreibung}",
        "**Instinktvarianten:**"
    ]
    for inst, txt in symptom.instinkt_varianten.items():
        ctx_lines.append(f"- {inst}: {txt}")
    if instinct_profile:
        ctx_lines.append(f"**Instinktprofil ({instinct_profile.gruppe}):** {instinct_profile.merkmale}")
    if user_breed and breed:
        ctx_lines.append(f"**Rasse ({breed.rassename}):** {breed.ursprungsland}")

    full_prompt = coach_prompt.replace("{{context}}", "\n".join(ctx_lines))

    # --- 3) LLM-Call für Rückfragen oder Diagnose ---
    messages = [
        {"role": "system",  "content": full_prompt},
        {"role": "assistant_dog", "content": dog_explanation},
        *[m for m in history if m["role"].startswith("assistant_coach")]
    ]
    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=messages
    )
    text = resp.choices[0].message.content.strip()

    # --- 4) JSON parsen & Response bauen ---
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        raise RuntimeError(f"Coach-Agent: Ungültige JSON-Antwort: {text}")

    if "questions" in payload:
        return CoachQuestionResponse(question=payload["questions"][0]).model_dump()
    else:
        final: FinalDiagnosisResponse = get_final_diagnosis(
            session_log=history + [{"role": "assistant_dog", "content": dog_explanation}],
            known_facts={"symptom": symptom.dict(), "instinktprofil": instinct_profile.dict() if instinct_profile else {}}
        )
        return CoachDiagnosisResponse(
            message=final.message,
            details=final.details,
            needs_background=final.needs_background
        ).model_dump()
