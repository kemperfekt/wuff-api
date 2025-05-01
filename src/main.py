# src/main.py

import os
import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from src.agents.flow_agent import run_full_flow

# Legacy-Alias für Tests – die Handler nutzen jetzt run_diagnose_agent
run_diagnose_agent = run_full_flow

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DiagnoseStartRequest(BaseModel):
    symptom_input: str

class DiagnoseStartResponse(BaseModel):
    session_id: str
    question: str | None = None
    message: str | None = None
    details: dict | None = None

@app.post("/diagnose_start", response_model=DiagnoseStartResponse)
def diagnose_start(req: DiagnoseStartRequest):
    sid = str(uuid.uuid4())
    # Nutze Alias
    result = run_diagnose_agent(sid, req.symptom_input)
    return {"session_id": sid, **result}

class DiagnoseRequest(BaseModel):
    session_id: str
    user_input: str

class DiagnoseResponse(BaseModel):
    question: str | None = None
    message: str | None = None
    details: dict | None = None

@app.post("/diagnose_continue", response_model=DiagnoseResponse)
def diagnose_continue(req: DiagnoseRequest):
    try:
        # Verwende Alias, nicht direkt run_full_flow
        result = run_diagnose_agent(req.session_id, req.user_input)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True)
