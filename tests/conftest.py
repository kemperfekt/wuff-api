# tests/conftest.py

import os
import pytest
from fastapi.testclient import TestClient
from src.main import app

@pytest.fixture(scope="session")
def client():
    return TestClient(app)

class DummyState:
    def __init__(self):
        self.history = []
        self.known_facts = {}
    def add_message(self, role, content):
        self.history.append({"role": role, "content": content})

@pytest.fixture(autouse=True)
def patch_state(monkeypatch):
    def dummy_load_state(session_id):
        return DummyState()
    def dummy_save_state(session_id, state):
        # state is ignored
        pass

    # Patch load_state/save_state in services.state
    monkeypatch.setattr("src.services.state.load_state", dummy_load_state)
    monkeypatch.setattr("src.services.state.save_state", dummy_save_state)
