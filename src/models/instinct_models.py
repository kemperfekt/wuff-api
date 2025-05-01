# src/models/instinct_models.py

from pydantic import BaseModel, ConfigDict
from typing import List

class InstinctClassification(BaseModel):
    known_instincts: List[str]
    uncertain_instincts: List[str]

    model_config = ConfigDict(populate_by_name=True)
