# src/main.py

import logging
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.models.flow_models import DiagnoseStart, DiagnoseContinue
from src.agents.diagnose_agent import run_diagnose_agent, generate_final_diagnosis

# --- Logging Setup ---
logger = logging.getLogger("uvicorn.error")

# --- FastAPI App ---
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-Memory Session Store: session_id -> history
sessions = {}

@app.get("/", tags=["Health"])
def health_check():
    logger.debug("Health check requested")
    return {"status": "ok"}

@app.post("/diagnose_start", tags=["Diagnosis"])
def diagnose_start(body: DiagnoseStart):
    logger.debug(f"Received diagnose_start with symptom_input='{body.symptom_input}'")
    try:
        session_id = str(uuid.uuid4())
        sessions[session_id] = []

        questions = run_diagnose_agent(body.symptom_input)
        question = questions[0] if questions else "Leider konnte keine Frage generiert werden."
        sessions[session_id].append({"role": "assistant", "content": question})
        logger.debug(f"Session {session_id} started, first question: {question}")

        return {
            "session_id": session_id,
            "message": question,
            "done": False
        }
    except Exception as e:
        logger.error(f"Error in diagnose_start: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/diagnose_continue", tags=["Diagnosis"])
def diagnose_continue(body: DiagnoseContinue):
    logger.debug(f"Received diagnose_continue for session_id='{body.session_id}' with message='{body.message}'")
    history = sessions.get(body.session_id)
    if history is None:
        logger.warning(f"Session {body.session_id} not found")
        raise HTTPException(status_code=404, detail="Session not found")

    history.append({"role": "user", "content": body.message})
    try:
        last_msg = history[-1]["content"]
        questions = run_diagnose_agent(last_msg)
        message = questions[0] if questions else "Keine weitere Frage verfügbar."
        done = False

        sessions[body.session_id].append({"role": "assistant", "content": message})
        logger.debug(f"Session {body.session_id} responded with: {message}")

        return {
            "message": message,
            "done": done
        }
    except Exception as e:
        logger.error(f"Error in diagnose_continue: {e}")
        raise HTTPException(status_code=500, detail=str(e))
