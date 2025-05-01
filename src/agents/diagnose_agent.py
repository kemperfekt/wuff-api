# src/agents/diagnose_agent.py

import os
import json
from typing import List, Dict, Any
from openai import OpenAI
from pydantic import ValidationError

from src.models.symptom_models import SymptomInfo
from src.models.instinct_models import InstinctClassification
from src.services.retrieval import get_symptom_info
from src.services.diagnose_service import get_final_diagnosis, FinalDiagnosisResponse

from src.prompts.prompt_hundliche_wahrnehmung import hundliche_wahrnehmung
from src.prompts.system_prompt_diagnose import diagnose_instinktklassifikation
from src.prompts.system_prompt_questions import diagnose_rueckfragen


def init_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_APIKEY")
    if not api_key:
        raise RuntimeError("OpenAI APIKEY nicht gesetzt")
    return OpenAI(api_key=api_key)


def classify_instincts(text: str, client: OpenAI) -> InstinctClassification:
    functions = [
        {
            "name": "classify_instincts",
            "description": "Klassifiziere Instinkte in 'known' und 'uncertain'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "known_instincts": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Instinkte, die klar erkennbar sind."
                    },
                    "uncertain_instincts": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Instinkte, die unklar bleiben und abgefragt werden müssen."
                    }
                },
                "required": ["known_instincts", "uncertain_instincts"]
            }
        }
    ]

    system_prompt = hundliche_wahrnehmung + "\n\n" + diagnose_instinktklassifikation

    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ],
        functions=functions,
        function_call={"name": "classify_instincts"}
    )

    func_call = response.choices[0].message.function_call
    args_json = func_call.arguments

    try:
        classification = InstinctClassification.parse_raw(args_json)
        return classification
    except ValidationError as e:
        raise RuntimeError(f"InstinctClassification-Parsing fehlgeschlagen: {e}")


def run_diagnose_agent(session_id: str, user_input: str) -> Dict[str, Any]:
    """
    Fortsetzen des Diagnose-Flows:
    - Lädt intern den Session-State via session_id
    - Führt Instinkt-Klassifikation, Rückfragen oder finale Diagnose aus
    - Speichert den Session-State
    """
    from src.services.state import load_state, save_state

    # 1. Session-State laden
    state = load_state(session_id)
    state.add_message("user", user_input)

    client = init_openai_client()

    # 2. Instinkt-Klassifikation
    classification = classify_instincts(user_input, client)

    # 3. Fakten sammeln
    facts: List[SymptomInfo] = []
    for instinct in classification.known_instincts:
        try:
            info = get_symptom_info(instinct)
            facts.append(info)
            state.add_message("assistant", f"Fakt geladen: {instinct}")
        except Exception:
            continue

    # 4. Rückfragen oder finale Diagnose
    if classification.uncertain_instincts:
        question_prompt = hundliche_wahrnehmung + "\n\n" + diagnose_rueckfragen
        messages = [
            {"role": "system", "content": question_prompt},
            {"role": "user", "content": json.dumps({
                "uncertain_instincts": classification.uncertain_instincts,
                "symptom_input": user_input
            })}
        ]
        q_resp = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=messages
        )
        next_q = q_resp.choices[0].message.content.strip()
        state.add_message("assistant", next_q)
        save_state(session_id, state)
        return {"question": next_q}
    else:
        # Finalen Diagnose-Service aufrufen
        try:
            final: FinalDiagnosisResponse = get_final_diagnosis(
                session_log=state.history,
                known_facts={"symptoms": [f.dict() for f in facts]}
            )
        except RuntimeError as e:
            raise RuntimeError(f"Fehler bei finaler Diagnose: {e}")
        state.add_message("assistant", final.message)
        save_state(session_id, state)
        return final.dict()
