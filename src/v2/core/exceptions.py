# src/v2/core/exceptions.py
"""
Clean exception hierarchy for WuffChat V2.

Provides structured error handling with proper separation between
different types of failures (service errors, validation errors, etc.)
"""
from typing import Optional, Dict, Any


class WuffChatError(Exception):
    """Base exception for all WuffChat V2 errors"""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}


class ServiceError(WuffChatError):
    """Base exception for service-related errors"""
    
    def __init__(
        self, 
        service_name: str,
        message: str,
        original_error: Optional[Exception] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.service_name = service_name
        self.original_error = original_error
        
        if original_error:
            self.details["original_error"] = str(original_error)
            self.details["original_error_type"] = type(original_error).__name__


class GPTServiceError(ServiceError):
    """Error in GPT/OpenAI service operations"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__("GPTService", message, **kwargs)


class WeaviateServiceError(ServiceError):
    """Error in Weaviate vector database operations"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__("WeaviateService", message, **kwargs)


class RedisServiceError(ServiceError):
    """Error in Redis cache operations"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__("RedisService", message, **kwargs)


class ValidationError(WuffChatError):
    """Input validation errors"""
    
    def __init__(
        self, 
        field: str,
        message: str,
        invalid_value: Any = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.field = field
        self.details["field"] = field
        
        if invalid_value is not None:
            self.details["invalid_value"] = str(invalid_value)


class FlowError(WuffChatError):
    """Errors in conversation flow management"""
    
    def __init__(
        self,
        current_state: str,
        message: str,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.current_state = current_state
        self.details["current_state"] = current_state


class StateTransitionError(FlowError):
    """Invalid state transition attempted"""
    
    def __init__(
        self,
        from_state: str,
        to_state: str,
        event: str,
        **kwargs
    ):
        message = f"Invalid transition from {from_state} to {to_state} via {event}"
        super().__init__(from_state, message, **kwargs)
        self.from_state = from_state
        self.to_state = to_state
        self.event = event
        self.details.update({
            "from_state": from_state,
            "to_state": to_state,
            "event": event
        })


class PromptError(WuffChatError):
    """Errors related to prompt management"""
    
    def __init__(
        self,
        prompt_key: str,
        message: str,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.prompt_key = prompt_key
        self.details["prompt_key"] = prompt_key


class ConfigurationError(WuffChatError):
    """Configuration or environment errors"""
    
    def __init__(
        self,
        config_key: str,
        message: str,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.config_key = config_key
        self.details["config_key"] = config_key


# Error handlers for common patterns
class ErrorHandler:
    """Utility class for consistent error handling"""
    
    @staticmethod
    def handle_service_error(
        error: Exception,
        service_name: str,
        fallback_value: Any,
        logger = None
    ) -> Any:
        """
        Handle service errors with logging and fallback.
        
        Args:
            error: The exception that occurred
            service_name: Name of the service that failed
            fallback_value: Value to return on error
            logger: Optional logger instance
            
        Returns:
            The fallback value
        """
        error_message = f"{service_name} error: {str(error)}"
        
        if logger:
            logger.error(error_message, exc_info=True)
        
        # Re-raise if it's already a WuffChat error
        if isinstance(error, WuffChatError):
            raise
        
        # Otherwise, wrap and continue with fallback
        return fallback_value
    
    @staticmethod
    def create_user_friendly_message(error: WuffChatError) -> str:
        """
        Convert technical errors to user-friendly German messages.
        
        Args:
            error: The WuffChat error
            
        Returns:
            User-friendly error message in German
        """
        error_messages = {
            "GPTServiceError": "Entschuldige, ich habe gerade technische Schwierigkeiten. Bitte versuche es gleich nochmal.",
            "WeaviateServiceError": "Ich kann gerade nicht auf mein Gedächtnis zugreifen. Bitte versuche es später noch einmal.",
            "RedisServiceError": "Es gibt ein Problem beim Speichern. Deine Eingabe wurde aber verarbeitet.",
            "ValidationError": "Ich habe deine Eingabe nicht verstanden. Kannst du es anders formulieren?",
            "FlowError": "Ups, ich bin durcheinander gekommen. Lass uns nochmal von vorne anfangen.",
            "ConfigurationError": "Es gibt ein technisches Problem. Bitte kontaktiere den Support.",
        }
        
        return error_messages.get(
            error.error_code,
            "Es ist ein unerwarteter Fehler aufgetreten. Bitte versuche es später noch einmal."
        )
    
# === V2 Agent Compatibility Classes ===
# These provide the exact interface that V2 agents expect

class V2BaseError(Exception):
    """Base exception for V2 agent operations"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class V2ValidationError(V2BaseError):
    """V2 validation errors with simple interface"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)


class V2AgentError(V2BaseError):
    """V2 agent operation errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)


class V2FlowError(V2BaseError):
    """V2 flow engine errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)


class V2ServiceError(V2BaseError):
    """V2 service errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)


# Aliases for backwards compatibility
V2BaseError = V2BaseError  # Self-reference for consistency