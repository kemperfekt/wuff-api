# src/models/flow_models.py

from pydantic import BaseModel


class AgentMessage(BaseModel):
    sender: str  # z. B. "coach", "dog", "mentor"
    text: str