# -------------------------------
# DogBot Datenmodelle für Diagnose
# -------------------------------
# Aufgabe: Strukturierung der Daten (Symptom-Infos, Rückfragen, Antworten)
# Verwendung mit Pydantic für saubere Datentypen und Validierung

from pydantic import BaseModel
from typing import List

# ---------------------------------------
# Modell für eine Instinktvariante eines Symptoms
# ---------------------------------------
class Instinktvariante(BaseModel):
    instinkt: str           # Name des Instinkts (z.B. Jagdinstinkt)
    beschreibung: str       # Beschreibung, wie sich der Instinkt beim Symptom zeigen könnte

# ---------------------------------------
# Modell für allgemeine Informationen zu einem Symptom
# ---------------------------------------
class SymptomInfo(BaseModel):
    symptom: str                     # Name oder kurze Beschreibung des Symptoms
    instinktvarianten: List[Instinktvariante]  # Liste der zugeordneten Instinktvarianten

# ---------------------------------------
# Modell für eine Rückfrage-Antwort-Kombination
# ---------------------------------------
class RueckfrageAntwort(BaseModel):
    frage: str    # Die gestellte Rückfrage
    antwort: str  # Die Antwort des Benutzers ("Ja", "Nein", "Unklar", etc.)
