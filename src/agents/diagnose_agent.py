# ---------------------------------------------
# Datei: src/agent_module.py
# Zweck: Diagnostik-Flow mit Instinkt-Klassifikation per Function Calling
# ---------------------------------------------

import os
import json
from typing import List, Dict

from openai import OpenAI
from pydantic import ValidationError

from src.models.symptom_models import SymptomInfo  
from src.models.instinct_models import InstinctClassification
from src.services.retrieval import get_symptom_info, get_breed_info

# Stelle sicher, dass deine openai-Package-Version >= 0.27.0 ist,
# damit Function Calling unterstützt wird.

def init_openai_client() -> OpenAI:
    """Initialisiert den OpenAI-Client aus der ENV."""
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_APIKEY")
    if not api_key:
        raise RuntimeError("OpenAI API-Key nicht gesetzt")
    return OpenAI(api_key=api_key)

def classify_instincts(text: str, client: OpenAI) -> InstinctClassification:
    """
    Fragt GPT per Function Calling, welche Instinkte eindeutig erkannt
    und welche unsicher sind. Gibt ein InstinctClassification-Objekt zurück.
    """
    # Definition der Function Calling API
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

    # System-Prompt, der GPT anweist, die Eingabe zu klassifizieren.
    system_prompt = (
        "Du bist ein Hunde-Verhaltens-Agent. "
        "Analysiere die folgende Eingabe und "
        "liste alle Instinkte auf, die klar erkennbar sind (known_instincts) "
        "und alle, bei denen du dir unsicher bist (uncertain_instincts)."
    )

    # Erster GPT-Aufruf mit Function Calling
    response = client.chat.completions.create(
        model="gpt-4o-mini",            # oder dein gewünschtes Modell
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ],
        functions=functions,
        function_call={"name": "classify_instincts"}  # zwingt GPT zur Funktionswahl
    )

    # Extrahiere die Argumente aus dem Function Call
    func_call = response.choices[0].message.function_call
    args_json = func_call.arguments

    try:
        # Parst und validiert gegen unser Pydantic-Modell
        classification = InstinctClassification.parse_raw(args_json)
        return classification
    except ValidationError as e:
        # Falls die Validierung fehlschlägt, werfen wir einen Fehler
        raise RuntimeError(f"InstinctClassification-Parsing fehlgeschlagen: {e}")

def run_diagnose_agent(symptom_input: str) -> List[str]:
    """
    Überarbeitete Version:
    1. Instinkt-Klassifikation
    2. Weaviate-Retrieval für bekannte Instinkte
    3. Dynamische Nachfragen nur für unsichere Instinkte
    """
    client = init_openai_client()

    # 1. Klassifiziere Instinkte aus der Nutzereingabe
    classification = classify_instincts(symptom_input, client)

    # 2. Wenn bekannte Instinkte vorhanden sind, hol Fakten aus Weaviate
    known_facts: List[SymptomInfo] = []
    for instinct in classification.known_instincts:
        try:
            info = get_symptom_info(instinct)  # deine bestehende Weaviate-Funktion
            known_facts.append(info)
        except Exception:
            # Einfaches Fehler-Handling, falls Weaviate keinen Eintrag findet
            continue

    # 3. Für unsichere Instinkte dynamische Fragen generieren
    uncertain = classification.uncertain_instincts
    if not uncertain:
        # Kein Unsicherer Instinkt → direkt finale Diagnose
        return [generate_final_diagnosis(known_facts, [])]

    # Bau den Prompt für die Nachfragen
    question_system = (
        "Formuliere für jeden Instinkt in der Liste 'uncertain_instincts' "
        "eine offene Frage, die hilft, Klarheit zu schaffen."
    )
    messages = [
        {"role": "system", "content": question_system},
        {"role": "assistant", "content": json.dumps(uncertain)}
    ]

    # GPT generiert nun eine Liste von Fragen
    q_resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )
    # Wir erwarten eine JSON-Liste im Freitext → hier ggf. Robustheits-Checks hinzufügen
    questions = json.loads(q_resp.choices[0].message.content)
    return questions

def generate_final_diagnosis(known_facts: List[SymptomInfo],
                             answers: List[str]) -> str:
    """
    Wie bisher: Konsolidiere bekannte Fakten und Nutzerantworten
    und liefere eine abschließende Instinkt-Diagnose.
    """
    client = init_openai_client()
    # Baue den finalen Prompt
    system_prompt = (
        "Du bist ein diagnostischer Agent für Hundeverhalten. "
        "Basierend auf den folgenden Fakten und Antworten "
        "nenne den primären Hundinstinkt (oder mehrere, falls zutreffend):\n\n"
    )
    # Füge Fakten und Antworten in die Nachricht
    content = system_prompt
    for fact in known_facts:
        content += f"- {fact.symptom_name}: {fact.instinktvarianten}\n"
    content += "\nUser-Antworten:\n" + "\n".join(f"- {a}" for a in answers)

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": content}]
    )
    return resp.choices[0].message.content.strip()
