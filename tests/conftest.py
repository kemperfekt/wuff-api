# tests/conftest.py

import os
import pytest
from fastapi.testclient import TestClient
from src.main import app
import src.services.retrieval as retrieval
from src.models.symptom_models import SymptomInfo
from src.models.instinct_models import InstinktVeranlagung
from src.services.state import load_state, save_state as _orig_save_state

client = TestClient(app)

class DummyState:
    def __init__(self):
        self.history = []
        self.known_facts = {}

    def add_message(self, role, content):
        self.history.append({"role": role, "content": content})

@pytest.fixture(autouse=True)
def stub_state_and_retrieval(monkeypatch):
    # 1) Stub state.load_state / save_state
    monkeypatch.setattr("src.services.state.load_state", lambda sid: DummyState())
    monkeypatch.setattr("src.services.state.save_state", lambda sid, state: None)

    # 2) Stub OpenAI Key
    monkeypatch.setenv("OPENAI_APIKEY", "testkey")

    # 3) get_client stubben auf einen Dummy mit query/get/with_where/do
    class DummyWeaviateClient:
        def __init__(self):
            self.query = self
        def get(self, class_name, properties):
            return self
        def with_where(self, clause):
            return self
        def do(self):
            return {"data": {"Get": {}}}
    monkeypatch.setattr(retrieval, "get_client", lambda: DummyWeaviateClient())

    # 4) Stub retrieval functions
    monkeypatch.setattr(
        retrieval,
        "get_symptom_info",
        lambda s: SymptomInfo(
            symptom_name="X",
            beschreibung="Desc",
            erste_hilfe="EH",
            instinktvarianten={"jagd": "J"}
        )
    )
    monkeypatch.setattr(
        retrieval,
        "get_instinkt_profile",
        lambda g: InstinktVeranlagung(
            gruppen_code="G",
            gruppe="Grp",
            untergruppe="Sub",
            funktion="F",
            merkmale="M",
            anforderungen="A",
            instinkte={"jagd": 10}
        )
    )
    monkeypatch.setattr(retrieval, "get_breed_info", lambda b: None)

    yield

    # cleanup
    monkeypatch.delenv("OPENAI_APIKEY", raising=False)
