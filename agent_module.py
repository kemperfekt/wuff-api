# -----------------------------------------------
# DogBot - Agent Module (Diagnose und Interaktion)
# -----------------------------------------------

import os
from openai import OpenAI
from weaviate_ops.symptom_tools import get_symptom_info
from connect_weaviate import get_weaviate_client
from pydantic import BaseModel
from symptom_models import SymptomInfo, Instinktvariante, RueckfrageAntwort
import json

# -----------------------------------------------
# Diagnose-Agent: Startet die Diagnose
# -----------------------------------------------
def run_diagnose_agent(symptom_input: str) -> list:
    """
    Holt Symptomdaten und generiert Rückfragen.
    Gibt alle Rückfragen als Liste zurück.
    """
    symptom_info_dict = get_symptom_info(symptom_input)

    if isinstance(symptom_info_dict, str) or "fehler" in symptom_info_dict:
        return [f"Fehler bei der Abfrage: {symptom_info_dict}"]

    try:
        symptom_info = SymptomInfo(**symptom_info_dict)
    except Exception as e:
        return [f"Fehler beim Verarbeiten der Symptomdaten: {e}"]

    questions = generate_followup_questions(symptom_info)

    if questions:
        return questions
    else:
        return ["Keine Rückfragen verfügbar. Bitte kontaktieren Sie den Support."]

# -----------------------------------------------
# Generiert Rückfragen basierend auf Instinkten
# -----------------------------------------------
def generate_followup_questions(symptom_info: SymptomInfo) -> list:
    questions = []

    for instinktvariante in symptom_info.instinktvarianten:
        if instinktvariante.instinkt == "Jagdinstinkt":
            questions.append("Zeigt dein Hund Interesse an bewegenden Objekten?")
        elif instinktvariante.instinkt == "Rudelinstinkt":
            questions.append("Ist dein Hund besonders an anderen Menschen oder Hunden interessiert?")
        elif instinktvariante.instinkt == "Territorialinstinkt":
            questions.append("Wacht dein Hund über bestimmte Orte in deinem Zuhause?")
        elif instinktvariante.instinkt == "Sexualinstinkt":
            questions.append("Hat dein Hund ein starkes Interesse an Hündinnen oder Rüden?")

    if not questions:
        raise ValueError("Keine Rückfragen basierend auf den Instinkten generiert.")

    return questions

# -----------------------------------------------
# Generiert die finale Diagnose
# -----------------------------------------------
def generate_final_diagnosis(symptom: str, answers: list) -> str:
    if any("Jagd" in answer for answer in answers):
        return f"Die Diagnose für das Symptom '{symptom}' könnte mit einem erhöhten Jagdinstinkt zusammenhängen."
    if any("Rudel" in answer for answer in answers):
        return f"Das Symptom '{symptom}' weist möglicherweise auf einen hohen Rudelinstinkt hin."
    return f"Das Symptom '{symptom}' bleibt unklar. Weitere Untersuchung notwendig."
