# src/agents/flow_agent.py

from typing import List, Dict, Any
import src.services.state as state_mod
from src.agents.dog_agent import run_dog_agent
from src.agents.coach_agent import run_coach_agent
from src.agents.mentor_agent import run_mentor_agent
from src.agents.trainer_agent import run_trainer_agent

def run_full_flow(session_id: str, user_input: str) -> Dict[str, Any]:
    """
    Orchestriert den gesamten Diagnose-Flow:
    1) Hund-Agent
    2) Coach-Agent
    3) Mentor-Agent
    4) Trainer-Agent
    Speichert zwischendrin State über src.services.state.
    """

    # 1) Lade Session-State
    state = state_mod.load_state(session_id)
    state.add_message("user", user_input)

    # 2) Dog-Agent
    dog_resp = run_dog_agent(state.history, user_input)
    state.add_message("assistant_dog", dog_resp.get("text", ""))

    # Wenn Dog-Agent direkt eine Frage stellt:
    if "question" in dog_resp:
        state_mod.save_state(session_id, state)
        return {"question": dog_resp["question"]}

    # 3) Coach-Agent
    coach_resp = run_coach_agent(state.history, dog_resp.get("text", ""), user_input)
    state.add_message("assistant_coach", coach_resp.get("question") or "")

    # Wenn Coach-Agent eine Frage stellt:
    if "question" in coach_resp:
        state_mod.save_state(session_id, state)
        return {"question": coach_resp["question"]}

    # 4) Mentor-Agent
    mentor_resp = run_mentor_agent(state.history, coach_resp)
    state.add_message("assistant_mentor", mentor_resp.get("explanation", ""))

    # 5) Trainer-Agent
    trainer_data = run_trainer_agent(state.history, mentor_resp)
    state.add_message("assistant_trainer", str(trainer_data))

    # --- Finale Rückgabe an Tests anpassen ---
    # Tests erwarten keys "message" und "details"
    result = {
        "message": trainer_data["plan"],
        "details": {"tips": trainer_data["tips"]}
    }

    # Speichere State und return
    state_mod.save_state(session_id, state)
    return result
