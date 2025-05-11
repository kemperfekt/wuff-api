# src/orchestrator/flow_orchestrator.py

from typing import List
from src.models.flow_models import AgentMessage
from src.agents.dog_agent import DogAgent
from src.state.session_state import SessionState, SymptomState, AgentStatus
from src.services.message_utils import safe_message


dog_agent = DogAgent()


def handle_symptom(symptom_input: str, instinktvarianten: dict, state: SessionState) -> List[AgentMessage]:
    """
    Führt einen einfachen Dialogfluss aus, verwendet explizit übergebenen SessionState:
    1. Hund reagiert emotional auf das Symptom
    2. Coach stellt Rückfragen zu Instinkten
    """

    messages: List[AgentMessage] = []

    # Initialisiere Agentenzustände bei Bedarf
    for agent in [dog_agent.role]:
        if agent not in state.agent_status:
            state.agent_status[agent] = AgentStatus()

    # Symptom im State erfassen
    if symptom_input not in state.symptoms:
        state.symptoms[symptom_input] = SymptomState(name=symptom_input)
        state.active_symptom = symptom_input

    # 1. Hund schildert Erlebnis
    if state.agent_status[dog_agent.role].is_first_message:
        messages += dog_agent.respond(
            user_input=symptom_input,
            is_first_message=True
        )
        state.agent_status[dog_agent.role].is_first_message = False

    return messages