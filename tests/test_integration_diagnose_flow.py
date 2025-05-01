import os
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.models.instinct_models import InstinctClassification
from src.services.diagnose_service import FinalDiagnosisResponse

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_env_and_alias_stub(monkeypatch):
    # 1) OPENAI-KEY stubben
    os.environ["OPENAI_APIKEY"] = "testkey"

    # 2) Stub den API-Alias run_diagnose_agent in src.main
    import src.main as main_mod

    def fake_run_diagnose_agent(session_id, user_input):
        if "Instinkt" in user_input:
            return {"question": "Nächste Frage?"}
        return {"message": "FinalDiagnosis", "details": {"facts": {}}}

    monkeypatch.setattr(main_mod, "run_diagnose_agent", fake_run_diagnose_agent)

def test_flow_returns_question():
    resp = client.post(
        "/diagnose_continue",
        json={"session_id": "s1", "user_input": "Symptom mit Instinkt"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "question" in data
    assert data["question"] == "Nächste Frage?"

def test_flow_returns_final_diagnosis():
    resp = client.post(
        "/diagnose_continue",
        json={"session_id": "s2", "user_input": "Kein Stichwort"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["message"] == "FinalDiagnosis"
    assert "facts" in data["details"]
