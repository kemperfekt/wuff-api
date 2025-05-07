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

    # 1) Fakten aus Weaviate ziehen
    symptom = get_symptom_info(symptom_input)
    # → symptom.instinktvarianten ist Dict[str,str]
    first_instinct: str = next(iter(symptom.instinktvarianten.keys()), None)  # nur der String-Name
    if user_breed:
        breed = get_breed_info(user_breed)
        instinct_profile = get_instinkt_profile(breed.gruppen_code)
    elif first_instinct:
        instinct_profile = get_instinkt_profile(first_instinct)
    else:
        instinct_profile = None

    # 2) Prompt-Kontext aufbauen
    context = [
        f"**Hund erklärt:** {dog_explanation}",
        f"**Symptombeschreibung:** {symptom.beschreibung[:200]}…",
        "**Instinktvarianten:**"
    ]
    for inst_name, text in symptom.instinktvarianten.items():
        context.append(f"- {inst_name}: {text[:100]}…")
    if instinct_profile:
        context.append(f"**Instinktprofil ({instinct_profile.gruppe}):** {instinct_profile.merkmale[:200]}…")
    if user_breed and breed:
        context.append(f"**Rasse ({breed.rassename}):** {breed.ursprungsland}")

    full_prompt = coach_prompt.replace("{{context}}", "\n".join(context))

    # 3) LLM-Aufruf
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

    # 4) JSON parsen
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        raise RuntimeError(f"Coach-Agent: Ungültige JSON-Antwort: {text}")

    # 5) Rückfragen- vs. Diagnose-Zweig
    if "questions" in payload:
        return CoachQuestionResponse(question=payload["questions"][0]).dict()
    else:
        final: FinalDiagnosisResponse = get_final_diagnosis(
            session_log=history + [{"role": "assistant_dog", "content": dog_explanation}],
            known_facts={
                "symptom": symptom.dict(),
                "instinktprofil": instinct_profile.dict() if instinct_profile else {}
            }
        )
        return CoachDiagnosisResponse(
            message=final.message,
            details=final.details,
            needs_background=final.needs_background
        ).dict()
