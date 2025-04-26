# -------------------------------
# DogBot Diagnose Server (FastAPI)
# -------------------------------

from fastapi import FastAPI
from pydantic import BaseModel
from agent_module import run_diagnose_agent, generate_final_diagnosis
from fastapi.middleware.cors import CORSMiddleware
import uuid

# FastAPI App-Instanz erstellen
app = FastAPI()

# CORS aktivieren
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-Memory Session Store
sessions = {}

# Request- und Response-Modelle
class SymptomRequest(BaseModel):
    symptom_input: str

class AnswerRequest(BaseModel):
    session_id: str
    answer: str

class DiagnoseResponse(BaseModel):
    session_id: str
    message: str
    done: bool = False

# ---------------------------------------
# POST /diagnose_start
# Startet eine neue Diagnose-Session
# ---------------------------------------
@app.post("/diagnose_start", response_model=DiagnoseResponse)
async def diagnose_start(symptom: SymptomRequest):
    session_id = str(uuid.uuid4())
    
    # Fragen über Agent erzeugen
    questions = run_diagnose_agent(symptom.symptom_input)

    # Session speichern
    sessions[session_id] = {
        "symptom": symptom.symptom_input,
        "questions": questions,
        "answers": []
    }

    # Erste Frage zurückgeben
    return DiagnoseResponse(session_id=session_id, message=questions[0], done=False)

# ---------------------------------------
# POST /diagnose_continue
# Antwort entgegennehmen und fortfahren
# ---------------------------------------
@app.post("/diagnose_continue", response_model=DiagnoseResponse)
async def diagnose_continue(answer: AnswerRequest):
    session = sessions.get(answer.session_id)
    if not session:
        return DiagnoseResponse(session_id=answer.session_id, message="Session nicht gefunden.", done=True)

    # Antwort speichern
    session["answers"].append(answer.answer)

    if len(session["answers"]) < len(session["questions"]):
        next_question = session["questions"][len(session["answers"])]
        return DiagnoseResponse(session_id=answer.session_id, message=next_question, done=False)
    else:
        # Diagnose erstellen
        final_diagnosis = generate_final_diagnosis(
            symptom=session["symptom"],
            answers=session["answers"]
        )
        del sessions[answer.session_id]
        return DiagnoseResponse(session_id=answer.session_id, message=final_diagnosis, done=True)
