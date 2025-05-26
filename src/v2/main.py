# src/v2/main.py
"""
V2 FastAPI Application - Drop-in replacement for V1 main.py

This provides the exact same API as V1 but uses the V2 flow engine internally.
Frontend compatibility is maintained through the same endpoints and response formats.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import logging

# V2 imports - the key difference from V1
from src.state.session_state import SessionStore
from src.v2.core.orchestrator import V2Orchestrator, init_orchestrator
from src.models.flow_models import FlowStep
from src.core.config import setup_logging

# Initialize FastAPI app
app = FastAPI(
    title="WuffChat V2 API",
    description="V2 implementation with FSM-based flow engine",
    version="2.0.0"
)

# Setup logging
logger = setup_logging()

# CORS configuration - same as V1 for compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.wuffchat.de",
        "https://api.wuffchat.de",
        "https://dogbot-agent.osc-fr1.scalingo.io",
        "https://dogbot-ui.osc-fr1.scalingo.io",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global session store - shared with V1
session_store = SessionStore()

# Initialize V2 orchestrator
orchestrator = init_orchestrator(session_store)

# API Models - same as V1 for compatibility
class IntroResponse(BaseModel):
    session_id: str
    messages: List[Dict[str, Any]]  # Changed to Dict to match V2 format

class MessageRequest(BaseModel):
    session_id: str
    message: str


@app.get("/")
def read_root():
    """Health check endpoint"""
    logger.info(">>> V2 HEALTHCHECK SUCCESS")
    return {"status": "ok", "version": "2.0.0"}


@app.post("/flow_intro", response_model=IntroResponse)
async def flow_intro():
    """
    Start a new conversation - V2 implementation.
    
    Creates a new session and returns initial greeting messages.
    Response format is identical to V1 for frontend compatibility.
    """
    try:
        # Create new session
        session = session_store.create_session()
        session.current_step = FlowStep.GREETING
        
        logger.info(f"[V2] Neue Session erstellt: ID={session.session_id}, Step={session.current_step}")
        
        # Start conversation using V2 orchestrator
        messages = await orchestrator.start_conversation(session.session_id)
        
        # Debug output
        logger.debug(f"[V2] Intro-Nachrichten: {len(messages)} messages generated")
        for msg in messages:
            logger.debug(f"  - {msg['sender']}: {msg['text'][:50]}...")
        
        # Return V1-compatible response
        return {
            "session_id": session.session_id,
            "messages": messages  # Already in correct format from V2
        }
        
    except Exception as e:
        logger.error(f"[V2] Error in flow_intro: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Starten der Konversation: {str(e)}"
        )


@app.post("/flow_step")
async def flow_step(req: MessageRequest):
    """
    Process a conversation step - V2 implementation.
    
    Handles user messages and returns bot responses.
    Response format is identical to V1 for frontend compatibility.
    """
    try:
        # Verify session exists
        session = session_store.get_or_create(req.session_id)
        if not session:
            logger.warning(f"[V2] Session nicht gefunden: {req.session_id}")
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Debug output before processing
        logger.info(f"[V2] Verarbeite Nachricht - Session ID: {session.session_id}, Step: {session.current_step}")
        logger.debug(f"[V2] Benutzer-Nachricht: {req.message}")
        
        # Process message using V2 orchestrator
        messages = await orchestrator.handle_message(req.session_id, req.message)
        
        # Get updated session state
        session = session_store.get_or_create(req.session_id)
        
        # Debug output after processing
        logger.info(f"[V2] Nachricht verarbeitet - Session ID: {session.session_id}, neuer Step: {session.current_step}")
        logger.debug(f"[V2] Antwort-Nachrichten: {len(messages)} messages")
        for msg in messages:
            logger.debug(f"  - {msg['sender']}: {msg['text'][:50]}...")
        
        # Return V1-compatible response
        return {
            "session_id": session.session_id,
            "messages": messages  # Already in correct format from V2
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"[V2] Error in flow_step: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Fehler bei der Nachrichtenverarbeitung: {str(e)}"
        )


# Additional V2-specific endpoints for debugging and monitoring
@app.get("/v2/health")
async def v2_health_check():
    """
    V2-specific health check with detailed status.
    
    This endpoint is new in V2 and provides detailed health information.
    """
    try:
        health = await orchestrator.health_check()
        return health
    except Exception as e:
        logger.error(f"[V2] Health check failed: {e}")
        return {
            "overall": "unhealthy",
            "error": str(e)
        }


@app.get("/v2/session/{session_id}")
async def get_session_info(session_id: str):
    """
    Get information about a specific session.
    
    This endpoint is new in V2 for debugging purposes.
    """
    try:
        info = orchestrator.get_session_info(session_id)
        return info
    except Exception as e:
        logger.error(f"[V2] Error getting session info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Abrufen der Session-Informationen: {str(e)}"
        )


@app.get("/v2/debug/flow")
async def get_flow_debug_info():
    """
    Get debug information about the flow engine.
    
    This endpoint is new in V2 for debugging the FSM.
    """
    try:
        debug_info = orchestrator.get_flow_debug_info()
        return debug_info
    except Exception as e:
        logger.error(f"[V2] Error getting flow debug info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Abrufen der Flow-Debug-Informationen: {str(e)}"
        )


# Startup event for initialization
@app.on_event("startup")
async def startup_event():
    """Initialize V2 services on startup"""
    logger.info("=" * 60)
    logger.info("🚀 WuffChat V2 API Starting...")
    logger.info("=" * 60)
    
    # Log configuration
    logger.info("📋 Configuration:")
    logger.info(f"  - Session Store: {len(session_store.sessions)} active sessions")
    logger.info(f"  - V2 Orchestrator: Initialized")
    
    # Perform health check
    try:
        health = await orchestrator.health_check()
        logger.info(f"  - Overall Health: {health['overall']}")
        logger.info(f"  - Flow Engine: {health['flow_engine']}")
        
        if 'services' in health:
            for service, status in health['services'].items():
                logger.info(f"  - {service.title()} Service: {status}")
    except Exception as e:
        logger.warning(f"⚠️  Startup health check failed: {e}")
    
    logger.info("=" * 60)
    logger.info("✅ V2 API Ready!")
    logger.info("=" * 60)


# Shutdown event for cleanup
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 WuffChat V2 API Shutting down...")
    # Add any cleanup code here if needed
    logger.info("👋 Goodbye!")


# Main entry point
if __name__ == "__main__":
    import uvicorn
    
    # Use different port than V1 for parallel testing
    port = 8001  # V1 uses 8000, V2 uses 8001
    
    logger.info(f"🚀 Starting V2 server on port {port}...")
    logger.info("=" * 60)
    logger.info("V2 API Endpoints:")
    logger.info("  - POST /flow_intro - Start new conversation")
    logger.info("  - POST /flow_step - Process message")
    logger.info("  - GET / - Health check")
    logger.info("  - GET /v2/health - Detailed health status")
    logger.info("  - GET /v2/session/{id} - Session info")
    logger.info("  - GET /v2/debug/flow - FSM debug info")
    logger.info("=" * 60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )