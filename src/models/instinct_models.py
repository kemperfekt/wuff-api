# ---------------------------------------------
# Datei: src/models/instinct_models.py
# Zweck: Pydantic-Modell für die Instinkt-Klassifikation,
#        das wir per Function Calling zurückbekommen.
# ---------------------------------------------

from pydantic import BaseModel
from typing import List

class InstinctClassification(BaseModel):
    """
    Modell für die Instinkt-Klassifikation.
    Wird von GPT per Function Calling mit folgendem JSON befüllt:
    {
      "known_instincts": [...],
      "uncertain_instincts": [...]
    }
    """
    known_instincts: List[str]
    uncertain_instincts: List[str]
