# tests/test_diagnose_service.py

import os
import json
import pytest
import openai
from src.services.diagnose_service import get_final_diagnosis, FinalDiagnosisResponse

# Fixture, um sicherzustellen, dass OPENAI_APIKEY gesetzt ist
@pytest.fixture(autouse=True)
def fix_api_key(monkeypatch):
    monkeypatch.setenv("OPENAI_APIKEY", "testkey")
    yield
    monkeypatch.delenv("OPENAI_APIKEY", raising=False)

class DummyChoice:
    def __init__(self, content: str):
        self.message = type("M", (), {"content": content})

class DummyResponse:
    def __init__(self, content: str):
        self.choices = [DummyChoice(content)]

def test_get_final_diagnosis_success(monkeypatch):
    # Stub OpenAI-Call mit gültiger JSON-Antwort
    dummy_json = json.dumps({"message": "Diagnose OK", "details": {"foo": "bar"}})
    monkeypatch.setattr(
        openai.ChatCompletion, "create",
        lambda *args, **kwargs: DummyResponse(dummy_json)
    )

    session_log = [{"role": "user", "content": "Test"}]
    known_facts = {"symptom": "bellend"}
    resp = get_final_diagnosis(session_log, known_facts)

    assert isinstance(resp, FinalDiagnosisResponse)
    assert resp.message == "Diagnose OK"
    assert resp.details == {"foo": "bar"}

def test_get_final_diagnosis_invalid_json(monkeypatch):
    # Stub mit ungültigem JSON
    monkeypatch.setattr(
        openai.ChatCompletion, "create",
        lambda *args, **kwargs: DummyResponse("not a json")
    )
    with pytest.raises(RuntimeError) as exc:
        get_final_diagnosis([], {})
    assert "Fehler bei Verarbeitung" in str(exc.value)

def test_get_final_diagnosis_validation_error(monkeypatch):
    # Stub mit JSON, das das Pydantic-Modell nicht erfüllt (fehlt 'message')
    bad_json = json.dumps({"details": {}})
    monkeypatch.setattr(
        openai.ChatCompletion, "create",
        lambda *args, **kwargs: DummyResponse(bad_json)
    )
    with pytest.raises(RuntimeError) as exc:
        get_final_diagnosis([], {})
    assert "Fehler bei Verarbeitung" in str(exc.value)
