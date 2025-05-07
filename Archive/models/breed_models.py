# src/models/breed_models.py

from pydantic import BaseModel, ConfigDict

class InstinctScore(BaseModel):
    territorial: float
    rudel: float
    sexual: float
    jagd: float

class BreedInfo(BaseModel):
    group_name: str
    function: str
    features: str
    requirements: str
    instinct_score: InstinctScore

    model_config = ConfigDict(populate_by_name=True)
