# src/v2/main.py
"""
V2 FastAPI Application - Drop-in replacement for V1 main.py

This provides the exact same API as V1 but uses the V2 flow engine internally.
Frontend compatibility is maintained through the same endpoints and response formats.
"""

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi.security import APIKeyHeader
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
import logging
from datetime import datetime
import os
import secrets

# V2 imports - the key difference from V1
from src.core.orchestrator import V2Orchestrator, init_orchestrator
from src.models.session_state import SessionStore
from src.models.flow_models import FlowStep
from src.core.logging_config import setup_logging
from src.core.rate_limit_config import get_real_ip, RATE_LIMIT_TIERS

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan event handler for startup/shutdown"""
    global orchestrator
    
    # Startup
    logger.info("=" * 60)
    logger.info("🚀 WuffChat V2 API Starting...")
    logger.info("=" * 60)
    
    # Validate environment variables (warn but don't fail)
    from src.core.config import validate_required_settings
    env_valid = validate_required_settings()
    if not env_valid:
        logger.warning("⚠️ Some environment variables are missing - services may fail on first use")
    
    # Initialize orchestrator with lazy loading to avoid blocking health checks
    try:
        orchestrator = init_orchestrator(session_store)
        
        # Log configuration
        logger.info("📋 Configuration:")
        logger.info(f"  - Session Store: {len(session_store.sessions)} active sessions")
        logger.info(f"  - V2 Orchestrator: Initialized (services lazy-loaded)")
        logger.info("  - Services: Will initialize on first use")
        
        logger.info("=" * 60)
        logger.info("✅ V2 API Ready!")
        logger.info("=" * 60)
        
        # Log startup completion
        import os
        port = os.getenv("PORT", "8000")
        logger.info(f"🌐 Server listening on port {port}")
        logger.info("💚 Health check available at GET /")
        logger.info("🔍 Monitoring for Scalingo health checks...")
        
        # Log Scalingo-specific environment
        if os.getenv("SCALINGO_APP"):
            logger.info(f"📦 Running on Scalingo: {os.getenv('SCALINGO_APP')}")
            logger.info(f"🔧 Container: {os.getenv('CONTAINER', 'unknown')}")
            logger.info(f"🏷️ Region: {os.getenv('SCALINGO_REGION', 'unknown')}")
        
        # Force immediate log flush
        for handler in logger.handlers:
            handler.flush()
        
        # Create a simple background task to log periodically
        import asyncio
        
        async def heartbeat():
            """Log heartbeat to show app is running"""
            count = 0
            instance_id = os.getenv("HOSTNAME", "unknown")[:8]
            while True:
                await asyncio.sleep(5)
                count += 1
                logger.info(f"💓 Heartbeat {count} - Instance {instance_id} running on port {port}")
        
        # Start heartbeat task
        asyncio.create_task(heartbeat())
        
        # Log that we're ready for connections
        logger.info("🟢 Server is ready to accept connections")
        logger.info("🔗 Listening on all interfaces (0.0.0.0)")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize V2 orchestrator: {e}")
        logger.error("🔥 Startup failed - check environment variables and dependencies")
        raise  # Re-raise to fail startup
    
    yield
    
    # Shutdown
    logger.info("🛑 WuffChat V2 API Shutting down...")
    logger.info("👋 Goodbye!")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="WuffChat V2 API",
    description="V2 implementation with FSM-based flow engine",
    version="2.0.0",
    lifespan=lifespan,
    docs_url=None,  # Disable docs to reduce overhead
    redoc_url=None  # Disable redoc to reduce overhead
)

# Setup logging
logger = setup_logging()

# =============================================================================
# API KEY AUTHENTICATION
# =============================================================================

# API Key Configuration
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def get_api_key():
    """Get API key from environment or generate one for development"""
    api_key = os.getenv("WUFFCHAT_API_KEY")
    if not api_key:
        # Generate a secure key for development
        api_key = secrets.token_urlsafe(32)
        logger.warning(f"⚠️ No WUFFCHAT_API_KEY set. Generated temporary key: {api_key}")
        logger.warning("⚠️ Set WUFFCHAT_API_KEY environment variable for production!")
        logger.warning("⚠️ Add this key to your frontend .env file as well!")
    else:
        logger.info("✅ API Key configured from environment")
    return api_key

# Initialize API key
VALID_API_KEY = get_api_key()

# List of endpoints that don't require authentication
PUBLIC_ENDPOINTS = {
    "/", "/health", "/healthz", "/_health", "/ping", "/ready", "/alive",
    "/docs", "/redoc", "/openapi.json"
}

async def verify_api_key(api_key: Optional[str] = Depends(api_key_header)):
    """Verify API key for protected endpoints"""
    if api_key is None:
        logger.warning("❌ Request without API key")
        raise HTTPException(
            status_code=401,
            detail="Missing API Key. Include 'X-API-Key' header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    if api_key != VALID_API_KEY:
        logger.warning(f"❌ Invalid API key attempt: {api_key[:8]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid API Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return api_key

# =============================================================================
# RATE LIMITING
# =============================================================================

# Create limiter instance with custom IP extraction
limiter = Limiter(key_func=get_real_ip)

# Add rate limit exceeded handler with custom message
def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom rate limit response with helpful message"""
    response = PlainTextResponse(
        content="Zu viele Anfragen. Bitte warte einen Moment und versuche es erneut.",
        status_code=429,
    )
    response.headers["Retry-After"] = "60"
    response.headers["X-RateLimit-Limit"] = str(getattr(exc, "limit", "N/A"))
    response.headers["X-RateLimit-Reset"] = str(getattr(exc, "reset", "N/A"))
    return response

app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)

# CRITICAL: Add limiter to app state (required by slowapi)
app.state.limiter = limiter

# Use rate limit configurations from config
RATE_LIMITS = RATE_LIMIT_TIERS["default"]

# Request logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    """Log all incoming requests for debugging"""
    path = request.url.path
    
    # Log health checks once
    if path == "/health":
        if not hasattr(app.state, "health_logged"):
            logger.info(f"✅ Health check endpoint hit: {path}")
            app.state.health_logged = True
    else:
        # Log non-health requests
        logger.info(f"📥 Request: {request.method} {path}")
    
    response = await call_next(request)
    return response

# Rate limit info middleware
@app.middleware("http")
async def add_rate_limit_headers(request: Request, call_next):
    """Add rate limit information to response headers"""
    response = await call_next(request)
    
    # Add rate limit headers if they exist
    if hasattr(request.state, "view_rate_limit"):
        response.headers["X-RateLimit-Limit"] = request.state.view_rate_limit
    if hasattr(request.state, "remaining"):
        response.headers["X-RateLimit-Remaining"] = str(request.state.remaining)
    if hasattr(request.state, "reset_time"):
        response.headers["X-RateLimit-Reset"] = str(request.state.reset_time)
    
    return response

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
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Global session store - shared with V1
session_store = SessionStore()

# Initialize V2 orchestrator
orchestrator = None

# API Models - same as V1 for compatibility
class IntroResponse(BaseModel):
    session_id: str
    messages: List[Dict[str, Any]]  # Changed to Dict to match V2 format

class MessageRequest(BaseModel):
    session_id: str
    message: str


@app.get("/", status_code=200)
def read_root():
    """Health check endpoint - responds immediately for Scalingo"""
    logger.info("🎯 Root endpoint (/) accessed!")
    # Synchronous response for maximum compatibility
    return {"status": "ok", "version": "2.0.0", "service": "wuffchat-v2"}

@app.get("/health", status_code=200)
def health():
    """Alternative health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.head("/", status_code=200)
def head_root():
    """HEAD request support for health checks"""
    return None

# Scalingo specific health check
@app.get("/_health", status_code=200)
def scalingo_health():
    """Scalingo-specific health check endpoint"""
    return {"status": "UP"}

# Plain text health check
@app.get("/healthz", response_class=PlainTextResponse, status_code=200)
def healthz():
    """Plain text health check for maximum compatibility"""
    return "OK"

# Ultra-simple ping endpoint
@app.get("/ping", status_code=200)
def ping():
    """Ultra-simple ping endpoint"""
    logger.info("🏓 Ping endpoint accessed!")
    return "pong"

# Startup probe endpoint
@app.get("/ready", status_code=200)
def ready():
    """Readiness probe endpoint"""
    logger.info("✅ Readiness probe accessed!")
    return {"ready": True}

# Liveness probe endpoint  
@app.get("/alive", status_code=200)
def alive():
    """Liveness probe endpoint"""
    logger.info("💚 Liveness probe accessed!")
    return {"alive": True}


@app.options("/flow_intro")
async def flow_intro_options():
    """Handle preflight requests for flow_intro"""
    return {"status": "ok"}


@app.post("/flow_intro", response_model=IntroResponse, dependencies=[Depends(verify_api_key)])
@limiter.limit(RATE_LIMITS["flow_intro"])
async def flow_intro(request: Request):
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
        if orchestrator is None:
            logger.error("[V2] Orchestrator not initialized!")
            raise HTTPException(status_code=503, detail="Service not ready - orchestrator not initialized")
        
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


@app.options("/flow_step")
async def flow_step_options():
    """Handle preflight requests for flow_step"""
    return {"status": "ok"}


@app.post("/flow_step", dependencies=[Depends(verify_api_key)])
@limiter.limit(RATE_LIMITS["flow_step"])
async def flow_step(request: Request, req: MessageRequest):
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
        if orchestrator is None:
            logger.error("[V2] Orchestrator not initialized!")
            raise HTTPException(status_code=503, detail="Service not ready - orchestrator not initialized")
        
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
    
@app.get("/v2/debug/prompts")
async def get_prompt_debug_info():
    """
    Get debug information about loaded prompts.
    
    This endpoint shows all loaded prompts and their keys.
    """
    from src.core.prompt_manager import get_prompt_manager, PromptCategory
    
    try:
        pm = get_prompt_manager()
        
        # Get all prompts by category
        prompts_by_category = {}
        for category in PromptCategory:
            prompts_by_category[category.value] = pm.list_prompts(category)
        
        # Try to get the specific greeting prompts
        greeting_debug = {}
        try:
            greeting_debug["dog.greeting"] = pm.get("dog.greeting")[:50] + "..."
        except Exception as e:
            greeting_debug["dog.greeting"] = f"ERROR: {e}"
            
        try:
            greeting_debug["dog.greeting.followup"] = pm.get("dog.greeting.followup")[:50] + "..."
        except Exception as e:
            greeting_debug["dog.greeting.followup"] = f"ERROR: {e}"
        
        return {
            "total_prompts": len(pm.prompts),
            "prompts_by_category": prompts_by_category,
            "greeting_debug": greeting_debug,
            "all_dog_prompts": [k for k in pm.prompts.keys() if k.startswith("dog.")]
        }
    except Exception as e:
        logger.error(f"[V2] Error getting prompt debug info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Abrufen der Prompt-Debug-Informationen: {str(e)}"
        )


#@app.get("/v2/debug/schema/{collection}")
#async def get_collection_schema(collection: str):
#    """Get schema for a specific collection"""
#    client = weaviate_service._client
#    schema = client.collections.get(collection).config.get()
#    properties = [prop.name for prop in schema.properties]
#    return {
#        "collection": collection,
#        "properties": properties
#    }

# Main entry point
if __name__ == "__main__":
    import uvicorn
    import signal
    import sys
    
    def signal_handler(signum, frame):
        logger.info(f"⚠️ Received signal {signum} - {signal.Signals(signum).name}")
        logger.info("🛑 Main process shutting down gracefully...")
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGHUP, signal_handler)
    
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