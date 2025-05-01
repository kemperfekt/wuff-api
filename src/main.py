# src/main.py

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.agents.diagnose_agent import run_diagnose_agent

app = FastAPI()

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
        # Hier wird run_diagnose_agent mit beiden Parametern aufgerufen
        result = run_diagnose_agent(req.session_id, req.user_input)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True)
