from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from src.agents.dog_agent import DogAgent
from src.state.session_state import SessionState
from src.models.flow_models import AgentMessage

router = APIRouter()

# Globale Sitzung (MVP-Version)
sessions: dict[str, SessionState] = {}


class FlowIntroResponse(BaseModel):
    session_id: str
    messages: List[AgentMessage]


class FlowStartRequest(BaseModel):
    symptom: str
    session_id: Optional[str] = None


class FlowContinueRequest(BaseModel):
    answer: str
    session_id: str


class FlowResponse(BaseModel):
    session_id: str
    messages: List[AgentMessage]
    done: Optional[bool] = False


@router.post("/flow_intro", response_model=FlowIntroResponse)
def flow_intro():
    session_id = "sess_" + str(len(sessions) + 1)
    sessions[session_id] = SessionState()

    # Begrüßung vom Hund – initiale Einführung
    greeting = AgentMessage(
        role="dog",
        content="🐾 Hallo Mensch! Ich bin dein Hund. Erzähl mir einfach, was dich gerade beschäftigt."
    )
    return FlowIntroResponse(session_id=session_id, messages=[greeting])


@router.post("/flow_start", response_model=FlowResponse)
def flow_start(request: FlowStartRequest):
    session_id = request.session_id or "sess_" + str(len(sessions) + 1)
    state = sessions.setdefault(session_id, SessionState())

    try:
        agent = DogAgent()
        messages = agent.react_to_symptom(request.symptom)
        return FlowResponse(session_id=session_id, messages=messages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/flow_continue", response_model=FlowResponse)
def flow_continue(request: FlowContinueRequest):
    state = sessions.get(request.session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    print(f"📨 Eingegangene Antwort von Mensch: {request.answer}")
    print(f"📨 Session-ID: {request.session_id}")

    try:
        agent = DogAgent()
        messages = agent.continue_flow(request.answer)

        print("✅ GPT hat folgende Nachrichten zurückgegeben:")
        for m in messages:
            print(f"- {m.sender}: {m.text}")

        return FlowResponse(session_id=request.session_id, messages=messages, done=False)
    except Exception as e:
        print("❌ Fehler beim Verarbeiten der Folgeantwort:", e)
        raise HTTPException(status_code=500, detail=str(e))