# tests/test_api.py

from fastapi.testclient import TestClient
import pytest

from src.main import app

client = TestClient(app)

def test_diagnose_continue_question(monkeypatch):
    # Patch run_diagnose_agent in src.main
    monkeypatch.setenv("OPENAI_APIKEY", "testkey")
    monkeypatch.setattr(
        "src.main.run_diagnose_agent",
        lambda session_id, user_input: {"question": "Weiter?"}
    )

    resp = client.post(
        "/diagnose_continue",
        json={"session_id": "sid", "user_input": "text"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("question") == "Weiter?"
    assert data.get("message") is None

def test_diagnose_continue_final(monkeypatch):
    monkeypatch.setenv("OPENAI_APIKEY", "testkey")
    monkeypatch.setattr(
        "src.main.run_diagnose_agent",
        lambda session_id, user_input: {"message": "Fertig", "details": {}}
    )

    resp = client.post(
        "/diagnose_continue",
        json={"session_id": "sid", "user_input": "text"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["message"] == "Fertig"
    assert isinstance(data.get("details"), dict)
