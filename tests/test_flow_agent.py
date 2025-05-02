# tests/test_flow_agent.py

import pytest
from unittest.mock import patch

from src.agents.flow_agent import run_full_flow

@pytest.fixture
def stub_all_agents():
    with patch("src.agents.flow_agent.run_dog_agent") as mock_dog, \
         patch("src.agents.flow_agent.run_coach_agent") as mock_coach, \
         patch("src.agents.flow_agent.run_mentor_agent") as mock_mentor, \
         patch("src.agents.flow_agent.run_trainer_agent") as mock_trainer:

        yield mock_dog, mock_coach, mock_mentor, mock_trainer

def test_flow_returns_question_at_dog(stub_all_agents):
    mock_dog, _, _, _ = stub_all_agents
    mock_dog.return_value = {"question": "Hund erklärt Problem."}

    result = run_full_flow("session1", "zieht an der Leine")
    assert result["question"] == "Hund erklärt Problem."

def test_flow_returns_question_at_coach(stub_all_agents):
    mock_dog, mock_coach, _, _ = stub_all_agents
    mock_dog.return_value = {"text": "Hund erklärt Problem."}
    mock_coach.return_value = {"question": "Coach stellt Rückfrage."}

    result = run_full_flow("session2", "zieht an der Leine")
    assert result["question"] == "Coach stellt Rückfrage."

def test_flow_returns_final_plan(stub_all_agents):
    mock_dog, mock_coach, mock_mentor, mock_trainer = stub_all_agents
    mock_dog.return_value = {"text": "Hund erklärt Problem."}
    mock_coach.return_value = {"message": "Coach akzeptiert Antwort."}
    mock_mentor.return_value = {"explanation": "Mentor erklärt Diagnose."}
    mock_trainer.return_value = {
        "plan": "Therapieplan erstellt.",
        "details": {"tips": ["Tipp 1", "Tipp 2"]}
    }

    result = run_full_flow("session3", "zieht an der Leine")
    assert result["plan"] == "Therapieplan erstellt."
    assert result["details"]["tips"] == ["Tipp 1", "Tipp 2"]
