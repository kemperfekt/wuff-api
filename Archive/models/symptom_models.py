# src/models/symptom_models.py

# -------------------------------
# DogBot Datenmodelle für Diagnose
# -------------------------------

from pydantic import BaseModel, ConfigDict, field_validator
from typing import List, Dict, Any

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

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("instinktvarianten", mode="before")
    @classmethod
    def normalize_variants(cls, v: Any) -> Any:
        """
        Normalize incoming instinktvarianten field:
        - If dict: convert to list of dicts with name/description
        - If list of strings: wrap into dicts with empty instinkt
        - Else: leave as is
        """
        # raw dict from Weaviate
        if isinstance(v, dict):
            return [
                {"instinkt": name, "beschreibung": desc}
                for name, desc in v.items()
            ]
        # list of strings fallback
        if isinstance(v, list) and v and isinstance(v[0], str):
            return [
                {"instinkt": "", "beschreibung": item}
                for item in v
            ]
        # already in desired format
        return v

# ---------------------------------------
# Modell für eine Rückfrage-Antwort-Kombination
# ---------------------------------------
class RueckfrageAntwort(BaseModel):
    frage: str
    antwort: str
