# src/services/state.py

from typing import Any, Dict, List

class State:
    def __init__(self):
        self.history: List[Dict[str, Any]] = []
        self.known_facts: Dict[str, Any] = {}

    def add_message(self, role: str, content: Any) -> None:
        self.history.append({"role": role, "content": content})

def load_state(session_id: str) -> State:
    """
    Lädt den Session-State (hier: Dummy-Implementierung).
    Später kannst du hier z.B. aus Redis oder einer DB laden.
    """
    return State()

def save_state(session_id: str, state: State) -> None:
    """
    Speichert den Session-State.
    Aktuell No-Op, später z.B. Redis/DB persistieren.
    """
    pass
