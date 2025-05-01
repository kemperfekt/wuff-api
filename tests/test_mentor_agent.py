import pytest
import src.agents.mentor_agent as mentor_mod
from src.agents.mentor_agent import init_openai_client, run_mentor_agent, MentorResponse

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

def test_run_mentor_agent(monkeypatch):
    explanation = "Hier die Erklärung"
    # Stub init_openai_client
    monkeypatch.setattr(
        "src.agents.mentor_agent.init_openai_client",
        lambda: DummyClient(explanation)
    )
    # Führe Mentor-Agent aus
    out = run_mentor_agent([], {"diagnosis": {"foo": "bar"}})
    assert isinstance(out, dict)
    assert out["explanation"] == explanation
