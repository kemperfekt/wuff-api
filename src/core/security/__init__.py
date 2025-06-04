"""
Security module for V2 architecture.

Centralizes all security-related functionality:
- Session management with tokens
- Input validation
- Rate limiting coordination
- Security middleware

This module is designed to be a clean layer on top of the
business logic, not intertwined with it.
"""

from .session_security import (
    SecureSessionStore,
    SessionToken,
    get_secure_session_store,
    init_secure_session_store
)

__all__ = [
    'SecureSessionStore',
    'SessionToken', 
    'get_secure_session_store',
    'init_secure_session_store'
]