# src/main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.state.session_state import SessionStore
from src.flow.flow_orchestrator import handle_message, init_orchestrator
from src.models.flow_models import AgentMessage
from src.models.flow_models import FlowStep
from src.core.config import setup_logging, logger

app = FastAPI()

# Logger einrichten
logger = setup_logging()

# CORS-Block für Frontend-Zugriff
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.wuffchat.de",
        "https://api.wuffchat.de",
        "https://dogbot-agent.osc-fr1.scalingo.io",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SessionStore als globaler Speicher
session_store = SessionStore()

# Orchestrator initialisieren
init_orchestrator(session_store)

class IntroResponse(BaseModel):
    session_id: str
    messages: list

class MessageRequest(BaseModel):
    session_id: str
    message: str

@app.get("/")
def read_root():
    logger.info(">>> HEALTHCHECK SUCCESS")
    return {"status": "ok"}

@app.post("/flow_intro", response_model=IntroResponse)
async def flow_intro():
    session = session_store.create_session()
    session.current_step = FlowStep.GREETING
    messages = await handle_message(session.session_id, "")
    
    # Debug-Ausgabe
    logger.info(f"Neue Session erstellt: ID={session.session_id}, Step={session.current_step}")
    logger.debug(f"Intro-Nachrichten: {[msg.sender + ': ' + msg.text for msg in messages]}")
    
    return {"session_id": session.session_id, "messages": [msg.model_dump() for msg in messages]}

@app.post("/flow_step")
async def flow_step(req: MessageRequest):
    # Verify valid session_id
    session = session_store.get_or_create(req.session_id)
    if not session:
        logger.warning(f"Session nicht gefunden: {req.session_id}")
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Debug-Ausgabe vor der Verarbeitung
    logger.info(f"Verarbeite Nachricht - Session ID: {session.session_id}, Step: {session.current_step}")
    logger.debug(f"Benutzer-Nachricht: {req.message}")
    
    messages = await handle_message(req.session_id, req.message)
    
    # Debug-Ausgabe nach der Verarbeitung
    session = session_store.get_or_create(req.session_id)  # Session neu holen
    logger.info(f"Nachricht verarbeitet - Session ID: {session.session_id}, neuer Step: {session.current_step}")
    logger.debug(f"Antwort-Nachrichten: {[msg.sender + ': ' + msg.text for msg in messages]}")
    
    return {
        "session_id": session.session_id,
        "messages": [msg.model_dump() for msg in messages]
    }

# Füge einen Startblock hinzu, wenn das Skript direkt ausgeführt wird
if __name__ == "__main__":
    import uvicorn
    logger.info("Server startet...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
