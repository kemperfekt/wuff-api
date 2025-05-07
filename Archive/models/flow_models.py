# src/models/flow_models.py

from pydantic import BaseModel, ConfigDict, Field

class DiagnoseStart(BaseModel):
    symptom_input: str

class DiagnoseContinue(BaseModel):
    session_id: str
    answer: str = Field(alias="answer")

    model_config = ConfigDict(populate_by_name=True)

    @property
    def message(self) -> str:
        return self.answer
