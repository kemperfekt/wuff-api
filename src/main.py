# main.py

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from orchestrator.flow_orchestrator import handle_symptom
from state.session_state import SessionStore
from state.session_state import SessionState

app = FastAPI()

# CORS, damit das Frontend zugreifen kann
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # später ggf. Frontend-Domain einschränken
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SessionStore als globaler Speicher
session_store = SessionStore()

# Dummy-Fragen – später dynamisch ersetzen
DUMMY_INSTINKTVARIANTEN = {
    "jagd": ["Fixiert dein Hund etwas in der Ferne?", "Zieht er los, wenn er eine Spur wittert?"],
    "rudel": ["Ist er besonders unruhig, wenn ihr getrennt seid?", "Läuft er gezielt zu bestimmten Menschen hin?"],
    "territorial": ["Reagiert er an bestimmten Orten besonders stark?", "Wirkt er wie ein 'Wächter'?"],
    "sexual": ["Ist er dabei angespannt gegenüber Hündinnen oder Rüden?", "Markiert er auffällig oft?"]
}

class IntroResponse(BaseModel):
    session_id: str
    messages: list

class StartRequest(BaseModel):
    session_id: str
    symptom: str

class ContinueRequest(BaseModel):
    session_id: str
    answer: str


@app.post("/flow_intro")
async def flow_intro():
    session = session_store.create_session()
    messages = [{
        "role": "system",
        "content": "Hallo! Was möchtest du über deinen Hund herausfinden?"
    }]
    return {"session_id": session.session_id, "messages": messages}


@app.post("/flow_start")
async def flow_start(req: StartRequest):
    session = session_store.get_or_create(req.session_id)
    result = handle_symptom(req.symptom, DUMMY_INSTINKTVARIANTEN, session)
    return {"session_id": session.session_id, "messages": [msg.dict() for msg in result], "done": False}


@app.post("/flow_continue")
async def flow_continue(req: ContinueRequest):
    # MVP: einfach Antwort anhängen – später mit echter FSM-Weiterverarbeitung
    session = session_store.get_or_create(req.session_id)
    return {
        "session_id": session.session_id,
        "messages": [{
            "role": "system",
            "content": f"Danke für deine Antwort: '{req.answer}'. Mehr Logik folgt bald!"
        }],
        "done": True
    }
