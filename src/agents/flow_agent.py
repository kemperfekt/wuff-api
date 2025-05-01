# src/agents/flow_agent.py

from typing import Dict, Any, List
from src.services.state import load_state, save_state
from .coach_agent import run_coach_agent
from .mentor_agent import run_mentor_agent
from .trainer_agent import run_trainer_agent
from .dog_agent import run_dog_agent  # dein bestehender Hund-Flow

def run_full_flow(session_id: str, user_input: str) -> Dict[str, Any]:
    state = load_state(session_id)
    state.add_message("user", user_input)

    # Dog-Agent
    dog_resp = run_dog_agent(state.history, user_input)
    state.add_message("assistant_dog", dog_resp.get("text", dog_resp.get("question","")))
    save_state(session_id, state)
    if "question" in dog_resp:
        return {"question": dog_resp["question"]}

    # Coach-Agent
    coach_resp = run_coach_agent(state.history, dog_resp["text"])
    state.add_message("assistant_coach", coach_resp.get("question", coach_resp.get("diagnosis")))
    save_state(session_id, state)
    if "question" in coach_resp:
        return {"question": coach_resp["question"]}

    # Mentor-Agent
    mentor_resp = run_mentor_agent(state.history, coach_resp)
    state.add_message("assistant_mentor", mentor_resp["explanation"])
    save_state(session_id, state)

    # Trainer-Agent
    trainer_resp = run_trainer_agent(state.history, mentor_resp)
    state.add_message("assistant_trainer", trainer_resp["plan"])
    save_state(session_id, state)

    # Finale Ausgabe
    return {"message": trainer_resp["plan"], "details": {"tips": trainer_resp["tips"]}}
