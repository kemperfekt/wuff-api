from typing import List
from src.models.flow_models import AgentMessage
from src.agents.base_agent import BaseAgent
from src.services.gpt_service import ask_gpt
from src.services.retrieval import get_symptom_info


class DogAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Hund",
            role="dog",
            greeting_text="Wuff! Ich bin dein Hund. Ich erzähle dir, wie sich die Situation für mich angefühlt hat.",
        )

    def react_to_symptom(self, symptom_description: str) -> List[AgentMessage]:
        """
        Reagiert instinktgeprägt und emotional auf das geschilderte Verhalten aus Hundesicht.
        Nutzt GPT + Weaviate (RAG) + ggf. Rückfrage zur Klärung.
        Rückgabe: emotionale Antwort + gezielte Nachfrage als 2 getrennte AgentMessages.
        """

        # 1. Symptomkontext aus Weaviate holen
        symptom_info = get_symptom_info(symptom_description)

        # 2. Prompt vorbereiten
        base_prompt = (
            "Stell dir vor, du bist ein Hund und erlebst folgende Situation:\n"
            f"'{symptom_description}'\n\n"
        )

        # a) Falls relevante Inhalte in RAG
        if symptom_info:
            base_prompt += (
                "Diese Informationen helfen dir beim Einordnen:\n"
                f"{symptom_info}\n\n"
            )

        # b) Hauptfrage
        base_prompt += (
            "Wie fühlt sich das aus Hundesicht an? Antworte emotional und instinktgeprägt – "
            "nicht analytisch. Du darfst auf Geräusche, Gerüche oder Körpersprache eingehen. "
            "Wenn du unsicher bist, stell am Ende eine kurze Nachfrage, die dir hilft, die Situation besser zu verstehen."
        )

        # 3. GPT fragen
        antwort = ask_gpt(base_prompt)

        # 4. Optional: Trennen von Aussage + Rückfrage
        # GPT soll die Rückfrage mit einem Trennzeichen markieren: "---"
        if "---" in antwort:
            hauptteil, rückfrage = antwort.split("---", 1)
            return [
                AgentMessage(role=self.role, content=hauptteil.strip()),
                AgentMessage(role=self.role, content=rückfrage.strip()),
            ]
        else:
            return [AgentMessage(role=self.role, content=antwort.strip())]
