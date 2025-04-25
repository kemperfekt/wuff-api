from fastapi import FastAPI
from pydantic import BaseModel
from agent_module import run_diagnose_agent
from fastapi.middleware.cors import CORSMiddleware

# FastAPI App erstellen
app = FastAPI()

# CORS aktivieren (damit dein Frontend localhost auf Backend localhost zugreifen darf)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Eingabemodell
class SymptomRequest(BaseModel):
    symptom_input: str

# Ausgabemodell
class DiagnoseResponse(BaseModel):
    result: str

# Diagnose-Route
@app.post("/diagnose", response_model=DiagnoseResponse)
async def diagnose(symptom: SymptomRequest):
    result = run_diagnose_agent(symptom.symptom_input)
    return DiagnoseResponse(result=result)

# Lokales Startkommando (wenn du die Datei direkt laufen lässt)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
