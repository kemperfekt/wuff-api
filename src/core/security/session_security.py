"""
Session security module for V2 architecture.

This module provides secure session management with tokens and expiration,
following the V2 architectural principles:
- Clean separation of concerns
- Single responsibility 
- Dependency injection
- Type safety with Pydantic

Part of the security layer, not a modification of core business logic.
"""

from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta, timezone
import secrets
from pydantic import BaseModel, Field

from src.models.session_state import SessionState
from src.core.logging_config import setup_logging
from src.core.exceptions import V2SecurityError

logger = setup_logging()


class SessionToken(BaseModel):
    """
    Secure token for session validation.
    
    Architectural note: Separate from SessionState to maintain 
    single responsibility - SessionState handles conversation state,
    SessionToken handles authentication.
    """
    token: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(minutes=30))
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    def is_expired(self) -> bool:
        """Check if token has expired"""
        return datetime.now(timezone.utc) > self.expires_at
    
    def validate(self, provided_token: str) -> bool:
        """Securely compare tokens"""
        return secrets.compare_digest(self.token, provided_token)
    
    def refresh(self) -> None:
        """Extend expiration on activity"""
        now = datetime.now(timezone.utc)
        self.last_activity = now
        self.expires_at = now + timedelta(minutes=30)


class SecureSessionStore:
    """
    Secure session store implementing token-based authentication.
    
    Design decisions:
    1. Composition over inheritance - wraps SessionStore
    2. Fail-secure - no auto-creation, explicit validation
    3. Clean interface - returns Optional instead of exceptions
    4. Automatic cleanup - prevents memory leaks
    """
    
    def __init__(self):
        # Separate stores for separation of concerns
        self._sessions: Dict[str, SessionState] = {}
        self._tokens: Dict[str, SessionToken] = {}
        
        # Cleanup configuration
        self._cleanup_interval = timedelta(minutes=5)
        self._last_cleanup = datetime.now(timezone.utc)
        
        # Metrics for monitoring
        self._creation_count = 0
        self._validation_failures = 0
    
    def create_session(self) -> Tuple[SessionState, str]:
        """
        Create a new secure session.
        
        Returns:
            Tuple of (SessionState, token_string)
            
        Architectural note: Returns tuple to keep token separate
        from session state - frontend needs token, business logic
        needs session.
        """
        # Create session
        session = SessionState()
        
        # Create security token
        token = SessionToken()
        
        # Store both
        self._sessions[session.session_id] = session
        self._tokens[session.session_id] = token
        
        # Metrics
        self._creation_count += 1
        
        # Periodic cleanup
        self._cleanup_expired()
        
        logger.info(f"🔐 Created secure session {session.session_id[:8]}...")
        return session, token.token
    
    def validate_and_get_session(
        self, 
        session_id: str, 
        token: str
    ) -> Optional[SessionState]:
        """
        Validate token and return session if valid.
        
        Returns:
            SessionState if valid, None if invalid/expired
            
        Design: Returns None instead of raising exception for
        cleaner error handling in request flow.
        """
        # Check session exists
        session = self._sessions.get(session_id)
        if not session:
            logger.debug(f"Session {session_id[:8]}... not found")
            return None
        
        # Check token exists
        session_token = self._tokens.get(session_id)
        if not session_token:
            logger.warning(f"🚫 No token for session {session_id[:8]}...")
            self._validation_failures += 1
            return None
        
        # Check expiration
        if session_token.is_expired():
            logger.info(f"⏰ Session {session_id[:8]}... expired")
            self.delete_session(session_id)
            return None
        
        # Validate token
        if not session_token.validate(token):
            logger.warning(f"🔒 Invalid token for session {session_id[:8]}...")
            self._validation_failures += 1
            return None
        
        # Success - refresh activity
        session_token.refresh()
        return session
    
    def delete_session(self, session_id: str) -> None:
        """Explicitly remove a session and its token"""
        if session_id in self._sessions:
            del self._sessions[session_id]
        if session_id in self._tokens:
            del self._tokens[session_id]
            logger.debug(f"🗑️ Deleted session {session_id[:8]}...")
    
    def _cleanup_expired(self) -> None:
        """
        Remove expired sessions periodically.
        
        Design: Automatic cleanup prevents memory leaks without
        requiring external cron jobs.
        """
        now = datetime.now(timezone.utc)
        
        # Rate limit cleanup operations
        if now - self._last_cleanup < self._cleanup_interval:
            return
        
        # Find expired sessions
        expired_ids = [
            sid for sid, token in self._tokens.items()
            if token.is_expired()
        ]
        
        # Remove them
        for sid in expired_ids:
            self.delete_session(sid)
        
        self._last_cleanup = now
        
        if expired_ids:
            logger.info(f"🧹 Cleaned up {len(expired_ids)} expired sessions")
    
    def get_metrics(self) -> Dict[str, int]:
        """
        Get store metrics for monitoring.
        
        Architectural note: Metrics separated from business logic
        for clean monitoring integration.
        """
        return {
            "active_sessions": len(self._sessions),
            "total_created": self._creation_count,
            "validation_failures": self._validation_failures,
            "expired_cleaned": self._creation_count - len(self._sessions)
        }
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, any]]:
        """
        Get session information for debugging (no token exposed).
        
        Used by admin/debug endpoints only.
        """
        session = self._sessions.get(session_id)
        token = self._tokens.get(session_id)
        
        if not session or not token:
            return None
        
        return {
            "session_id": session_id,
            "created_at": token.created_at.isoformat(),
            "expires_at": token.expires_at.isoformat(),
            "last_activity": token.last_activity.isoformat(),
            "is_expired": token.is_expired(),
            "current_step": session.current_step.value
        }


# Global instance - initialized in main.py
secure_session_store: Optional[SecureSessionStore] = None


def get_secure_session_store() -> SecureSessionStore:
    """
    Get the global secure session store instance.
    
    Follows FastAPI dependency injection pattern.
    """
    global secure_session_store
    if secure_session_store is None:
        raise V2SecurityError("SecureSessionStore not initialized")
    return secure_session_store


def init_secure_session_store() -> SecureSessionStore:
    """Initialize the global secure session store"""
    global secure_session_store
    secure_session_store = SecureSessionStore()
    logger.info("🔐 Initialized SecureSessionStore")
    return secure_session_store