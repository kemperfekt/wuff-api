# tests/test_dog_agent.py

import os
import pytest
from src.agents.dog_agent import init_openai_client, run_dog_agent, DogResponse

class DummyClient:
    """
    Stub-Client, der eine vordefinierte Antwort liefert.
    Simuliert OpenAI.ChatCompletion.create(...)
    """
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
def fix_api_key(monkeypatch):
    # Stelle sicher, dass OPENAI_APIKEY in allen Tests gesetzt ist
    monkeypatch.setenv("OPENAI_APIKEY", "testkey")
    yield
    monkeypatch.delenv("OPENAI_APIKEY", raising=False)

def test_init_openai_client_no_key(monkeypatch):
    monkeypatch.delenv("OPENAI_APIKEY", raising=False)
    with pytest.raises(RuntimeError) as exc:
        init_openai_client()
    assert "OpenAI APIKEY nicht gesetzt" in str(exc.value)

def test_run_dog_agent_returns_text(monkeypatch):
    dummy_text = "Ich rieche diesen Teppich und fühle mich sicher."
    # Stub init_openai_client → DummyClient liefert dummy_text
    monkeypatch.setattr(
        "src.agents.dog_agent.init_openai_client",
        lambda: DummyClient(dummy_text)
    )

    result = run_dog_agent([], "Warum bell ich nachts?")
    # Prüfe, dass das Ergebnis dem Pydantic-Modell entspricht
    assert isinstance(result, dict)
    assert "text" in result
    assert result["text"] == dummy_text
