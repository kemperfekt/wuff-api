# -----------------------------------------------
# DogBot - Agent Module (Diagnose und Interaktion)
# (Agentic RAG: GPT + Tool-Use + Weaviate)
# -----------------------------------------------

import os
import json
from openai import OpenAI
from pydantic import BaseModel
from weaviate_ops.symptom_tools import get_symptom_info
from symptom_models import SymptomInfo

# -----------------------------------------------
# OpenAI Client initialisieren
# -----------------------------------------------

api_key = os.getenv("OPENAI_APIKEY")
if not api_key:
    raise EnvironmentError("OPENAI_APIKEY ist nicht gesetzt.")

client = OpenAI(api_key=api_key)

# -----------------------------------------------
# Diagnose-Agent: Startet die Diagnose
# -----------------------------------------------

def run_diagnose_agent(symptom_input: str) -> list:
    """
    Holt Symptomdaten über GPT (Tool-Use) und generiert Rückfragen.
    Gibt alle Rückfragen als Liste zurück.
    """
    system_prompt = (
        "Du bist ein Diagnose-Agent. Hole Informationen über das Symptom mit dem Tool get_symptom_info "
        "und formuliere für jede relevante Instinktvariante eine gezielte Ja-/Nein-Rückfrage."
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
    symptom_info = SymptomInfo(**tool_response_dict)

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
            }
        ]
    )

    rückfragen = [frage.strip() for frage in follow_up.choices[0].message.content.split("\n") if frage.strip()]
    return rückfragen

# -----------------------------------------------
# Diagnose-Agent: Erstellt finale Diagnose
# -----------------------------------------------

def generate_final_diagnosis(symptom: str, questions: list, answers: list) -> str:
    """
    Analysiert Antworten und erstellt auf Basis der Antworten eine Diagnose.
    """
    diagnose_prompt = (
        "Du bist ein Diagnose-Agent. Bestimme auf Basis der Antworten den wahrscheinlichsten Instinkt "
        "(Jagdinstinkt, Rudelinstinkt, Territorialinstinkt oder Sexualinstinkt). "
        "Falls die Antworten unklar sind, bilde eine Hypothese basierend auf dem Symptom."
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

# -----------------------------------------------
# Hinweis:
# - GPT ruft Weaviate indirekt via get_symptom_info auf.
# - GPT erstellt selbstständig Rückfragen und Diagnosen.
# -----------------------------------------------