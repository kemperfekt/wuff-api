# src/agents/diagnose_agent.py

import os
import json
from typing import List, Dict

from openai import OpenAI
from pydantic import ValidationError

from src.models.symptom_models import SymptomInfo  
from src.models.instinct_models import InstinctClassification
from src.services.retrieval import get_symptom_info, get_breed_info

from src.prompts.prompt_hundliche_wahrnehmung import hundliche_wahrnehmung
from src.prompts.system_prompt_diagnose import diagnose_instinktklassifikation
from src.prompts.system_prompt_questions import diagnose_rueckfragen


def init_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_APIKEY")
    if not api_key:
        raise RuntimeError("OpenAI API-Key nicht gesetzt")
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
        model="gpt-4o-mini",
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


def run_diagnose_agent(symptom_input: str) -> List[str]:
    client = init_openai_client()
    classification = classify_instincts(symptom_input, client)

    known_facts: List[SymptomInfo] = []
    for instinct in classification.known_instincts:
        try:
            info = get_symptom_info(instinct)
            known_facts.append(info)
        except Exception:
            continue

    uncertain = classification.uncertain_instincts
    if not uncertain:
        return [generate_final_diagnosis(known_facts, [])]

    question_prompt = hundliche_wahrnehmung + "\n\n" + diagnose_rueckfragen

    messages = [
        {"role": "system", "content": question_prompt},
        {"role": "user", "content": json.dumps({
            "uncertain_instincts": uncertain,
            "symptom_input": symptom_input
        })}
    ]

    q_resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )
    return [q_resp.choices[0].message.content.strip()]


def generate_final_diagnosis(known_facts: List[SymptomInfo], answers: List[str]) -> str:
    client = init_openai_client()
    system_prompt = hundliche_wahrnehmung + "\n\n" + (
        "Du bist ein diagnostischer Agent für Hundeverhalten. "
        "Basierend auf den folgenden Fakten und Antworten nenne den primären Hundinstinkt "
        "(oder mehrere, falls zutreffend):\n\n"
    )

    content = system_prompt
    for fact in known_facts:
        content += f"- {fact.symptom_name}: {fact.instinktvarianten}\n"
    content += "\nUser-Antworten:\n" + "\n".join(f"- {a}" for a in answers)

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": content}]
    )
    return resp.choices[0].message.content.strip()
