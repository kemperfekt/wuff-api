import json
import os
import pytest
import src.agents.dog_agent as dog_mod
from src.agents.dog_agent import init_openai_client, run_dog_agent, DogResponse

class DummyClient:
    def __init__(self, content):
        self._content = content
        self.chat = self
        self.completions = self

    def create(self, *args, **kwargs):
        # Simuliere OpenAI-Response mit einer choice
        return type("Resp", (), {
            "choices": [type("Choice", (), {
                "message": type("Msg", (), {"content": self._content})
            })]
        })

@pytest.fixture(autouse=True)
def fix_api_key(monkeypatch):
    # Stellt sicher, dass OPENAI_APIKEY gesetzt ist
    monkeypatch.setenv("OPENAI_APIKEY", "testkey")
    yield
    monkeypatch.delenv("OPENAI_APIKEY", raising=False)

def test_init_openai_client_no_key(monkeypatch):
    # Entferne Key und erwarte Fehler
    monkeypatch.delenv("OPENAI_APIKEY", raising=False)
    with pytest.raises(RuntimeError) as exc:
        init_openai_client()
    assert "OpenAI APIKEY nicht gesetzt" in str(exc.value)

def test_run_dog_agent_returns_text(monkeypatch):
    dummy_text = "Ich rieche diesen Teppich und fühle mich sicher."
    # Stub init_openai_client
    monkeypatch.setattr(
        "src.agents.dog_agent.init_openai_client",
        lambda: DummyClient(dummy_text)
    )

    result = run_dog_agent([], "Warum bell ich nachts?")
    # Ergebnis ist serialisiertes Pydantic-Modell
    assert isinstance(result, dict)
    assert result["text"] == dummy_text
