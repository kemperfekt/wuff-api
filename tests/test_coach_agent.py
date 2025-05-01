# tests/test_coach_agent.py
import os
import json
import pytest
from src.agents.coach_agent import run_coach_agent

class DummyClient:
    def __init__(self, content):
        self._content = content
        self.chat = self
        self.completions = self

    def create(self, model, messages, **kwargs):
        # Simuliere eine Chat-Antwort mit raw JSON-String
        return type("Resp", (), {
            "choices": [type("Choice", (), {
                "message": type("Message", (), {
                    "content": self._content
                })
            })]
        })

@pytest.fixture(autouse=True)
def fix_api_key(monkeypatch):
    monkeypatch.setenv("OPENAI_APIKEY", "test")
    yield
    monkeypatch.delenv("OPENAI_APIKEY", raising=False)

def test_coach_agent_question(monkeypatch):
    # Stub init_openai_client, so dass unser DummyClient verwendet wird
    json_q = json.dumps({"question": "Welche Umstände?"})
    monkeypatch.setattr(
        "src.agents.coach_agent.init_openai_client",
        lambda: DummyClient(json_q)
    )
    # leere History, Dog-Text
    res = run_coach_agent([], "Hund erklärt Verhalten")
    assert "question" in res
    assert res["question"] == "Welche Umstände?"

def test_coach_agent_diagnosis(monkeypatch):
    payload = {"diagnosis": {"instinkt": "Jagd"}, "needs_background": True}
    json_d = json.dumps(payload)
    monkeypatch.setattr(
        "src.agents.coach_agent.init_openai_client",
        lambda: DummyClient(json_d)
    )
    res = run_coach_agent([], "Hund erklärt Verhalten")
    assert "diagnosis" in res
    assert res["diagnosis"]["instinkt"] == "Jagd"
    assert res["needs_background"] is True
