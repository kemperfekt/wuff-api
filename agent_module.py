import json
import os
from openai import OpenAI
from symptom_models import SymptomInfo, RueckfrageAntwort
from weaviate_ops.symptom_tools import get_symptom_info

api_key = os.getenv("OPENAI_APIKEY")
if not api_key:
    raise EnvironmentError("OPENAIAPIKEY ist nicht gesetzt.")

client = OpenAI(api_key=api_key)

def run_diagnose_agent(symptom_input: str) -> str:
    system_prompt = (
        "Du bist ein Diagnose-Agent. Deine Aufgabe ist es, auf Basis der Informationen, die du über das Tool get_symptom_info erhältst, "
        "gezielte Ja-/Nein-Rückfragen zu stellen. Nutze dafür die dort angegebenen Instinktvarianten. "
        "Formuliere höchstens eine Rückfrage pro Instinkt, neutral und direkt an den Menschen gerichtet."
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
        return message.content or "Fehler beim Tool-Call."

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
                    "Hier sind die Instinktvarianten, anhand derer du deine Rückfragen formulieren sollst:\n"
                    + json.dumps(tool_response.instinktvarianten.model_dump(), ensure_ascii=False)
                )
            }
        ]
    )

    rückfragen = [f for f in follow_up.choices[0].message.content.split("\n") if f.strip()]

    diagnose_prompt = (
        "Du bist ein Diagnose-Agent. Deine Aufgabe ist es, auf Grundlage der gegebenen Antworten den wahrscheinlichsten Instinkt (oder mehrere bei Gleichstand) zu bestimmen. "
        "Wenn Antworten unklar oder nicht vorhanden sind, musst du dennoch eine Hypothese bilden, basierend auf der Symptombeschreibung und den Instinktvarianten. "
        "Berücksichtige ausschließlich diese vier Instinkte: Jagdinstinkt, Rudelinstinkt, Territorialinstinkt, Sexualinstinkt."
    )

    antworten = [RueckfrageAntwort(frage=q, antwort="Unklar") for q in rückfragen]  # Platzhalter, später liefert das Frontend echte Antworten

    diagnose_response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": diagnose_prompt},
            {"role": "user", "content": f"Antworten: {[a.model_dump() for a in antworten]}"}
        ]
    )

    return diagnose_response.choices[0].message.content

def generate_followup_questions(symptom_input: str) -> list[str]:
    system_prompt = (
        "Du bist ein Diagnose-Agent. Deine Aufgabe ist es, zu dem folgenden Symptom gezielte Ja-/Nein-Rückfragen zu formulieren. "
        "Nutze dabei die Informationen, die du über das Tool get_symptom_info erhältst, insbesondere die Instinktvarianten. "
        "Formuliere maximal eine Rückfrage pro Instinkt, klar und neutral gestellt."
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

def generate_final_diagnosis(symptom: str, questions: list[str], answers: list[str]) -> str:
    diagnose_prompt = (
        "Du bist ein Diagnose-Agent. Auf Grundlage der Antworten auf deine Rückfragen sollst du den wahrscheinlichsten Instinkt (oder mehrere bei Gleichstand) bestimmen. "
        "Wenn Antworten unklar oder widersprüchlich sind, bilde trotzdem eine Hypothese auf Basis der Symptombeschreibung und der Instinktvarianten. "
        "Berücksichtige nur folgende Instinkte: Jagdinstinkt, Rudelinstinkt, Territorialinstinkt, Sexualinstinkt."
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

