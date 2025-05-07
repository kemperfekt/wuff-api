# tests/test_coach_agent.py

import json
import pytest
import src.agents.coach_agent as coach_mod
import src.services.diagnose_service as diag_svc
from src.agents.coach_agent import run_coach_agent
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

@pytest.fixture(autouse=True)
def stub_openai_key(monkeypatch):
    # OpenAI-Key stubben
    monkeypatch.setenv("OPENAI_APIKEY", "testkey")
    yield
    monkeypatch.delenv("OPENAI_APIKEY", raising=False)

def test_coach_agent_question(monkeypatch):
    # Dummy für Symptom & Instinktprofil
    class DummySymptom:
        def __init__(self):
            self.symptom_name = "X"
            self.beschreibung = "Desc"
            self.erste_hilfe = "EH"
            self.instinkt_varianten = {"jagd": "J"}
        def dict(self):
            return {
                "symptom_name": self.symptom_name,
                "beschreibung": self.beschreibung,
                "erste_hilfe": self.erste_hilfe,
                "instinkt_varianten": self.instinkt_varianten
            }

    class DummyInstinctProfile:
        def __init__(self):
            self.gruppen_code = "G"
            self.gruppe = "Grp"
            self.untergruppe = "Sub"
            self.funktion = "F"
            self.merkmale = "M"
            self.anforderungen = "A"
            self.instinkte = {"jagd": 10}
        def dict(self):
            return {
                "gruppen_code": self.gruppen_code,
                "gruppe": self.gruppe,
                "untergruppe": self.untergruppe,
                "funktion": self.funktion,
                "merkmale": self.merkmale,
                "anforderungen": self.anforderungen,
                "instinkte": self.instinkte
            }

    # Stub Retrieval im Coach-Modul
    monkeypatch.setattr(coach_mod, "get_symptom_info", lambda s: DummySymptom())
    monkeypatch.setattr(coach_mod, "get_instinkt_profile", lambda g: DummyInstinctProfile())
    monkeypatch.setattr(coach_mod, "get_breed_info", lambda b: None)

    # Stub OpenAI für Rückfragen
    dummy = json.dumps({"questions": ["Frage1", "Frage2"]})
    monkeypatch.setattr(
        "src.agents.coach_agent.init_openai_client",
        lambda: DummyClient(dummy)
    )

    out = run_coach_agent([], "Hund erklärt", "Ich belle im Garten")
    assert out["question"] == "Frage1"

def test_coach_agent_diagnosis(monkeypatch):
    # Dummy für Symptom & Instinktprofil
    class DummySymptom:
        def __init__(self):
            self.symptom_name = "X"
            self.beschreibung = "Desc"
            self.erste_hilfe = "EH"
            self.instinkt_varianten = {"jagd": "J"}
        def dict(self):
            return {
                "symptom_name": self.symptom_name,
                "beschreibung": self.beschreibung,
                "erste_hilfe": self.erste_hilfe,
                "instinkt_varianten": self.instinkt_varianten
            }

    class DummyInstinctProfile:
        def __init__(self):
            self.gruppen_code = "G"
            self.gruppe = "Grp"
            self.untergruppe = "Sub"
            self.funktion = "F"
            self.merkmale = "M"
            self.anforderungen = "A"
            self.instinkte = {"jagd": 10}
        def dict(self):
            return {
                "gruppen_code": self.gruppen_code,
                "gruppe": self.gruppe,
                "untergruppe": self.untergruppe,
                "funktion": self.funktion,
                "merkmale": self.merkmale,
                "anforderungen": self.anforderungen,
                "instinkte": self.instinkte
            }

    # Stub Retrieval im Coach-Modul
    monkeypatch.setattr(coach_mod, "get_symptom_info", lambda s: DummySymptom())
    monkeypatch.setattr(coach_mod, "get_instinkt_profile", lambda g: DummyInstinctProfile())
    monkeypatch.setattr(coach_mod, "get_breed_info", lambda b: None)

    # Stub finalen Diagnose-Service
    monkeypatch.setattr(
        diag_svc,
        "get_final_diagnosis",
        lambda session_log, known_facts: FinalDiagnosisResponse(
            message="Msg",
            details={"i": 1}
        )
    )

    # Stub init_openai_client mit minimal gültigem JSON, damit Coach-Agent in Diagnose-Zweig geht
    monkeypatch.setattr(
        "src.agents.coach_agent.init_openai_client",
        lambda: DummyClient("{}")
    )

    out = run_coach_agent([], "Hund erklärt", "Ich belle im Garten")
    assert out["message"] == "Msg"
    assert out["details"] == {"i": 1}
    assert out["needs_background"] is False
