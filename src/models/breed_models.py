# src/models/breed_models.py

from pydantic import BaseModel


class InstinctScore(BaseModel):
    """
    Scores für die vier Hundinstinkte, typischerweise Werte von 0.0 bis 1.0.
    Felder:
      - territorial: Territorialinstinkt
      - rudel: Rudelinstinkt
      - sexual: Sexualinstinkt
      - jagd: Jagdinstinkt
    """
    territorial: float
    rudel: float
    sexual: float
    jagd: float


class BreedInfo(BaseModel):
    """
    Modell für Hunderassen-Gruppen-Informationen aus Weaviate.

    Felder:
      - group_name: Name der Rasse-Gruppe
      - function: Hauptfunktion der Rasse-Gruppe
      - features: Merkmale dieser Gruppe
      - requirements: Anforderungen an Haltung und Training
      - instinct_score: Objekt mit numerischen Scores für Instinkte
    """
    group_name: str
    function: str
    features: str
    requirements: str
    instinct_score: InstinctScore
