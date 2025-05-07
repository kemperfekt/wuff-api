# tests/test_run_diagnose_agent.py

import os
from src.agents.diagnose_agent import run_diagnose_agent
from src.models.instinct_models import InstinctClassification
from src.services.diagnose_service import FinalDiagnosisResponse

class DummyClient:
    def __init__(self, content):
        self._content = content
        self.chat = self
        self.completions = self
    def create(self, model, messages, **kwargs):
        return type("Resp", (), {
            "choices": [type("Choice", (), {
                "message": type("Msg", (), {"content": self._content})
            })]
        })

def test_run_diagnose_agent_question(monkeypatch):
    # 1) Stub Instinct-Klassifikation mit unsicheren Instinkten
    classification = InstinctClassification(
        known_instincts=[],
        uncertain_instincts=["instinkt1"]
    )
    monkeypatch.setattr(
        "src.agents.diagnose_agent.classify_instincts",
        lambda text, client: classification
    )

    # 2) Stub OpenAI-Client für Rückfrage
    dummy_question = "Wie alt ist der Hund?"
    monkeypatch.setenv("OPENAI_APIKEY", "testkey")
    monkeypatch.setattr(
        "src.agents.diagnose_agent.init_openai_client",
        lambda: DummyClient(dummy_question)
    )

    result = run_diagnose_agent("sess1", "Symptom Beschreibung")
    assert "question" in result
    assert result["question"] == dummy_question

def test_run_diagnose_agent_final(monkeypatch):
    # 1) Stub Instinct-Klassifikation ohne unsichere Instinkte
    classification = InstinctClassification(
        known_instincts=["inst1"],
        uncertain_instincts=[]
    )
    monkeypatch.setattr(
        "src.agents.diagnose_agent.classify_instincts",
        lambda text, client: classification
    )

    # 2) Stub get_symptom_info
    monkeypatch.setattr(
        "src.agents.diagnose_agent.get_symptom_info",
        lambda instinct: type("SI", (), {
            "dict": lambda self: {"symptom_name": instinct, "instinktvarianten": []}
        })()
    )

    # 3) Stub Final-Diagnose-Service
    final = FinalDiagnosisResponse(message="Diagnose", details={"test": True})
    monkeypatch.setenv("OPENAI_APIKEY", "testkey")
    monkeypatch.setattr(
        "src.agents.diagnose_agent.get_final_diagnosis",
        lambda session_log, known_facts: final
    )

    result = run_diagnose_agent("sess2", "Symptom Beschreibung")
    assert result["message"] == "Diagnose"
    assert result["details"] == {"test": True}
