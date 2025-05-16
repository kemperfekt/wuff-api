# src/orchestrator/flow_orchestrator.py

from typing import List
from src.models.flow_models import AgentMessage, FlowStep
from src.state.session_state import SessionState
from src.agents.dog_agent import DogAgent

dog_agent = DogAgent()


def handle_message(user_input: str, state: SessionState) -> List[AgentMessage]:
    user_input = user_input.strip().lower()

    # Restart bei bestimmten Eingaben
    if user_input in ["neu", "restart", "von vorne"]:
        state.current_step = FlowStep.GREETING
        state.active_symptom = ""
        return [AgentMessage(role=dog_agent.role, content="Okay, wir starten neu. Was möchtest du mir erzählen?")]

    step = state.current_step
    messages: List[AgentMessage] = []

    if step == FlowStep.GREETING:
        messages.append(AgentMessage(role=dog_agent.role, content="Hallo! Ich bin dein Hund. Was ist los?"))
        state.current_step = FlowStep.WAIT_FOR_SYMPTOM

    elif step == FlowStep.WAIT_FOR_SYMPTOM:
        if len(user_input) < 5:
            messages.append(AgentMessage(role=dog_agent.role, content="Magst du mir genauer sagen, was passiert ist?"))
        else:
            state.active_symptom = user_input
            messages.append(AgentMessage(role=dog_agent.role, content="Ah, verstehe… Aus meiner Sicht fühlt sich das so an: [Dummy Hundeperspektive]. Willst du, dass ich versuche zu verstehen, warum ich das mache?"))
            state.current_step = FlowStep.WAIT_FOR_CONFIRMATION

    elif step == FlowStep.WAIT_FOR_CONFIRMATION:
        if "ja" in user_input:
            messages.append(AgentMessage(role=dog_agent.role, content="Gut, dann brauche ich ein bisschen mehr Kontext. Wo war das? Wer war dabei?"))
            state.current_step = FlowStep.WAIT_FOR_CONTEXT
        elif "nein" in user_input:
            messages.append(AgentMessage(role=dog_agent.role, content="Okay, kein Problem. Wenn du es dir anders überlegst, sag einfach Bescheid."))
            state.current_step = FlowStep.END_OR_RESTART
        else:
            messages.append(AgentMessage(role=dog_agent.role, content="Magst du mir einfach 'Ja' oder 'Nein' sagen?"))

    elif step == FlowStep.WAIT_FOR_CONTEXT:
        if len(user_input) < 5:
            messages.append(AgentMessage(role=dog_agent.role, content="Ich brauch noch ein bisschen mehr Info… Wo war das genau, was war los?"))
        else:
            messages.append(AgentMessage(role=dog_agent.role, content="Danke. Wenn ich das mit meinem Instinkt vergleiche, sieht es so aus: [Dummy Diagnose]. Willst du nochmal was anderes erzählen?"))
            state.current_step = FlowStep.END_OR_RESTART

    elif step == FlowStep.END_OR_RESTART:
        if "ja" in user_input:
            state.current_step = FlowStep.WAIT_FOR_SYMPTOM
            messages.append(AgentMessage(role=dog_agent.role, content="Okay, was möchtest du mir diesmal erzählen?"))
        elif "nein" in user_input:
            messages.append(AgentMessage(role=dog_agent.role, content="Alles klar, dann ruh ich mich mal aus. Bis bald."))
        else:
            messages.append(AgentMessage(role=dog_agent.role, content="Sag einfach 'Ja' für ein neues Thema oder 'Nein' zum Beenden."))

    else:
        messages.append(AgentMessage(role=dog_agent.role, content="Ich bin kurz verwirrt… lass uns neu starten."))
        state.current_step = FlowStep.GREETING

    return messages