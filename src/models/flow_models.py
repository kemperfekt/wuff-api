# src/models/flow_models.py

from pydantic import BaseModel


class AgentMessage(BaseModel):
    role: str  # z. B. "coach", "dog", "mentor"
    content: str