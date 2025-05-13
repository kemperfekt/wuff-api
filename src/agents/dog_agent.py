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
            "Wenn du dein Verhalten noch nicht verstehst, stelle eine Rückfrage, um dir selbst auf die Spur zu kommen. "
            "Sprich nur über dein eigenes Verhalten – nicht über das Verhalten des Menschen. "
            "Trenne deine Erlebnisbeschreibung und die Rückfrage strikt mit drei Bindestrichen auf einer eigenen Zeile: ---"
        )

        # 3. GPT fragen
        antwort = ask_gpt(base_prompt)

        # 4. Optional: Trennen von Aussage + Rückfrage
        # GPT soll die Rückfrage mit einem Trennzeichen markieren: "---"
        if "---" in antwort:
            hauptteil, rückfrage = antwort.split("---", 1)
            return [
                AgentMessage(sender=self.role, text=hauptteil.strip()),
                AgentMessage(sender=self.role, text=rückfrage.strip()),
            ]
        else:
            return [AgentMessage(sender=self.role, text=antwort.strip())]

    def continue_flow(self, answer: str) -> List[AgentMessage]:
        """
        GPT soll mit Hilfe der instinkt_varianten aus Weaviate erkennen, 
        aus welchem Instinkt das Verhalten stammt. Falls unklar, Rückfrage stellen.
        """
        symptom = self.latest_symptom
        symptom_info = get_symptom_info(symptom)

        if not symptom_info or not symptom_info.get("instinkt_varianten"):
            print("❌ Keine instinkt_varianten gefunden.")
            return [AgentMessage(sender=self.role, text="Da fehlen mir gerade wichtige Informationen...")]

        varianten = symptom_info["instinkt_varianten"]
        variantentext = (
            f"Jagd: {varianten['jagd']}\n"
            f"Territorial: {varianten['territorial']}\n"
            f"Rudel: {varianten['rudel']}\n"
            f"Sexual: {varianten['sexual']}"
        )

        prompt = (
            f"Der Mensch hat mir das hier gesagt:\n'{answer}'\n\n"
            "Ich bin ein Hund und versuche herauszufinden, aus welchem Instinkt mein Verhalten stammt.\n\n"
            f"Hier sind vier mögliche Instinktvarianten für mein Verhalten:\n\n{variantentext}\n\n"
            "Dein Ziel: Entscheide, ob du aus diesen Varianten schon erkennst, welcher Instinkt bei dir eine Rolle spielt.\n"
            "Wenn du dir sicher bist, gib eine Diagnose ab, z. B.:\n"
            "„Ich glaube, es ist mein Jagdinstinkt.“\n\n"
            "Wenn du noch unsicher bist, stelle eine Rückfrage – an dich selbst – um deinen eigenen Impuls besser zu verstehen.\n"
            "Sprich niemals über den Menschen. Bleibe in deiner Wahrnehmung.\n\n"
            "Trenne Diagnose und Rückfrage strikt mit '---'."
        )

        antwort = ask_gpt(prompt).strip()
        print("📥 GPT-Antwort:\n", antwort)

        teile = [t.strip() for t in antwort.split("---") if t.strip()]
        messages = [AgentMessage(sender=self.role, text=teil) for teil in teile if teil]
        print("🐾 DogAgent antwortet mit folgenden Messages:")
        for m in messages:
            print(f"- {m.sender}: {m.text}")
        return messages
