# src/agents/flow_agent.py

from typing import Dict

from src.services.state import load_state, save_state
from src.agents.dog_agent import run_dog_agent
from src.agents.coach_agent import run_coach_agent
from src.agents.mentor_agent import run_mentor_agent
from src.agents.trainer_agent import run_trainer_agent

def run_full_flow(session_id: str, symptom_input: str) -> Dict:
    state = load_state(session_id)

    # === Phase 1: Hund erklärt ===
    if not any(m["role"] == "assistant_dog" for m in state.history):
        dog_response = run_dog_agent(symptom_input)
        state.add_message("assistant_dog", dog_response["text"])
        save_state(session_id, state)
        return {"question": dog_response["text"]}

    # === Phase 2: Coach stellt Rückfragen oder Diagnose ===
    if not any(m["role"] == "assistant_coach" for m in state.history):
        coach_response = run_coach_agent(
            history=state.history,
            dog_explanation=state.history[-1]["content"],
            symptom_input=symptom_input
        )
        if "question" in coach_response:
            state.add_message("assistant_coach", coach_response["question"])
            save_state(session_id, state)
            return {"question": coach_response["question"]}
        else:
            state.add_message("assistant_coach", coach_response["message"])
            state.known_facts.update(coach_response["details"])
            save_state(session_id, state)

    # === Phase 3: Mentor erklärt Hintergründe, falls nötig ===
    if not any(m["role"] == "assistant_mentor" for m in state.history):
        mentor_response = run_mentor_agent(
            history=state.history,
            known_facts=state.known_facts
        )
        state.add_message("assistant_mentor", mentor_response["explanation"])
        save_state(session_id, state)
        return {"message": mentor_response["explanation"]}

    # === Phase 4: Trainer erstellt Plan ===
    if not any(m["role"] == "assistant_trainer" for m in state.history):
        trainer_response = run_trainer_agent(
            history=state.history,
            known_facts=state.known_facts
        )
        state.add_message("assistant_trainer", trainer_response["plan"])
        state.known_facts.update({"trainer_tips": trainer_response["tips"]})
        save_state(session_id, state)
        return {
            "message": trainer_response["plan"],
            "details": {"tips": trainer_response["tips"]}
        }

    # Fallback (sollte nicht erreicht werden)
    return {"message": "Die Diagnose ist abgeschlossen."}
