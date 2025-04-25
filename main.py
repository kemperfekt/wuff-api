# -------------------------------
# DogBot Diagnose Server (FastAPI)
# -------------------------------
# Aufgabe: Verwaltung von Diagnose-Sessions über Web-API
# (1) Symptom empfangen → Rückfragen generieren
# (2) Antworten empfangen → Diagnose erstellen

from fastapi import FastAPI
from pydantic import BaseModel
from agent_module import run_diagnose_agent, generate_followup_questions, generate_final_diagnosis
from fastapi.middleware.cors import CORSMiddleware
import uuid

# FastAPI App-Instanz erstellen
app = FastAPI()

# CORS aktivieren (erlaubt Anfragen von beliebigen Frontends z.B. localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-Memory Session Store (nur für Prototyping, nicht persistent)
sessions = {}

# Datentyp für Symptom-Start-Anfrage
class SymptomRequest(BaseModel):
    symptom_input: str

# Datentyp für Antwort auf Rückfrage
class AnswerRequest(BaseModel):
    session_id: str
    answer: str

# Standard-Response-Format
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
    # Neue Session-ID erzeugen
    session_id = str(uuid.uuid4())
    
    # GPT fragt passende Rückfragen an
    questions = generate_followup_questions(symptom.symptom_input)

    # Session initialisieren und speichern
    sessions[session_id] = {
        "symptom": symptom.symptom_input,
        "questions": questions,
        "answers": []
    }

    # Erste Rückfrage zurücksenden
    return DiagnoseResponse(session_id=session_id, message=questions[0], done=False)

# ---------------------------------------
# POST /diagnose_continue
# Nimmt eine Antwort entgegen und gibt
# nächste Rückfrage oder Diagnose zurück
# ---------------------------------------
@app.post("/diagnose_continue", response_model=DiagnoseResponse)
async def diagnose_continue(answer: AnswerRequest):
    session = sessions.get(answer.session_id)
    if not session:
        # Fehler: Session nicht gefunden
        return DiagnoseResponse(session_id=answer.session_id, message="Session nicht gefunden.", done=True)

    # Antwort speichern
    session["answers"].append(answer.answer)

    # Gibt es noch weitere Rückfragen?
    if len(session["answers"]) < len(session["questions"]):
        next_question = session["questions"][len(session["answers"])]
        return DiagnoseResponse(session_id=answer.session_id, message=next_question, done=False)
    else:
        # Alle Rückfragen beantwortet → Diagnose erstellen
        final_diagnosis = generate_final_diagnosis(
            symptom=session["symptom"],
            questions=session["questions"],
            answers=session["answers"]
        )
        # Session löschen (optional)
        del sessions[answer.session_id]
        return DiagnoseResponse(session_id=answer.session_id, message=final_diagnosis, done=True)

# ---------------------------------------
# Hinweis: generate_followup_questions
# und generate_final_diagnosis befinden
# sich in agent_module.py
# ---------------------------------------
