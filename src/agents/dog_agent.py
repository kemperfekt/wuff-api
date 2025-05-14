from typing import List
import json
from src.models.flow_models import AgentMessage
from src.agents.base_agent import BaseAgent
from src.services.gpt_service import ask_gpt
from src.services.retrieval import get_symptom_info

INSTINKT_FRAGEN = {
    "jagd": [
        "Kommt es vor, dass ich plötzlich stehenbleibe und etwas in der Ferne fixiere, oder ausgiebig auf dem Boden schnüffle?"
    ],
    "territorial": [
        "Kommt das häufiger vor, wenn wir aus der Wohnung oder aus dem Haus gehen oder in der Nähe unseres Zuhause unterwegs sind?"
    ],
    "rudel": [
        "Stelle ich mich in solchen Situationen quer vor Dich oder schneide ich Dir beim Laufen den Weg ab?"
    ],
    "sexual": [
        "Falls ich ein Rüde bin: Bin ich vielleicht einer Hündin begegnet? Falls ich eine Hündin bin: War ich in der Zeit läufig?"
    ]
}


class DogAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Hund",
            role="dog",
            greeting_text="Wuff! Ich bin dein Hund. Bitte nenne mir ein Verhalten und ich schildere Dir, wie ich es erlebe.",
        )

    def react_to_symptom(self, symptom_description: str) -> List[AgentMessage]:
        """
        Reagiert instinktgeprägt und emotional auf das geschilderte Verhalten aus Hundesicht.
        Nutzt GPT + Weaviate (RAG) + ggf. Rückfrage zur Klärung.
        Rückgabe: emotionale Antwort + gezielte Nachfrage als 2 getrennte AgentMessages.
        """
        self.latest_symptom = symptom_description

        from src.services.retrieval import get_hundeperspektive

        perspektive_raw = get_hundeperspektive(symptom_description)

        retrieved_chunks = perspektive_raw.strip()
        if not retrieved_chunks:
            fallback = (
                "Vielen Dank für die Beschreibung. Leider kann ich zu dem Verhalten noch nichts sagen. "
            )
            return [AgentMessage(sender=self.role, text=fallback)]

        base_prompt = (
            f"Ich bin ein Hund und habe dieses Verhalten gezeigt:\n'{symptom_description}'\n\n"
        )

        base_prompt += (
            "Hier sind Erlebnisse von Hunden in ähnlichen Situationen:\n"
            f"{retrieved_chunks}\n\n"
            "Du bist ein Hund. Beschreibe in einfacher Sprache, wie du dieses Verhalten aus deiner Perspektive wahrnimmst – geleitet von deinen Instinkten. "
            "Vermeide Fachbegriffe, bleibe bei deinem Erleben als Hund. Nenne keine Instinkte beim Namen und sprich nicht über den Menschen. "
            "Formuliere ruhig und klar. Nutze nur das, was oben steht. Keine Fantasie.\n"
            "Beende deine Beschreibung mit einem Punkt, aber ohne weitere Fragen oder Kommentare."
        )

        # 3. GPT fragen
        antwort = ask_gpt(base_prompt)

        if not antwort:
            return [AgentMessage(sender=self.role, text="Da fällt mir gerade nichts ein...")]

        # 4. Rückgabe: Erlebnisbeschreibung + Diagnose-Angebot
        return [
            AgentMessage(sender=self.role, text=antwort.strip()),
            AgentMessage(sender=self.role, text="Willst du wissen, warum ich mich so verhalte?"),
        ]

    def continue_flow(self, answer: str) -> List[AgentMessage]:
        """
        GPT soll mit Hilfe der instinkt_varianten aus Weaviate erkennen, 
        aus welchem Instinkt das Verhalten stammt. Falls unklar, Rückfrage stellen.
        """
        symptom = self.latest_symptom
        symptom_info_raw = get_symptom_info(symptom)
        print("🧪 Weaviate-Rohantwort:\n", symptom_info_raw)

        if not symptom_info_raw or not symptom_info_raw.strip().startswith("{"):
            print("❌ Ungültige Weaviate-Rückgabe.")
            return [AgentMessage(sender=self.role, text="Ich konnte dazu nichts in meiner Erinnerung finden...")]

        symptom_info = json.loads(symptom_info_raw)

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
            "Wenn du dir sicher bist, gib eine Diagnose ab, z.B.:\n"
            "„Ich glaube, es ist mein Jagdinstinkt.“\n\n"
            "Wenn du noch unsicher bist, stelle eine Rückfrage – an dich selbst – um deinen eigenen Impuls besser zu verstehen.\n"
            "Sprich niemals über den Menschen. Bleibe in deiner Wahrnehmung.\n\n"
            "Formuliere nur eine Aussage: entweder eine Diagnose ODER eine Rückfrage. Gib nur einen Satz zurück."
        )

        antwort = ask_gpt(prompt).strip()

        if not antwort:
            return [AgentMessage(sender=self.role, text="Da kam nichts zurück, ich bin verwirrt...")]

        print("📥 GPT-Antwort:\n", antwort)

        print("🐾 DogAgent antwortet:")
        print(f"- {self.role}: {antwort}")

        if "?" in antwort and "warum" not in antwort.lower():
            # GPT hat eine Rückfrage gestellt – wir merken sie und geben sie direkt weiter
            return [AgentMessage(sender=self.role, text=antwort)]

        if "instinkt" in antwort.lower():
            # GPT hat eine Diagnose geliefert
            return [AgentMessage(sender=self.role, text=antwort)]

        # Fallback: keine klare Diagnose, keine Rückfrage – Rückfragenlogik starten
        instinct_order = ["jagd", "territorial", "rudel", "sexual"]
        active = self.latest_symptom
        from src.state.session_state import sessions  # temporär: Zugriff auf globales sessions-Dict
        state = sessions.get("debug")  # für MVP statisch, später dynamisch per Übergabe
        if not state:
            return [AgentMessage(sender=self.role, text="Ich konnte meinen inneren Spürsinn nicht abrufen...")]

        sym_state = state.symptoms.get(active)
        if not sym_state:
            return [AgentMessage(sender=self.role, text="Ich habe das Verhalten nicht wiedergefunden...")]

        for instinkt in instinct_order:
            if not sym_state.asked_instincts.get(instinkt):
                sym_state.asked_instincts[instinkt] = True
                return [AgentMessage(sender=self.role, text=f"Wenn du an mich denkst – trifft das hier manchmal zu: {instinkt.upper()}?")]

        return [AgentMessage(sender=self.role, text="Ich konnte keinen passenden Instinkt finden. Wollen wir nochmal von vorn anfangen?")]
