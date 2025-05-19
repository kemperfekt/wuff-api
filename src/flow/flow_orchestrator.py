# src/orchestrator/flow_orchestrator.py

from typing import List, Dict, Any
from src.models.flow_models import AgentMessage, FlowStep
from src.state.session_state import SessionState, SessionStore
from src.agents.dog_agent import DogAgent
from src.agents.companion_agent import CompanionAgent
from src.services.gpt_service import validate_user_input

# Singleton-Instanz des SessionStore
# Stellen sicher, dass wir dieselbe Instanz wie in main.py verwenden
session_store = None

class FlowOrchestrator:
    """Orchestriert den Konversationsfluss"""
    
    def __init__(self, session_store_instance):
        global session_store
        session_store = session_store_instance
        self.dog_agent = DogAgent()
        self.companion_agent = CompanionAgent()
    
    async def handle_message(self, session_id: str, user_input: str) -> List[AgentMessage]:
        """
        Verarbeitet eine Benutzernachricht.
        
        Args:
            session_id: ID der Session
            user_input: Nachricht des Benutzers
            
        Returns:
            Liste von Antwort-Nachrichten
        """
        # Session holen
        state = session_store.get_or_create(session_id)
        
        # Benutzernachricht zur Session hinzufügen, wenn nicht leer
        if user_input:
            state.messages.append(AgentMessage(sender="user", text=user_input))
        
        # Originale Logik aus deinem bestehenden handle_message
        user_input = user_input.strip().lower() if user_input else ""

        # Restart bei bestimmten Eingaben
        if user_input in ["neu", "restart", "von vorne"]:
            state.current_step = FlowStep.GREETING
            state.active_symptom = ""
            messages = [AgentMessage(sender=self.dog_agent.role, text="Okay, wir starten neu. Was möchtest du mir erzählen?")]
            state.messages.extend(messages)
            return messages

        step = state.current_step
        messages: List[AgentMessage] = []

        if step == FlowStep.GREETING:
            messages.append(AgentMessage(sender=self.dog_agent.role, text="Hallo! Schön, dass Du da bist. Ich erkläre Dir Hundeverhalten aus der Hundeperspektive. Bitte beschreibe ein Verhalten oder eine Situation!"))
            state.current_step = FlowStep.WAIT_FOR_SYMPTOM
            state.messages.extend(messages)
            return messages

        elif step == FlowStep.WAIT_FOR_SYMPTOM:
            if not user_input:
                # Fall: Leere Nachricht
                messages.append(AgentMessage(sender=self.dog_agent.role, text="Ich verstehe nicht ganz. Kannst du mir ein Verhalten beschreiben?"))
                state.messages.extend(messages)
                return messages
            
            if not validate_user_input(user_input):
                messages.append(AgentMessage(
                    sender=self.dog_agent.role,
                    text="Hm… das klingt nicht nach einem Hundeverhalten. Willst du neu starten?"
                ))
                state.current_step = FlowStep.END_OR_RESTART
                state.messages.extend(messages)
                return messages
            
            if len(user_input) < 10:
                messages.append(AgentMessage(sender=self.dog_agent.role, text="Kannst Du das bitte etwas ausführlicher beschreiben?"))
                state.messages.extend(messages)
                return messages
            else:
                state.active_symptom = user_input
                # Benutzernachricht bereits gespeichert, daher nicht nochmal speichern
                messages.append(AgentMessage(sender=self.dog_agent.role, text="Ah, verstehe… Aus meiner Sicht fühlt sich das so an: [Dummy Hundeperspektive]. Magst Du erfahren, warum ich mich so verhalte?"))
                state.current_step = FlowStep.WAIT_FOR_CONFIRMATION
                state.messages.extend(messages)
                return messages

        elif step == FlowStep.WAIT_FOR_CONFIRMATION:
            # Benutzernachricht bereits gespeichert, daher nicht nochmal speichern
            if "ja" in user_input:
                messages.append(AgentMessage(sender=self.dog_agent.role, text="Gut, dann brauche ich ein bisschen mehr Informationen. Bitte beschreibe, wie es zu der Situation kam, wer dabei war und was sonst noch wichtig sein könnte."))
                state.current_step = FlowStep.WAIT_FOR_CONTEXT
                state.messages.extend(messages)
                return messages
            elif "nein" in user_input:
                messages.append(AgentMessage(sender=self.dog_agent.role, text="Okay, kein Problem. Wenn du es dir anders überlegst, sag einfach Bescheid."))
                state.current_step = FlowStep.END_OR_RESTART
                state.messages.extend(messages)
                return messages
            else:
                messages.append(AgentMessage(sender=self.dog_agent.role, text="Magst du mir einfach 'Ja' oder 'Nein' sagen?"))
                state.messages.extend(messages)
                return messages

        elif step == FlowStep.WAIT_FOR_CONTEXT:
            # Benutzernachricht bereits gespeichert, daher nicht nochmal speichern
            if len(user_input) < 5:
                messages.append(AgentMessage(sender=self.dog_agent.role, text="Ich brauch noch ein bisschen mehr Info… Wo war das genau, was war los?"))
                state.messages.extend(messages)
                return messages
            else:
                # Nach dem Kontext kommt die Diagnose
                messages.append(AgentMessage(sender=self.dog_agent.role, text="Danke. Wenn ich das mit meinem Instinkt vergleiche, sieht es so aus: [Dummy Diagnose]."))
                state.current_step = FlowStep.FINAL_DIAGNOSIS
                messages.append(AgentMessage(sender=self.dog_agent.role, text="Möchtest du eine Lernaufgabe, die dir in dieser Situation helfen kann?"))
                state.current_step = FlowStep.ASK_FOR_EXERCISE
                state.messages.extend(messages)
                return messages

        # Nach der Diagnose folgt die Abfrage für die Lernaufgabe
        elif step == FlowStep.ASK_FOR_EXERCISE:
            if "ja" in user_input:
                # Zeige die Lernaufgabe
                messages.append(AgentMessage(sender=self.dog_agent.role, text="[Dummy Lernaufgabe: Übe mit Deinem Hund an der Leine ruhig zu bleiben, indem Du bei jedem Ziehen stehen bleibst und erst weitergehst, wenn die Leine wieder locker ist.]"))
                messages.append(AgentMessage(sender=self.dog_agent.role, text="Möchtest du ein weiteres Hundeverhalten verstehen?"))
                state.current_step = FlowStep.END_OR_RESTART
                state.messages.extend(messages)
                return messages
            elif "nein" in user_input:
                # Direkt zum Feedback springen
                messages.append(AgentMessage(sender="companion", text=self.companion_agent.feedback_questions[0]))
                state.feedback = []
                state.current_step = FlowStep.FEEDBACK_Q1
                state.messages.extend(messages)
                return messages
            else:
                messages.append(AgentMessage(sender=self.dog_agent.role, text="Bitte antworte mit 'Ja' oder 'Nein' - möchtest du eine Lernaufgabe?"))
                state.messages.extend(messages)
                return messages

        elif step == FlowStep.END_OR_RESTART:
            # Benutzernachricht bereits gespeichert, daher nicht nochmal speichern
            if "ja" in user_input:
                state.current_step = FlowStep.WAIT_FOR_SYMPTOM
                messages.append(AgentMessage(sender=self.dog_agent.role, text="Super! Beschreibe mir bitte ein anderes Verhalten."))
                state.messages.extend(messages)
                return messages
            elif "nein" in user_input:
                messages.append(AgentMessage(sender="companion", text=self.companion_agent.feedback_questions[0]))
                state.feedback = []
                state.current_step = FlowStep.FEEDBACK_Q1
                state.messages.extend(messages)
                return messages
            else:
                messages.append(AgentMessage(sender=self.dog_agent.role, text="Sag einfach 'Ja' für ein neues Verhalten oder 'Nein' zum Beenden und Feedback geben."))
                state.messages.extend(messages)
                return messages

        elif step == FlowStep.FEEDBACK_Q1:
            # Benutzernachricht bereits gespeichert, daher nicht nochmal speichern
            state.feedback.append(user_input)
            messages.append(AgentMessage(sender="companion", text=self.companion_agent.feedback_questions[1]))
            state.current_step = FlowStep.FEEDBACK_Q2
            state.messages.extend(messages)
            return messages

        elif step == FlowStep.FEEDBACK_Q2:
            # Benutzernachricht bereits gespeichert, daher nicht nochmal speichern
            state.feedback.append(user_input)
            messages.append(AgentMessage(sender="companion", text=self.companion_agent.feedback_questions[2]))
            state.current_step = FlowStep.FEEDBACK_Q3
            state.messages.extend(messages)
            return messages

        elif step == FlowStep.FEEDBACK_Q3:
            # Benutzernachricht bereits gespeichert, daher nicht nochmal speichern
            state.feedback.append(user_input)
            messages.append(AgentMessage(sender="companion", text=self.companion_agent.feedback_questions[3]))
            state.current_step = FlowStep.FEEDBACK_Q4
            state.messages.extend(messages)
            return messages

        elif step == FlowStep.FEEDBACK_Q4:
            # Benutzernachricht bereits gespeichert, daher nicht nochmal speichern
            state.feedback.append(user_input)
            messages.append(AgentMessage(sender="companion", text=self.companion_agent.feedback_questions[4]))
            state.current_step = FlowStep.FEEDBACK_Q5
            state.messages.extend(messages)
            return messages

        elif step == FlowStep.FEEDBACK_Q5:
            # Benutzernachricht bereits gespeichert, daher nicht nochmal speichern
            state.feedback.append(user_input)
            try:
                await self.companion_agent.save_feedback(state.session_id, state.feedback, state.messages)
            except Exception as e:
                print(f"⚠️ Fehler beim Speichern des Feedbacks: {e} — Feedback wird nicht gespeichert.")
            messages.append(AgentMessage(sender="companion", text="Danke für Dein Feedback! 🐾"))
            state.current_step = FlowStep.GREETING
            state.messages.extend(messages)
            return messages

        else:
            messages.append(AgentMessage(sender=self.dog_agent.role, text="Ich bin kurz verwirrt… lass uns neu starten."))
            state.current_step = FlowStep.GREETING
            state.messages.extend(messages)
            return messages

# Wird von main.py aufgerufen, um den Orchestrator zu initialisieren
orchestrator = None

def init_orchestrator(session_store_instance):
    global orchestrator
    orchestrator = FlowOrchestrator(session_store_instance)
    return orchestrator

# Diese Funktion ist diejenige, die von extern importiert wird
async def handle_message(session_id: str, user_input: str) -> List[AgentMessage]:
    """
    Wrapper-Funktion, die die handle_message Methode des Orchestrators aufruft.
    
    Args:
        session_id: ID der Session
        user_input: Nachricht des Benutzers
        
    Returns:
        Liste von Antwort-Nachrichten
    """
    if orchestrator is None:
        raise RuntimeError("Orchestrator wurde nicht initialisiert. Rufe init_orchestrator() auf.")
    
    return await orchestrator.handle_message(session_id, user_input)