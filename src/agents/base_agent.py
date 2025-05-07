# src/agents/base_agent.py

from typing import Optional, List
from models.flow_models import AgentMessage
from services.retrieval import ask_with_context
from services.gpt_service import ask_gpt


class BaseAgent:
    def __init__(
        self,
        name: str,
        role: str,
        greeting_text: Optional[str] = None,
        question_text: Optional[str] = None,
    ):
        self.name = name
        self.role = role
        self.greeting_text = greeting_text
        self.question_text = question_text

    def respond(
        self,
        user_input: str,
        use_rag: bool = True,
        rag_class: str = "Symptom",
        is_first_message: bool = False,
    ) -> List[AgentMessage]:
        """
        Generiert eine Antwort auf eine Nutzereingabe – entweder mit oder ohne Kontext (RAG).
        Gibt eine Liste von AgentMessage-Objekten zurück.
        """

        messages = []

        # Optional: Begrüßung beim Erstkontakt
        if is_first_message and self.greeting_text:
            messages.append(AgentMessage(role=self.role, content=self.greeting_text))

        # Hauptantwort: GPT mit oder ohne RAG
        if use_rag:
            reply = ask_with_context(user_input, collection=rag_class)
        else:
            reply = ask_gpt(user_input)

        messages.append(AgentMessage(role=self.role, content=reply))

        # Optional: Abschlussfrage
        if self.question_text:
            messages.append(AgentMessage(role=self.role, content=self.question_text))

        return messages