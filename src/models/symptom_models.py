# -------------------------------
# DogBot Datenmodelle für Diagnose
# -------------------------------

from pydantic import BaseModel
from typing import List

# ---------------------------------------
# Modell für eine Instinktvariante eines Symptoms
# ---------------------------------------
class Instinktvariante(BaseModel):
    instinkt: str
    beschreibung: str

# ---------------------------------------
# Modell für allgemeine Informationen zu einem Symptom
# ---------------------------------------
class SymptomInfo(BaseModel):
    symptom_name: str 
    instinktvarianten: List[Instinktvariante]

# ---------------------------------------
# Modell für eine Rückfrage-Antwort-Kombination
# ---------------------------------------
class RueckfrageAntwort(BaseModel):
    frage: str
    antwort: str
