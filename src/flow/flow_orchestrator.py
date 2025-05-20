# src/orchestrator/flow_orchestrator.py

from typing import List, Dict, Any, Callable, Awaitable
from src.models.flow_models import AgentMessage, FlowStep
from src.state.session_state import SessionState, SessionStore
from src.agents.dog_agent import DogAgent
from src.agents.companion_agent import CompanionAgent
from src.services.gpt_service import validate_user_input
from src.services.rag_service import RAGService

# Handler-Typ-Definition für bessere Lesbarkeit
StepHandler = Callable[[SessionState, str], Awaitable[List[AgentMessage]]]

class FlowOrchestrator:
    """Orchestriert den Konversationsfluss in einer modularen Struktur"""
    
    def __init__(self, session_store_instance):
        self.session_store = session_store_instance
        self.dog_agent = DogAgent()
        self.companion_agent = CompanionAgent()
        
        # Mapping von Schritten zu Handlern für bessere Struktur
        self.step_handlers: Dict[FlowStep, StepHandler] = {
            FlowStep.GREETING: self._handle_greeting,
            FlowStep.WAIT_FOR_SYMPTOM: self._handle_symptom_input,
            FlowStep.WAIT_FOR_CONFIRMATION: self._handle_confirmation,
            FlowStep.WAIT_FOR_CONTEXT: self._handle_context_input,
            FlowStep.ASK_FOR_EXERCISE: self._handle_exercise_request,
            FlowStep.END_OR_RESTART: self._handle_end_or_restart,
            FlowStep.FEEDBACK_Q1: self._handle_feedback_q1,
            FlowStep.FEEDBACK_Q2: self._handle_feedback_q2,
            FlowStep.FEEDBACK_Q3: self._handle_feedback_q3,
            FlowStep.FEEDBACK_Q4: self._handle_feedback_q4,
            FlowStep.FEEDBACK_Q5: self._handle_feedback_q5,
        }
    
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
        state = self.session_store.get_or_create(session_id)
        
        # Benutzernachricht zur Session hinzufügen, wenn nicht leer
        if user_input:
            state.messages.append(AgentMessage(sender="user", text=user_input))
        
        user_input = user_input.strip().lower() if user_input else ""

        # Spezialkommandos für Neustart
        if user_input in ["neu", "restart", "von vorne"]:
            return await self._handle_restart(state)

        # Step-basierten Handler auswählen und ausführen
        handler = self.step_handlers.get(state.current_step)
        if handler:
            try:
                messages = await handler(state, user_input)
            except Exception as e:
                print(f"❌ Fehler im Handler für {state.current_step}: {e}")
                messages = [AgentMessage(
                    sender=self.dog_agent.role,
                    text="Entschuldige, es ist ein Problem aufgetreten. Lass uns neu starten."
                )]
                state.current_step = FlowStep.GREETING
        else:
            # Fallback für unbekannte Schritte
            messages = [AgentMessage(
                sender=self.dog_agent.role,
                text="Ich bin kurz verwirrt… lass uns neu starten."
            )]
            state.current_step = FlowStep.GREETING

        # Nachrichten zur Session hinzufügen
        state.messages.extend(messages)
        return messages
    
    async def _handle_restart(self, state: SessionState) -> List[AgentMessage]:
        """Behandelt einen Neustart-Request"""
        state.current_step = FlowStep.GREETING
        state.active_symptom = ""
        return [AgentMessage(
            sender=self.dog_agent.role,
            text="Okay, wir starten neu. Was möchtest du mir erzählen?"
        )]
    
    async def _handle_greeting(self, state: SessionState, user_input: str) -> List[AgentMessage]:
        """Behandelt den Begrüßungsschritt"""
        state.current_step = FlowStep.WAIT_FOR_SYMPTOM
        return [AgentMessage(
            sender=self.dog_agent.role,
            text="Hallo! Schön, dass Du da bist. Ich erkläre Dir Hundeverhalten aus der Hundeperspektive. Bitte beschreibe ein Verhalten oder eine Situation!"
        )]
    
async def _handle_symptom_input(self, state: SessionState, user_input: str) -> List[AgentMessage]:
    """Behandelt die Eingabe eines Symptoms - delegiert an DogAgent"""
    if not user_input:
        return [AgentMessage(
            sender=self.dog_agent.role,
            text="Ich verstehe nicht ganz. Kannst du mir ein Verhalten beschreiben?"
        )]
    
    is_valid = await validate_user_input(user_input)
    if not is_valid:
        state.current_step = FlowStep.END_OR_RESTART
        return [AgentMessage(
            sender=self.dog_agent.role,
            text="Hm… das klingt nicht nach einem Hundeverhalten. Willst du neu starten?"
        )]
    
    if len(user_input) < 10:
        return [AgentMessage(
            sender=self.dog_agent.role,
            text="Kannst Du das bitte etwas ausführlicher beschreiben?"
        )]
    
    # Verhalten speichern und zur Bestätigung weitergehen
    state.active_symptom = user_input
    state.current_step = FlowStep.WAIT_FOR_CONFIRMATION
    
    # GEÄNDERT: Delegation an den DogAgent für konsistente Antworten
    try:
        # Kontext mit relevanten Informationen anreichern
        context = {
            "is_first_response": True,  # Gibt an, dass dies die erste Antwort ist
            "additional_context": ""    # Kein zusätzlicher Kontext in diesem Schritt
        }
        
        # WICHTIG: Nur eine Teil-Antwort vom DogAgent anfordern
        partial_response = await self.dog_agent.respond(user_input, state.session_id, context)
        
        # Für den ersten Schritt nur die erste Nachricht zurückgeben und fragen, ob der User mehr wissen möchte
        if partial_response and len(partial_response) > 0:
            first_message = partial_response[0]
            return [AgentMessage(
                sender=self.dog_agent.role,
                text=f"{first_message.text} Magst Du mehr erfahren, warum ich mich so verhalte?"
            )]
        else:
            # Fallback, falls keine Antwort erhalten wurde
            return [AgentMessage(
                sender=self.dog_agent.role,
                text="Aus meiner Sicht fühlt sich das so an... Magst Du erfahren, warum ich mich so verhalte?"
            )]
            
    except Exception as e:
        print(f"❌ Fehler bei der Symptomanalyse: {e}")
        return [AgentMessage(
            sender=self.dog_agent.role,
            text="Aus meiner Sicht fühlt sich das so an... Magst Du erfahren, warum ich mich so verhalte?"
        )]
    
    async def _handle_confirmation(self, state: SessionState, user_input: str) -> List[AgentMessage]:
        """Behandelt die Bestätigung des Nutzers, mehr zu erfahren"""
        if "ja" in user_input:
            state.current_step = FlowStep.WAIT_FOR_CONTEXT
            return [AgentMessage(
                sender=self.dog_agent.role,
                text="Gut, dann brauche ich ein bisschen mehr Informationen. Bitte beschreibe, wie es zu der Situation kam, wer dabei war und was sonst noch wichtig sein könnte."
            )]
        elif "nein" in user_input:
            state.current_step = FlowStep.END_OR_RESTART
            return [AgentMessage(
                sender=self.dog_agent.role,
                text="Okay, kein Problem. Wenn du es dir anders überlegst, sag einfach Bescheid."
            )]
        else:
            return [AgentMessage(
                sender=self.dog_agent.role,
                text="Magst du mir einfach 'Ja' oder 'Nein' sagen?"
            )]
    
    async def _handle_context_input(self, state: SessionState, user_input: str) -> List[AgentMessage]:
        """Behandelt die Kontexteingabe des Nutzers"""
        if len(user_input) < 5:
            return [AgentMessage(
                sender=self.dog_agent.role,
                text="Ich brauch noch ein bisschen mehr Info… Wo war das genau, was war los?"
            )]
        
        # Nach dem Kontext: Diagnose und Übungsangebot
        state.current_step = FlowStep.ASK_FOR_EXERCISE
        return [
            AgentMessage(
                sender=self.dog_agent.role,
                text="Danke. Wenn ich das mit meinem Instinkt vergleiche, sieht es so aus: [Dummy Diagnose]."
            ),
            AgentMessage(
                sender=self.dog_agent.role,
                text="Möchtest du eine Lernaufgabe, die dir in dieser Situation helfen kann?"
            )
        ]
    
    async def _handle_exercise_request(self, state: SessionState, user_input: str) -> List[AgentMessage]:
        """Behandelt die Anfrage nach einer Übung"""
        if "ja" in user_input:
            state.current_step = FlowStep.END_OR_RESTART
            return [
                AgentMessage(
                    sender=self.dog_agent.role,
                    text="[Dummy Lernaufgabe: Übe mit Deinem Hund an der Leine ruhig zu bleiben, indem Du bei jedem Ziehen stehen bleibst und erst weitergehst, wenn die Leine wieder locker ist.]"
                ),
                AgentMessage(
                    sender=self.dog_agent.role,
                    text="Möchtest du ein weiteres Hundeverhalten verstehen?"
                )
            ]
        elif "nein" in user_input:
            # Direkt zum Feedback springen
            state.current_step = FlowStep.FEEDBACK_Q1
            state.feedback = []
            return [AgentMessage(
                sender="companion", 
                text=self.companion_agent.feedback_questions[0]
            )]
        else:
            return [AgentMessage(
                sender=self.dog_agent.role,
                text="Bitte antworte mit 'Ja' oder 'Nein' - möchtest du eine Lernaufgabe?"
            )]
    
    async def _handle_end_or_restart(self, state: SessionState, user_input: str) -> List[AgentMessage]:
        """Behandelt das Ende oder einen Neustart"""
        if "ja" in user_input:
            state.current_step = FlowStep.WAIT_FOR_SYMPTOM
            return [AgentMessage(
                sender=self.dog_agent.role,
                text="Super! Beschreibe mir bitte ein anderes Verhalten."
            )]
        elif "nein" in user_input:
            state.current_step = FlowStep.FEEDBACK_Q1
            state.feedback = []
            return [AgentMessage(
                sender="companion", 
                text=self.companion_agent.feedback_questions[0]
            )]
        else:
            return [AgentMessage(
                sender=self.dog_agent.role,
                text="Sag einfach 'Ja' für ein neues Verhalten oder 'Nein' zum Beenden und Feedback geben."
            )]
    
    async def _handle_feedback_q1(self, state: SessionState, user_input: str) -> List[AgentMessage]:
        """Behandelt die erste Feedback-Frage"""
        state.feedback.append(user_input)
        state.current_step = FlowStep.FEEDBACK_Q2
        return [AgentMessage(
            sender="companion", 
            text=self.companion_agent.feedback_questions[1]
        )]
    
    async def _handle_feedback_q2(self, state: SessionState, user_input: str) -> List[AgentMessage]:
        """Behandelt die zweite Feedback-Frage"""
        state.feedback.append(user_input)
        state.current_step = FlowStep.FEEDBACK_Q3
        return [AgentMessage(
            sender="companion", 
            text=self.companion_agent.feedback_questions[2]
        )]
    
    async def _handle_feedback_q3(self, state: SessionState, user_input: str) -> List[AgentMessage]:
        """Behandelt die dritte Feedback-Frage"""
        state.feedback.append(user_input)
        state.current_step = FlowStep.FEEDBACK_Q4
        return [AgentMessage(
            sender="companion", 
            text=self.companion_agent.feedback_questions[3]
        )]
    
    async def _handle_feedback_q4(self, state: SessionState, user_input: str) -> List[AgentMessage]:
        """Behandelt die vierte Feedback-Frage"""
        state.feedback.append(user_input)
        state.current_step = FlowStep.FEEDBACK_Q5
        return [AgentMessage(
            sender="companion", 
            text=self.companion_agent.feedback_questions[4]
        )]
    
    async def _handle_feedback_q5(self, state: SessionState, user_input: str) -> List[AgentMessage]:
        """Behandelt die fünfte Feedback-Frage und speichert das Feedback"""
        state.feedback.append(user_input)
        try:
            await self.companion_agent.save_feedback(state.session_id, state.feedback, state.messages)
        except Exception as e:
            print(f"⚠️ Fehler beim Speichern des Feedbacks: {e} — Feedback wird nicht gespeichert.")
        
        state.current_step = FlowStep.GREETING
        return [AgentMessage(
            sender="companion", 
            text="Danke für Dein Feedback!"
        )]


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