# tests/test_mentor_agent.py
import os
import pytest
from src.agents.mentor_agent import run_mentor_agent

class DummyClient:
    def __init__(self, content):
        self._content = content
        self.chat = self
        self.completions = self

    def create(self, model, messages, **kwargs):
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

def test_mentor_agent(monkeypatch):
    dummy_text = "Hier die Erklärung"
    monkeypatch.setattr(
        "src.agents.mentor_agent.init_openai_client",
        lambda: DummyClient(dummy_text)
    )
    # history kann leer sein, coach_resp beliebiges Dict
    res = run_mentor_agent([], {"diagnosis": {"foo": "bar"}})
    assert "explanation" in res
    assert res["explanation"] == dummy_text
