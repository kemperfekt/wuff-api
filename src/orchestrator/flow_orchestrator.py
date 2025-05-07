# src/orchestrator/flow_orchestrator.py

from typing import List
from models.flow_models import AgentMessage
from agents.coach_agent import CoachAgent
from agents.dog_agent import DogAgent
from state.session_state import SessionState, SymptomState, AgentStatus


dog_agent = DogAgent()
coach_agent = CoachAgent()


def handle_symptom(symptom_input: str, instinktvarianten: dict, state: SessionState) -> List[AgentMessage]:
    """
    Führt einen einfachen Dialogfluss aus, verwendet explizit übergebenen SessionState:
    1. Hund reagiert emotional auf das Symptom
    2. Coach stellt Rückfragen zu Instinkten
    """

    messages: List[AgentMessage] = []

    # Initialisiere Agentenzustände bei Bedarf
    for agent in [dog_agent.role, coach_agent.role]:
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

    # 2. Coach stellt Rückfragen
    if state.agent_status[coach_agent.role].is_first_message:
        messages += [AgentMessage(role=coach_agent.role, content=coach_agent.greeting_text)]
        state.agent_status[coach_agent.role].is_first_message = False

    messages += coach_agent.generate_rueckfragen(
        symptom_name=symptom_input,
        instinktvarianten=instinktvarianten,
    )

    return messages