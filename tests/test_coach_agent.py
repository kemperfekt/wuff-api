# tests/test_coach_agent.py

import json
import pytest
import src.agents.coach_agent as coach_mod
from src.agents.coach_agent import run_coach_agent

class DummyClient:
    def __init__(self, content):
        self._content = content
        self.chat = self
        self.completions = self
    def create(self, *args, **kwargs):
        return type("Resp", (), {
            "choices": [type("Choice", (), {
                "message": type("Msg", (), {"content": self._content})
            })]
        })

@pytest.fixture(autouse=True)
def stub_retrieval_and_key(monkeypatch):
    # Symptom-Stub
    monkeypatch.setattr(
        coach_mod,
        "get_symptom_info",
        lambda s: type("S", (), {
            "beschreibung": "Desc",
            "instinkt_varianten": {"i": "V"},
            "dict": lambda self: {}
        })()
    )
    # Instinktprofil-Stub
    monkeypatch.setattr(
        coach_mod,
        "get_instinkt_profile",
        lambda code: type("P", (), {
            "gruppe": "G",
            "merkmale": "M",
            "dict": lambda self: {}
        })()
    )
    # Breed-Stub
    monkeypatch.setattr(coach_mod, "get_breed_info", lambda b: None)

    # OpenAI-Key stubben
    monkeypatch.setenv("OPENAI_APIKEY", "testkey")
    yield
    monkeypatch.delenv("OPENAI_APIKEY", raising=False)

def test_question_branch(monkeypatch):
    # LLM liefert {"questions": ["Q"]}
    monkeypatch.setattr(
        "src.agents.coach_agent.init_openai_client",
        lambda: DummyClient(json.dumps({"questions": ["Q"]}))
    )
    out = run_coach_agent(history=[], dog_explanation="dog", symptom_input="sym")
    assert out.get("question") == "Q"
    assert "message" not in out

def test_diagnosis_branch(monkeypatch):
    # DummyFinal mit needs_background
    class DummyFinal:
        def __init__(self):
            self.message = "M"
            self.details = {"d": 1}
            self.needs_background = False

    # Stub finalen Diagnose-Service direkt im Coach-Modul
    monkeypatch.setattr(
        coach_mod,
        "get_final_diagnosis",
        lambda session_log, known_facts: DummyFinal()
    )
    # LLM liefert leeres JSON, damit Diagnose-Zweig greift
    monkeypatch.setattr(
        "src.agents.coach_agent.init_openai_client",
        lambda: DummyClient("{}")
    )

    out = run_coach_agent(history=[], dog_explanation="dog", symptom_input="sym")
    assert out["message"] == "M"
    assert out["details"] == {"d": 1}
    assert out["needs_background"] is False
