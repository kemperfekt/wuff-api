from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.flow_endpoints import router as flow_router

app = FastAPI()

# Lokales Testing mit Frontend (localhost:3000 ↔ 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # oder z. B. ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API-Router einbinden
app.include_router(flow_router)
