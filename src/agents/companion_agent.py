import json
from datetime import datetime
from pathlib import Path
from src.models.flow_models import AgentMessage


class CompanionAgent:
    def __init__(self):
        self.role = "companion"
        self.feedback_questions = [
            "Wie hilfreich war die inhaltliche Beratung für Dich? (0–10)",
            "Wie authentisch fandest Du den Dialog mit einem Hund? (0–10)",
            "Wie wahrscheinlich ist es, dass Du Wuffchat weiterempfiehlst? (0–10)",
        ]

    def save_feedback(self, session_id: str, responses: list[str], messages: list[AgentMessage]):
        """Speichert die Antworten als JSON-Datei unter /data/feedback_{session_id}.json"""
        feedback_data = {
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "responses": [
                {"question": q, "answer": a}
                for q, a in zip(self.feedback_questions, responses)
            ],
            "messages": [msg.model_dump() for msg in messages],
        }
        Path("data").mkdir(exist_ok=True)
        with open(f"data/feedback_{session_id}.json", "w", encoding="utf-8") as f:
            json.dump(feedback_data, f, ensure_ascii=False, indent=2)

    def get_intro_messages(self) -> list[AgentMessage]:
        return [
            AgentMessage(sender=self.role, text="Ich würde mich freuen, wenn du mir noch ein kurzes Feedback gibst."),
            *[
                AgentMessage(sender=self.role, text=question)
                for question in self.feedback_questions
            ],
        ]
