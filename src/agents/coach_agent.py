

from typing import List
from models.flow_models import AgentMessage
from services.retrieval import ask_with_context
from services.gpt_service import ask_gpt
from agents.base_agent import BaseAgent
from services.weaviate_service import get_client


class CoachAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Coach",
            role="coach",
            greeting_text="Hallo, ich bin dein Coach. Ich helfe dir, das Verhalten deines Hundes zu verstehen.",
        )

    def generate_rueckfragen(self, symptom_name: str, instinktvarianten: dict) -> List[AgentMessage]:
        """
        Wählt je Instinkt eine gezielte Rückfrage aus den vorhandenen Varianten (via RAG).
        """
        client = get_client()
        symptom = client.collections.get("Symptom").query.fetch_object_by_id(symptom_name)
        if not symptom:
            return [AgentMessage(role=self.role, content="Ich konnte leider keine Informationen zum Symptom finden.")]

        rueckfragen = []
        for instinkt, varianten in instinktvarianten.items():
            if not varianten:
                continue

            # Prompt für GPT mit Auswahloptionen zur Formulierung einer passenden Rückfrage
            variantentext = "\n".join(f"- {v}" for v in varianten)
            prompt = (
                f"Ein Mensch beschreibt folgendes Symptom bei seinem Hund: '{symptom_name}'.\n"
                f"Hier sind mögliche Rückfragen zum Instinkt '{instinkt}':\n{variantentext}\n\n"
                f"Welche dieser Rückfragen ist am sinnvollsten, um das Verhalten besser zu verstehen? "
                f"Bitte gib genau eine davon als Klartext zurück."
            )

            selected = ask_gpt(prompt)
            rueckfragen.append(AgentMessage(role=self.role, content=selected))

        return rueckfragen