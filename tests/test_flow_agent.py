# tests/test_flow_agent.py

import pytest
from src.agents.flow_agent import run_full_flow

@pytest.fixture(autouse=True)
def stub_all_agents(monkeypatch):
    # 1) Dog-Agent stub: signature (history, symptom_input)
    monkeypatch.setattr(
        "src.agents.flow_agent.run_dog_agent",
        lambda history, symptom_input: {"question": "Dog fragt?"}
    )
    # 2) Coach-Agent stub: signature (history, dog_expl, symptom_input)
    monkeypatch.setattr(
        "src.agents.flow_agent.run_coach_agent",
        lambda history, dog_expl, symptom_input: {"question": "Coach fragt?"}
    )
    # 3) Mentor-Agent stub: signature (history, coach_resp)
    monkeypatch.setattr(
        "src.agents.flow_agent.run_mentor_agent",
        lambda history, coach_resp: {"explanation": "Mentor erklärt"}
    )
    # 4) Trainer-Agent stub: signature (history, mentor_resp)
    monkeypatch.setattr(
        "src.agents.flow_agent.run_trainer_agent",
        lambda history, mentor_resp: {"plan": "Plan", "tips": ["t1", "t2"]}
    )

def test_flow_returns_question_at_dog():
    out = run_full_flow("sess1", "Symptom XYZ")
    assert out == {"question": "Dog fragt?"}

def test_flow_returns_question_at_coach(monkeypatch):
    # override dog, damit er keine Frage stellt sondern nur text
    monkeypatch.setattr(
        "src.agents.flow_agent.run_dog_agent",
        lambda history, symptom_input: {"text": "dog exp"}
    )
    out = run_full_flow("sess2", "Symptom ABC")
    assert out == {"question": "Coach fragt?"}

def test_flow_returns_final_plan(monkeypatch):
    # dog & coach pass through
    monkeypatch.setattr(
        "src.agents.flow_agent.run_dog_agent",
        lambda history, symptom_input: {"text": "dog exp"}
    )
    monkeypatch.setattr(
        "src.agents.flow_agent.run_coach_agent",
        lambda history, dog_expl, symptom_input: {"message": "Diagnose", "details": {}}
    )
    # Now Mentor & Trainer run as stubbed in fixture
    out = run_full_flow("sess3", "Symptom 123")
    assert out["message"] == "Plan"
    assert out["details"] == {"tips": ["t1", "t2"]}
