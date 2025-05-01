# tests/test_trainer_agent.py
import os
import json
import pytest
from src.agents.trainer_agent import run_trainer_agent

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

def test_trainer_agent(monkeypatch):
    payload = {"plan": "Täglich 5min Leine laufen", "tips": ["Langsam steigern", "Lob verwenden"]}
    json_p = json.dumps(payload)
    monkeypatch.setattr(
        "src.agents.trainer_agent.init_openai_client",
        lambda: DummyClient(json_p)
    )
    res = run_trainer_agent([], {"explanation": "Irrelevant"})
    assert "plan" in res
    assert res["plan"].startswith("Täglich")
    assert isinstance(res["tips"], list)
    assert res["tips"][0] == "Langsam steigern"
