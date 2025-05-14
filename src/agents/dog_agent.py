from typing import List
from src.models.flow_models import AgentMessage
from src.agents.base_agent import BaseAgent
from src.services.gpt_service import ask_gpt
from src.services.retrieval import get_symptom_info
from src.state.session_state import sessions  # hinzufügen, ganz oben bei den Imports


class DogAgent(BaseAgent):
    def __init__(self):
        # Initialisiert den DogAgent mit vordefiniertem Namen, Rolle und Begrüßungstext
        super().__init__(
            name="Hund",
            role="dog",
            greeting_text="Wuff! Ich bin dein Hund. Bitte nenne mir ein Verhalten und ich schildere dir, wie ich es erlebe.",
        )

    def ask_for_symptom(self) -> List[AgentMessage]:
        """
        Gibt Begrüßung und erste Frage nach einem beobachteten Verhalten zurück.
        """
        return [
            AgentMessage(sender=self.role, text=self.greeting_text),
            AgentMessage(sender=self.role, text="Was ist los? Beschreib mir bitte, was du beobachtet hast."),
        ]

    def check_symptom_in_weaviate(self, symptom: str) -> str:
        """
        Prüft über Weaviate, ob das beschriebene Symptom einem bekannten Hundeverhalten entspricht.
        Rückgabe: passender Beschreibungstext oder leerer String.
        """
        result = get_symptom_info(symptom)
        return result or ""

    def describe_symptom_as_dog(self, chunk: str, symptom: str) -> str:
        """
        Erstellt ein GPT-Prompt, das die Hundeperspektive auf das erkannte Verhalten beschreibt.
        Nutzt nur die Inhalte aus dem Retrieval-Ergebnis.
        """
        prompt = (
            f"Ich bin ein Hund und habe dieses Verhalten gezeigt:\n'{symptom}'\n\n"
            "Hier ist eine Beschreibung aus ähnlichen Situationen:\n"
            f"{chunk}\n\n"
            "Du bist ein Hund. Beschreibe ruhig und klar, wie du dieses Verhalten aus deiner Sicht erlebt hast. "
            "Sprich nicht über Menschen oder Trainingsmethoden. Nenne keine Instinkte beim Namen. Keine Fantasie. Keine Fachbegriffe."
        )
        return ask_gpt(prompt)

    def ask_if_diagnosis_wanted(self) -> AgentMessage:
        """
        Fragt den Menschen, ob er mehr über die Ursache (Diagnose) wissen möchte.
        """
        return AgentMessage(
            sender=self.role,
            text="Nochmal von vorne?"
        )

    async def respond(self, user_input: str, is_first_message: bool = False) -> List[AgentMessage]:
        """
        Verarbeitet eine Nutzereingabe. Falls Erstkontakt: fragt nach Symptom.
        Sonst: prüft Verhalten, beschreibt es aus Hundesicht und fragt nach Diagnoseinteresse.
        """
        messages = []

        # Prüfe, ob Nutzer "ja" antwortet auf "Nochmal von vorne?"
        if user_input.lower() == "ja" and getattr(self, 'last_bot_message', "") == "Nochmal von vorne?":
            return await self.start_conversation()

        # Wenn Diagnose bereits bestätigt wurde → nächste Phase (z. B. Detailfragen)
        state = sessions.get_or_create("debug")
        if state.diagnosis_confirmed:
            return [AgentMessage(
                sender=self.role,
                text="Danke, dass du mir vertraust. Was genau ist passiert? Wo warst du, wer war dabei, und wie war die Stimmung?"
            )]

        if is_first_message:
            # Einstieg: Begrüßung und erste Frage
            messages += self.ask_for_symptom()
            return messages

        # Symptomprüfung in Weaviate
        match = self.check_symptom_in_weaviate(user_input)
        if not match:
            # Kein bekanntes Verhalten gefunden
            messages.append(AgentMessage(
                sender=self.role,
                text="Hm, das klingt für mich nicht nach typischem Hundeverhalten. Magst du es nochmal anders beschreiben?"
            ))
            messages += self.ask_for_symptom()
            return messages

        # Beschreibung aus Hundeperspektive generieren
        dog_view = self.describe_symptom_as_dog(match, user_input)
        messages.append(AgentMessage(sender=self.role, text=dog_view))

        # Diagnose-Angebot
        diagnosis_message = self.ask_if_diagnosis_wanted()
        messages.append(diagnosis_message)

        # Session-State aktualisieren
        if state:
            state.awaiting_diagnosis_confirmation = True
            state.active_symptom = user_input

        # Speichere die letzte Bot-Nachricht für die Prüfung in der nächsten Runde
        self.last_bot_message = diagnosis_message.text

        return messages

    async def continue_flow(self, user_input: str) -> List[AgentMessage]:
        return await self.respond(user_input)

    async def start_conversation(self) -> List[AgentMessage]:
        """
        Startet die Konversation neu mit Begrüßung und erster Frage.
        """
        return self.ask_for_symptom()
