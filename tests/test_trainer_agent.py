import json
import pytest
import src.agents.trainer_agent as trainer_mod
from src.agents.trainer_agent import init_openai_client, run_trainer_agent, TrainingPlan

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
def fix_api_key(monkeypatch):
    monkeypatch.setenv("OPENAI_APIKEY", "testkey")
    yield
    monkeypatch.delenv("OPENAI_APIKEY", raising=False)

def test_init_openai_client_no_key(monkeypatch):
    monkeypatch.delenv("OPENAI_APIKEY", raising=False)
    with pytest.raises(RuntimeError):
        init_openai_client()

def test_run_trainer_agent(monkeypatch):
    plan_payload = {"plan": "Täglich 5min Leine laufen", "tips": ["Langsam steigern", "Lob verwenden"]}
    content = json.dumps(plan_payload)
    # Stub init_openai_client
    monkeypatch.setattr(
        "src.agents.trainer_agent.init_openai_client",
        lambda: DummyClient(content)
    )
    # Führe Trainer-Agent aus
    out = run_trainer_agent([], {"explanation": "Irrelevant"})
    assert isinstance(out, dict)
    assert out["plan"] == plan_payload["plan"]
    assert out["tips"] == plan_payload["tips"]
