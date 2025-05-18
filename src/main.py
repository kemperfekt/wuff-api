# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.state.session_state import SessionStore
from src.orchestrator.flow_orchestrator import handle_message
from src.models.flow_models import AgentMessage
from src.models.flow_models import FlowStep

app = FastAPI()

# CORS-Block für Frontend-Zugriff
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.wuffchat.de"],  # später ggf. Frontend-Domain einschränken
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SessionStore als globaler Speicher
session_store = SessionStore()

class IntroResponse(BaseModel):
    session_id: str
    messages: list

class MessageRequest(BaseModel):
    session_id: str
    message: str

@app.get("/")
def read_root():
    return {"status": "ok"}

@app.post("/flow_intro")
async def flow_intro():
    session = session_store.create_session()
    session.current_step = FlowStep.GREETING
    messages = handle_message("start", session)
    return {"session_id": session.session_id, "messages": [msg.model_dump() for msg in messages]}

@app.post("/flow_step")
async def flow_step(req: MessageRequest):
    session = session_store.get_or_create(req.session_id)
    messages = handle_message(req.message, session)
    return {
        "session_id": session.session_id,
        "messages": [msg.model_dump() for msg in messages]
    }
