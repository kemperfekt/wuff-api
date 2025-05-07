from typing import List
from models.flow_models import AgentMessage
from agents.base_agent import BaseAgent


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
        Diese Version verwendet GPT, perspektivisch ergänzt durch Inhalte aus der 'Hundeperspektive'-Collection (RAG).
        """
        from services.gpt_service import ask_gpt

        prompt = (
            "Stell dir vor, du bist ein Hund und erlebst folgende Situation:\n"
            f"'{symptom_description}'\n\n"
            "Wie fühlt sich das aus Hundesicht an? Antworte emotional, mit instinktgeprägter Wahrnehmung – "
            "nicht analytisch. Du darfst auch auf Geräusche, Gerüche oder Körpersprache eingehen."
        )

        antwort = ask_gpt(prompt)
        return [AgentMessage(role=self.role, content=antwort)]
