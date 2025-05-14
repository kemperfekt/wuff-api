from typing import List
from src.models.flow_models import AgentMessage
from src.agents.dog_agent import DogAgent
from src.state.session_state import SessionState, SymptomState, AgentStatus
from src.services.message_utils import safe_message
from src.services.retrieval import get_instinktvarianten_for_symptom
from src.services.gpt_service import diagnose_from_instinkte


dog_agent = DogAgent()


def handle_symptom(symptom_input: str, instinktvarianten: dict, state: SessionState) -> List[AgentMessage]:
    # Rückfragen-Antwort speichern
    if state.active_symptom in state.symptoms:
        sym_state = state.symptoms[state.active_symptom]
        # Wenn offene Rückfragen zu Instinkten existieren, speichere die Antwort als Menschensicht
        for instinkt in ["jagd", "rudel", "territorial", "sexual"]:
            if getattr(sym_state, "asked_instincts", {}).get(instinkt) and instinkt not in getattr(sym_state, "instinct_answers", {}):
                if not hasattr(sym_state, "instinct_answers") or sym_state.instinct_answers is None:
                    sym_state.instinct_answers = {}
                sym_state.instinct_answers[instinkt] = symptom_input
                return [AgentMessage(role=dog_agent.role, content="Danke. Ich überlege weiter...")]
    """
    Führt einen einfachen Dialogfluss aus, verwendet explizit übergebenen SessionState:
    1. Hund reagiert emotional auf das Symptom
    """

    messages: List[AgentMessage] = []

    # Diagnoseentscheidung prüfen
    if state.awaiting_diagnosis_confirmation:
        if symptom_input.lower().strip() in ["ja", "ja.", "gern", "okay", "bitte"]:
            state.diagnosis_confirmed = True
            state.awaiting_diagnosis_confirmation = False
            return [AgentMessage(role=dog_agent.role, content="Okay, dann schauen wir mal genauer hin...")]
        else:
            state.awaiting_diagnosis_confirmation = False
            return [AgentMessage(role=dog_agent.role, content="Alles klar, sag Bescheid, wenn du mehr wissen willst.")]

    # Verarbeitung der bestätigten Diagnose-Anfrage
    if getattr(state, "diagnosis_confirmed", False):
        state.diagnosis_confirmed = False  # Status löschen
        symptom = state.active_symptom
        varianten = get_instinktvarianten_for_symptom(symptom)
        if not varianten:
            # Rückfragenlogik starten
            instinktfragen = {
                "jagd": "Habe ich mich dabei wie auf der Jagd verhalten – aufmerksam, angespannt, ganz auf ein Ziel fokussiert?",
                "rudel": "War es eine Situation, wo jemand aus unserer Gruppe gefehlt hat oder fremd war?",
                "territorial": "War das in der Nähe unseres Zuhauses oder habe ich etwas bewacht?",
                "sexual": "Gab es da vielleicht eine Begegnung mit einem anderen Hund, bei der ich mich aufgeregt habe?"
            }
            sym_state = state.symptoms.get(symptom)
            if not sym_state:
                sym_state = SymptomState()
                state.symptoms[symptom] = sym_state
            # asked_instincts initialisieren, falls nicht vorhanden
            if not hasattr(sym_state, "asked_instincts") or sym_state.asked_instincts is None:
                sym_state.asked_instincts = {}
            for instinkt, frage in instinktfragen.items():
                if not sym_state.asked_instincts.get(instinkt):
                    sym_state.asked_instincts[instinkt] = True
                    return [AgentMessage(role=dog_agent.role, content=frage)]
            # Wenn alle Antworten vorhanden: Diagnoseversuch mit gesammelten Rückfragen
            if hasattr(sym_state, "instinct_answers") and len(sym_state.instinct_answers) == 4:
                antwort = diagnose_from_instinkte(symptom, sym_state.instinct_answers)
                return [AgentMessage(role=dog_agent.role, content=antwort)]
            return [AgentMessage(role=dog_agent.role, content="Ich bin mir nicht sicher. Wollen wir nochmal von vorne anfangen?")]
        antwort = diagnose_from_instinkte(symptom, varianten)
        return [AgentMessage(role=dog_agent.role, content=antwort)]

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