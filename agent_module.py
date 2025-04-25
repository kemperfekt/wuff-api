# -------------------------------
# DogBot Diagnose Agentenmodul
# -------------------------------
# Aufgabe: Steuerung der Kommunikation mit GPT
# - Rückfragen generieren auf Basis von Symptomen
# - Diagnose erstellen auf Basis der Antworten

import json
import os
from openai import OpenAI
from symptom_models import SymptomInfo, RueckfrageAntwort
from weaviate_ops.symptom_tools import get_symptom_info

# OpenAI API-Key laden
api_key = os.getenv("OPENAIAPIKEY")
if not api_key:
    raise EnvironmentError("OPENAIAPIKEY ist nicht gesetzt.")

# OpenAI-Client erstellen
client = OpenAI(api_key=api_key)

# ---------------------------------------
# Funktion: Nur für Altsystem (nicht mehr aktiv genutzt)
# Führt gesamte Diagnose auf einmal aus (Symptom -> Rückfragen -> Diagnose)
# ---------------------------------------
def run_diagnose_agent(symptom_input: str) -> str:
    system_prompt = (
        "You are a diagnosis agent. Your task is to ask targeted yes/no follow-up questions based on the information you receive via the tool get_symptom_info. "
        "Use the instinct variants provided there as your basis. Formulate no more than one question per instinct, stated neutrally and directly to the human."
    )

    # Tool-Call vorbereiten
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Symptom: {symptom_input}"}
        ],
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "get_symptom_info",
                    "description": "Provides structured information about a symptom including instinct variants.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symptom_name": {"type": "string"}
                        },
                        "required": ["symptom_name"]
                    }
                }
            }
        ],
        tool_choice="auto"
    )

    message = response.choices[0].message
    if not message.tool_calls:
        return message.content or "Error during tool call."

    # Tool aufrufen
    args = json.loads(message.tool_calls[0].function.arguments)
    symptom_name = args.get("symptom_name")
    tool_response_dict = get_symptom_info(symptom_name)
    tool_response = SymptomInfo.from_dict(tool_response_dict)

    # Rückfragen formulieren
    follow_up = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Symptom: {symptom_input}"},
            message,
            {
                "role": "tool",
                "tool_call_id": message.tool_calls[0].id,
                "name": message.tool_calls[0].function.name,
                "content": json.dumps(tool_response_dict, ensure_ascii=False)
            },
            {
                "role": "assistant",
                "content": (
                    "These are the instinct variants you should use to formulate follow-up questions:\n"
                    + json.dumps(tool_response.instinktvarianten.model_dump(), ensure_ascii=False)
                )
            }
        ]
    )

    rückfragen = [f for f in follow_up.choices[0].message.content.split("\n") if f.strip()]

    diagnose_prompt = (
        "You are a diagnosis agent. Your task is to determine the most likely instinct (or instincts) based on the provided answers. "
        "If answers are unclear or missing, you must still form a hypothesis based on the symptom description and the instinct variants provided. "
        "Only use these four instincts: Hunting instinct, Social instinct, Territorial instinct, Sexual instinct."
    )

    antworten = [RueckfrageAntwort(frage=q, antwort="Unclear") for q in rückfragen]

    diagnose_response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": diagnose_prompt},
            {"role": "user", "content": f"Answers: {[a.model_dump() for a in antworten]}"}
        ]
    )

    return diagnose_response.choices[0].message.content

# ---------------------------------------
# NEU: Folgefragen generieren (für neues Session-Handling)
# ---------------------------------------
def generate_followup_questions(symptom_input: str) -> list[str]:
    system_prompt = (
        "Du bist ein Diagnose-Agent. Deine Aufgabe ist es, zu dem folgenden Symptom gezielte Ja-/Nein-Rückfragen zu formulieren. "
        "Nutze die Informationen, die du über das Tool get_symptom_info erhältst, insbesondere die Instinktvarianten. "
        "Formuliere maximal eine Rückfrage pro Instinkt."
    )

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Symptom: {symptom_input}"}
        ],
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "get_symptom_info",
                    "description": "Liefert strukturierte Informationen über ein Symptom inklusive Instinktvarianten.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symptom_name": {"type": "string"}
                        },
                        "required": ["symptom_name"]
                    }
                }
            }
        ],
        tool_choice="auto"
    )

    message = response.choices[0].message
    if not message.tool_calls:
        return ["Fehler beim Tool-Call."]

    args = json.loads(message.tool_calls[0].function.arguments)
    symptom_name = args.get("symptom_name")
    tool_response_dict = get_symptom_info(symptom_name)
    tool_response = SymptomInfo.from_dict(tool_response_dict)

    follow_up = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Symptom: {symptom_input}"},
            message,
            {
                "role": "tool",
                "tool_call_id": message.tool_calls[0].id,
                "name": message.tool_calls[0].function.name,
                "content": json.dumps(tool_response_dict, ensure_ascii=False)
            },
            {
                "role": "assistant",
                "content": (
                    "Hier sind die Instinktvarianten, anhand derer du Rückfragen formulieren sollst:\n"
                    + json.dumps(tool_response.instinktvarianten.model_dump(), ensure_ascii=False)
                )
            }
        ]
    )

    rückfragen = [f for f in follow_up.choices[0].message.content.split("\n") if f.strip()]
    return rückfragen

# ---------------------------------------
# NEU: Finale Diagnose erstellen
# ---------------------------------------
def generate_final_diagnosis(symptom: str, questions: list[str], answers: list[str]) -> str:
    diagnose_prompt = (
        "Du bist ein Diagnose-Agent. Auf Grundlage der Antworten auf deine Rückfragen sollst du den wahrscheinlichsten Instinkt (oder mehrere) bestimmen. "
        "Falls Antworten unklar sind, bilde trotzdem eine Hypothese auf Basis der Symptome und Instinktvarianten. "
        "Erlaube dir keine eigenen Mutmaßungen jenseits der Antworten."
    )

    antworten_liste = [{"frage": frage, "antwort": antwort} for frage, antwort in zip(questions, answers)]

    diagnose_response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": diagnose_prompt},
            {"role": "user", "content": f"Symptom: {symptom}\nAntworten: {json.dumps(antworten_liste, ensure_ascii=False)}"}
        ]
    )

    return diagnose_response.choices[0].message.content
