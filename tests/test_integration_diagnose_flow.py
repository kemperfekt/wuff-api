# tests/test_integration_diagnose_flow.py

import os
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.models.instinct_models import InstinctClassification
from src.services.diagnose_service import FinalDiagnosisResponse

client = TestClient(app)

class FakeClient:
    def __init__(self, content=""):
        self._content = content
        self.chat = self
        self.completions = self

    def create(self, model, messages, **kwargs):
        return type("Resp", (), {
            "choices": [type("Choice", (), {
                "message": type("Msg", (), {"content": self._content})
            })]
        })

@pytest.fixture(autouse=True)
def setup_env_and_stubs(monkeypatch):
    # 1) OPENAI-KEY stubben
    os.environ["OPENAI_APIKEY"] = "testkey"

    # 2) OpenAI-Client stubben (dummy Frage-Response)
    monkeypatch.setattr(
        "src.agents.diagnose_agent.init_openai_client",
        lambda: FakeClient("Nächste Frage?")
    )

    # 3) classify_instincts stub
    def fake_classify(text, client):
        if "instinkt" in text.lower():
            return InstinctClassification(known_instincts=[], uncertain_instincts=["instinkt"])
        else:
            return InstinctClassification(known_instincts=["inst1"], uncertain_instincts=[])
    monkeypatch.setattr(
        "src.agents.diagnose_agent.classify_instincts",
        fake_classify
    )

    # 4) get_symptom_info stub
    def fake_get_symptom_info(instinct):
        return type("SI", (), {
            "dict": lambda self: {"symptom_name": instinct, "instinktvarianten": []}
        })()
    monkeypatch.setattr(
        "src.agents.diagnose_agent.get_symptom_info",
        fake_get_symptom_info
    )

    # 5) get_final_diagnosis stub
    def fake_final(session_log, known_facts):
        return FinalDiagnosisResponse(message="FinalDiagnosis", details={"facts": known_facts})
    monkeypatch.setattr(
        "src.agents.diagnose_agent.get_final_diagnosis",
        fake_final
    )

def test_flow_returns_question():
    resp = client.post(
        "/diagnose_continue",
        json={"session_id": "s1", "user_input": "Symptom mit Instinkt"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "question" in data
    assert isinstance(data["question"], str)
    assert data["question"] != ""

def test_flow_returns_final_diagnosis():
    resp = client.post(
        "/diagnose_continue",
        json={"session_id": "s2", "user_input": "Kein Stichwort"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["message"] == "FinalDiagnosis"
    assert "facts" in data["details"]
