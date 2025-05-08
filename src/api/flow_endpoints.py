from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from orchestrator.flow_orchestrator import handle_symptom
from state.session_state import SessionState
from models.flow_models import AgentMessage

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
    greeting = AgentMessage(role="dog", content="🐾 Hallo Mensch! Ich bin dein Hund. Erzähl mir einfach, was dich gerade beschäftigt.")
    return FlowIntroResponse(session_id=session_id, messages=[greeting])


@router.post("/flow_start", response_model=FlowResponse)
def flow_start(request: FlowStartRequest):
    session_id = request.session_id or "sess_" + str(len(sessions) + 1)
    state = sessions.setdefault(session_id, SessionState())

    # 🧠 Dummy-Instinktvarianten (später dynamisch aus Weaviate)
    instinktvarianten = {
        "jagd": ["Fixiert dein Hund etwas in der Ferne?", "Zieht er los, wenn er eine Spur wittert?"],
        "rudel": ["Ist er besonders unruhig, wenn ihr getrennt seid?", "Läuft er gezielt zu bestimmten Menschen hin?"],
        "territorial": ["Reagiert er an bestimmten Orten besonders stark?", "Wirkt er wie ein 'Wächter'?"],
        "sexual": ["Ist er dabei angespannt gegenüber Hündinnen oder Rüden?", "Markiert er auffällig oft?"]
    }

    try:
        messages = handle_symptom(request.symptom, instinktvarianten, state)
        return FlowResponse(session_id=session_id, messages=messages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/flow_continue", response_model=FlowResponse)
def flow_continue(request: FlowContinueRequest):
    state = sessions.get(request.session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    # Antwort an CoachAgent weitergeben – aktuell noch nicht implementiert
    messages = [
        AgentMessage(role="coach", content="Danke! Ich habe deine Antwort notiert. 🧠 Mehr Fragen folgen bald.")
    ]

    return FlowResponse(session_id=request.session_id, messages=messages, done=False)
