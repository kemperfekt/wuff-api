# src/agents/diagnose_agent.py
import os
import json
import logging
from typing import List, Dict, Any
from openai import OpenAI
from pydantic import ValidationError

from src.models.symptom_models import SymptomInfo
from src.models.instinct_models import InstinctClassification
from src.services.retrieval import get_symptom_info
from src.services.diagnose_service import get_final_diagnosis, FinalDiagnosisResponse
from src.services.state import load_state, save_state

from src.prompts.prompt_hundliche_wahrnehmung import hundliche_wahrnehmung
from src.prompts.system_prompt_diagnose import diagnose_instinktklassifikation
from src.prompts.system_prompt_questions import diagnose_rueckfragen

# Logging konfigurieren
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


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
                    "known_instincts": {"type": "array", "items": {"type": "string"}},
                    "uncertain_instincts": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["known_instincts", "uncertain_instincts"]
            }
        }
    ]
    system_prompt = hundliche_wahrnehmung + "\n\n" + diagnose_instinktklassifikation
    logger.debug("System Prompt for classify_instincts: %s", system_prompt)

    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ],
        functions=functions,
        function_call={"name": "classify_instincts"}
    )
    args_json = response.choices[0].message.function_call.arguments
    logger.debug("Raw function_call.arguments: %s", args_json)

    try:
        classification = InstinctClassification.model_validate_json(args_json)
        logger.debug(
            "Classification result: known_instincts=%s, uncertain_instincts=%s",
            classification.known_instincts,
            classification.uncertain_instincts
        )
        return classification
    except ValidationError as e:
        logger.error("Parsing InstinctClassification failed: %s", e)
        raise RuntimeError(f"InstinctClassification-Parsing fehlgeschlagen: {e}\nRaw args: {args_json}")


def run_diagnose_agent(session_id: str, user_input: str) -> Dict[str, Any]:
    """
    Fortsetzen des Diagnose-Flows:
    - Lädt Session-State
    - Klassifiziert Instinkte
    - Liefert generische Rückfrage bei keiner Klassifikation
    - Liefert spezifische Rückfrage bei Unsicherheiten
    - Ruft finale Diagnose auf bei klaren Instinkten
    """
    state = load_state(session_id)
    state.add_message("user", user_input)
    logger.debug("Session %s - Received user input: %s", session_id, user_input)

    client = init_openai_client()
    classification = classify_instincts(user_input, client)

    # Keine Instinkte erkannt
    if not classification.known_instincts and not classification.uncertain_instincts:
        generic_q = (
            "Könntest du das Verhalten genauer beschreiben, z.B. "
            "wann und wie oft es auftritt?"
        )
        logger.debug("No instincts detected - returning generic question")
        state.add_message("assistant", generic_q)
        save_state(session_id, state)
        return {"question": generic_q}

    # Unsichere Instinkte vorhanden
    if classification.uncertain_instincts:
        logger.debug("Uncertain instincts detected: %s", classification.uncertain_instincts)
        question_prompt = hundliche_wahrnehmung + "\n\n" + diagnose_rueckfragen
        payload = {
            "uncertain_instincts": classification.uncertain_instincts,
            "symptom_input": user_input
        }
        logger.debug("Payload for follow-up questions: %s", payload)
        messages = [
            {"role": "system", "content": question_prompt},
            {"role": "user", "content": json.dumps(payload)}
        ]
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=messages
        )
        next_q = response.choices[0].message.content.strip()
        logger.debug("Follow-up question from model: %s", next_q)
        state.add_message("assistant", next_q)
        save_state(session_id, state)
        return {"question": next_q}

    # Finale Diagnose
    logger.debug("Known instincts: %s - proceeding to final diagnosis", classification.known_instincts)
    facts: List[SymptomInfo] = []
    for instinct in classification.known_instincts:
        try:
            info = get_symptom_info(instinct)
            facts.append(info)
            state.add_message("assistant", f"Fakt geladen: {instinct}")
        except Exception as e:
            logger.warning("Failed to load symptom info for %s: %s", instinct, e)

    try:
        final: FinalDiagnosisResponse = get_final_diagnosis(
            session_log=state.history,
            known_facts={"symptoms": [f.dict() for f in facts]}
        )
        logger.debug("Final diagnosis: %s", final)
    except RuntimeError as e:
        logger.error("Final diagnosis failed: %s", e)
        raise

    state.add_message("assistant", final.message)
    save_state(session_id, state)
    return final.dict()
