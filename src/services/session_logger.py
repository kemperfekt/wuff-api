import os
import json
from pathlib import Path
from typing import List
from src.models.flow_models import AgentMessage
from src.state.session_state import SessionState

def save_feedback_session(state: SessionState, messages: List[AgentMessage]):
    session_id = state.session_id
    save_dir = Path(os.getenv("SESSION_LOG_PATH", "data/sessions"))
    save_dir.mkdir(parents=True, exist_ok=True)
    path = save_dir / f"{session_id}.json"

    data = {
        "session_id": session_id,
        "symptom": state.active_symptom,
        "feedback": state.feedback,
        "messages": [m.model_dump() for m in messages],
    }

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[SessionLogger] Fehler beim Speichern von {path}: {e}")