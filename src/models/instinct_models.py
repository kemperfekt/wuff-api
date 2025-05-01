from pydantic import BaseModel, Field
from typing import List, Dict, Any

class InstinctClassification(BaseModel):
    """
    Ergebnis der Instinkt-Klassifikation:
    - known_instincts: klar erkannte Instinkte
    - uncertain_instincts: Instinkte, zu denen Rückfragen nötig sind
    """
    known_instincts: List[str] = Field(...)
    uncertain_instincts: List[str] = Field(...)

class InstinktVeranlagung(BaseModel):
    """
    Profil einer Instinktveranlagungsgruppe aus Weaviate:
    - gruppen_code: Code der Gruppe
    - gruppe: Name der Hauptgruppe
    - untergruppe: Name der Untergruppe
    - funktion: Ursprüngliche Funktion
    - merkmale: Typische Merkmale
    - anforderungen: Anforderungen an Haltung/Training
    - instinkte: Gewichtung der einzelnen Instinkte
    """
    gruppen_code: str = Field(...)
    gruppe: str = Field(...)
    untergruppe: str = Field(...)
    funktion: str = Field(...)
    merkmale: str = Field(...)
    anforderungen: str = Field(...)
    instinkte: Dict[str, int] = Field(...)
