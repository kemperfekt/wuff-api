# tests/test_diagnose_service.py

import json
import pytest
from src.services.diagnose_service import get_final_diagnosis, FinalDiagnosisResponse

class DummyResponse:
    def __init__(self, content):
        self.choices = [type("Choice", (), {"message": type("Message", (), {"content": content})})]

def test_get_final_diagnosis_success(monkeypatch):
    dummy_payload = {"message": "Alles gut", "details": {"instinkt": "Beute"}}
    dummy_content = json.dumps(dummy_payload)
    def dummy_create(*args, **kwargs):
        return DummyResponse(dummy_content)
    monkeypatch.setattr(
        "src.services.diagnose_service.openai.ChatCompletion.create",
        dummy_create
    )
    session_log = [{"role": "user", "content": "Test"}]
    known_facts = {"foo": "bar"}
    result = get_final_diagnosis(session_log, known_facts)
    assert isinstance(result, FinalDiagnosisResponse)
    assert result.message == dummy_payload["message"]
    assert result.details == dummy_payload["details"]

def test_get_final_diagnosis_invalid_json(monkeypatch):
    def dummy_create(*args, **kwargs):
        return DummyResponse("nicht-json")
    monkeypatch.setattr(
        "src.services.diagnose_service.openai.ChatCompletion.create",
        dummy_create
    )
    with pytest.raises(RuntimeError) as excinfo:
        get_final_diagnosis([], {})
    assert "Fehler bei Verarbeitung der Diagnose-Antwort" in str(excinfo.value)
