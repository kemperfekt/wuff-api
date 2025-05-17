from typing import List
from src.models.flow_models import AgentMessage, FlowStep
from src.state.session_state import SessionState
from src.agents.dog_agent import DogAgent
from src.agents.companion_agent import CompanionAgent
from src.services.gpt_service import validate_user_input

dog_agent = DogAgent()
companion_agent = CompanionAgent()


def handle_message(user_input: str, state: SessionState) -> List[AgentMessage]:
    user_input = user_input.strip().lower()

    # Restart bei bestimmten Eingaben
    if user_input in ["neu", "restart", "von vorne"]:
        state.current_step = FlowStep.GREETING
        state.active_symptom = ""
        messages = [AgentMessage(sender=dog_agent.role, text="Okay, wir starten neu. Was möchtest du mir erzählen?")]
        state.messages.extend(messages)
        return messages

    step = state.current_step
    messages: List[AgentMessage] = []

    if step == FlowStep.GREETING:
        messages.append(AgentMessage(sender=dog_agent.role, text="Hallo! Ich bin dein Hund. Was ist los?"))
        state.current_step = FlowStep.WAIT_FOR_SYMPTOM
        state.messages.extend(messages)
        return messages

    elif step == FlowStep.WAIT_FOR_SYMPTOM:
        if not validate_user_input(user_input):
            messages.append(AgentMessage(
                sender=dog_agent.role,
                text="Hm… das klingt nicht nach einem Hundeverhalten. Willst du neu starten?"
            ))
            state.current_step = FlowStep.END_OR_RESTART
            state.messages.extend(messages)
            return messages
        if len(user_input) < 5:
            messages.append(AgentMessage(sender=dog_agent.role, text="Magst du mir genauer sagen, was passiert ist?"))
            state.messages.extend(messages)
            return messages
        else:
            state.active_symptom = user_input
            state.messages.append(AgentMessage(sender="user", text=user_input))
            messages.append(AgentMessage(sender=dog_agent.role, text="Ah, verstehe… Aus meiner Sicht fühlt sich das so an: [Dummy Hundeperspektive]. Magst Du erfahren, warum ich mich so verhalte?"))
            state.current_step = FlowStep.WAIT_FOR_CONFIRMATION
            state.messages.extend(messages)
            return messages

    elif step == FlowStep.WAIT_FOR_CONFIRMATION:
        state.messages.append(AgentMessage(sender="user", text=user_input))
        if "ja" in user_input:
            messages.append(AgentMessage(sender=dog_agent.role, text="Gut, dann brauche ich ein bisschen mehr Kontext. Wo war das? Wer war dabei?"))
            state.current_step = FlowStep.WAIT_FOR_CONTEXT
            state.messages.extend(messages)
            return messages
        elif "nein" in user_input:
            messages.append(AgentMessage(sender=dog_agent.role, text="Okay, kein Problem. Wenn du es dir anders überlegst, sag einfach Bescheid."))
            state.current_step = FlowStep.END_OR_RESTART
            state.messages.extend(messages)
            return messages
        else:
            messages.append(AgentMessage(sender=dog_agent.role, text="Magst du mir einfach 'Ja' oder 'Nein' sagen?"))
            state.messages.extend(messages)
            return messages

    elif step == FlowStep.WAIT_FOR_CONTEXT:
        state.messages.append(AgentMessage(sender="user", text=user_input))
        if len(user_input) < 5:
            messages.append(AgentMessage(sender=dog_agent.role, text="Ich brauch noch ein bisschen mehr Info… Wo war das genau, was war los?"))
            state.messages.extend(messages)
            return messages
        else:
            messages.append(AgentMessage(sender=dog_agent.role, text="Danke. Wenn ich das mit meinem Instinkt vergleiche, sieht es so aus: [Dummy Diagnose]. Willst du nochmal was anderes erzählen?"))
            state.current_step = FlowStep.END_OR_RESTART
            state.messages.extend(messages)
            return messages

    elif step == FlowStep.END_OR_RESTART:
        state.messages.append(AgentMessage(sender="user", text=user_input))
        if "ja" in user_input:
            state.current_step = FlowStep.WAIT_FOR_SYMPTOM
            messages.append(AgentMessage(sender=dog_agent.role, text="Okay, was möchtest du mir erzählen?"))
            state.messages.extend(messages)
            return messages
        elif "nein" in user_input:
            messages.append(AgentMessage(sender="companion", text=companion_agent.feedback_questions[0]))
            state.feedback = []
            state.current_step = FlowStep.FEEDBACK_Q1
            state.messages.extend(messages)
            return messages
        else:
            messages.append(AgentMessage(sender=dog_agent.role, text="Sag einfach 'Ja' für ein neues Thema oder 'Nein' zum Beenden."))
            state.messages.extend(messages)
            return messages

    elif step == FlowStep.FEEDBACK_Q1:
        state.messages.append(AgentMessage(sender="user", text=user_input))
        state.feedback.append(user_input)
        messages.append(AgentMessage(sender="companion", text=companion_agent.feedback_questions[1]))
        state.current_step = FlowStep.FEEDBACK_Q2
        state.messages.extend(messages)
        return messages

    elif step == FlowStep.FEEDBACK_Q2:
        state.messages.append(AgentMessage(sender="user", text=user_input))
        state.feedback.append(user_input)
        messages.append(AgentMessage(sender="companion", text=companion_agent.feedback_questions[2]))
        state.current_step = FlowStep.FEEDBACK_Q3
        state.messages.extend(messages)
        return messages

    elif step == FlowStep.FEEDBACK_Q3:
        state.messages.append(AgentMessage(sender="user", text=user_input))
        state.feedback.append(user_input)
        companion_agent.save_feedback(state.session_id, state.feedback, state.messages)
        messages.append(AgentMessage(sender="companion", text="Danke für Dein Feedback! 🐾"))
        state.current_step = FlowStep.GREETING
        state.messages.extend(messages)
        return messages

    else:
        messages.append(AgentMessage(sender=dog_agent.role, text="Ich bin kurz verwirrt… lass uns neu starten."))
        state.current_step = FlowStep.GREETING
        state.messages.extend(messages)
        return messages