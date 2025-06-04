# src/v2/core/exceptions.py
"""
V2 Core Exceptions - Complete standardized error handling for V2 architecture.

This module defines all custom exceptions used in the V2 system,
providing consistent error handling and debugging information.
"""

from typing import Optional, Dict, Any, List


class V2BaseException(Exception):
    """Base exception for all V2 errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize V2 base exception.
        
        Args:
            message: Human-readable error message
            details: Optional additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class V2FlowError(V2BaseException):
    """Errors in flow processing and state transitions"""
    
    def __init__(
        self, 
        message: str, 
        current_state: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        messages: Optional[List[Any]] = None
    ):
        """
        Initialize flow error.
        
        Args:
            message: Error description  
            current_state: State where error occurred
            details: Additional error context
            messages: Optional list of V2AgentMessage objects to return
        """
        super().__init__(message, details)
        self.current_state = current_state
        self.messages = messages or []
        
        # Add current state to details
        if current_state:
            self.details['current_state'] = current_state
    
    def __str__(self) -> str:
        """String representation including state context"""
        base_msg = super().__str__()
        if self.current_state:
            return f"{base_msg} [State: {self.current_state}]"
        return base_msg


class V2ValidationError(V2BaseException):
    """Errors in input validation and data integrity"""
    
    def __init__(
        self, 
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize validation error.
        
        Args:
            message: Error description
            field: Field that failed validation
            value: Invalid value
            details: Additional validation context
        """
        super().__init__(message, details)
        self.field = field
        self.value = value
        
        # Add field info to details
        if field:
            self.details['field'] = field
        if value is not None:
            self.details['value'] = str(value)


class V2ServiceError(V2BaseException):
    """Errors in external service interactions"""
    
    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize service error.
        
        Args:
            message: Error description
            service_name: Name of the failing service
            operation: Operation that failed
            details: Additional service context
        """
        super().__init__(message, details)
        self.service_name = service_name
        self.operation = operation
        
        # Add service info to details
        if service_name:
            self.details['service'] = service_name
        if operation:
            self.details['operation'] = operation


class V2AgentError(V2BaseException):
    """Errors in agent processing and responses"""
    
    def __init__(
        self,
        message: str,
        agent_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize agent error.
        
        Args:
            message: Error description
            agent_name: Name of the failing agent
            details: Additional agent context
        """
        super().__init__(message, details)
        self.agent_name = agent_name
        
        if agent_name:
            self.details['agent'] = agent_name


class V2ConfigurationError(V2BaseException):
    """Errors in system configuration and initialization"""
    
    def __init__(
        self,
        message: str,
        component: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize configuration error.
        
        Args:
            message: Error description
            component: Component with configuration issue
            details: Additional configuration context
        """
        super().__init__(message, details)
        self.component = component
        
        if component:
            self.details['component'] = component


class PromptError(V2BaseException):
    """Errors in prompt management and template processing"""
    
    def __init__(
        self,
        message: str,
        prompt_type: Optional[str] = None,
        template_vars: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize prompt error.
        
        Args:
            message: Error description
            prompt_type: Type of prompt that failed
            template_vars: Variables used in template
            details: Additional prompt context
        """
        super().__init__(message, details)
        self.prompt_type = prompt_type
        self.template_vars = template_vars or {}
        
        if prompt_type:
            self.details['prompt_type'] = prompt_type
        if template_vars:
            self.details['template_vars'] = template_vars


class GPTServiceError(V2ServiceError):
    """Specific errors for GPT service interactions"""
    
    def __init__(
        self,
        message: str,
        model: Optional[str] = None,
        prompt_length: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize GPT service error.
        
        Args:
            message: Error description
            model: GPT model that failed
            prompt_length: Length of prompt that failed
            details: Additional GPT context
        """
        super().__init__(message, service_name="GPT", details=details)
        self.model = model
        self.prompt_length = prompt_length
        
        if model:
            self.details['model'] = model
        if prompt_length:
            self.details['prompt_length'] = prompt_length


class WeaviateServiceError(V2ServiceError):
    """Specific errors for Weaviate service interactions"""
    
    def __init__(
        self,
        message: str,
        collection: Optional[str] = None,
        query: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Weaviate service error.
        
        Args:
            message: Error description
            collection: Collection that failed
            query: Query that failed
            details: Additional Weaviate context
        """
        super().__init__(message, service_name="Weaviate", details=details)
        self.collection = collection
        self.query = query
        
        if collection:
            self.details['collection'] = collection
        if query:
            self.details['query'] = query[:100]  # Truncate long queries


class RedisServiceError(V2ServiceError):
    """Specific errors for Redis service interactions"""
    
    def __init__(
        self,
        message: str,
        key: Optional[str] = None,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Redis service error.
        
        Args:
            message: Error description
            key: Redis key that failed
            operation: Redis operation that failed
            details: Additional Redis context
        """
        super().__init__(message, service_name="Redis", operation=operation, details=details)
        self.key = key
        
        if key:
            self.details['key'] = key


class SessionError(V2BaseException):
    """Errors in session management and state handling"""
    
    def __init__(
        self,
        message: str,
        session_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize session error.
        
        Args:
            message: Error description
            session_id: Session that failed
            details: Additional session context
        """
        super().__init__(message, details)
        self.session_id = session_id
        
        if session_id:
            self.details['session_id'] = session_id


class V2SecurityError(V2BaseException):
    """Errors in security validation and authentication"""
    
    def __init__(
        self,
        message: str,
        error_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize security error.
        
        Args:
            message: Error description
            error_type: Type of security error (auth, token, expiration)
            details: Additional security context
        """
        super().__init__(message, details)
        self.error_type = error_type
        
        if error_type:
            self.details['error_type'] = error_type


class MessageError(V2BaseException):
    """Errors in message processing and formatting"""
    
    def __init__(
        self,
        message: str,
        message_type: Optional[str] = None,
        sender: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize message error.
        
        Args:
            message: Error description
            message_type: Type of message that failed
            sender: Sender of the message
            details: Additional message context
        """
        super().__init__(message, details)
        self.message_type = message_type
        self.sender = sender
        
        if message_type:
            self.details['message_type'] = message_type
        if sender:
            self.details['sender'] = sender


# Convenience functions for creating common errors

def flow_error(message: str, current_state: str) -> V2FlowError:
    """Create a flow error with current state context."""
    return V2FlowError(message, current_state=current_state)


def validation_error(message: str, field: str, value: Any = None) -> V2ValidationError:
    """Create a validation error with field context."""
    return V2ValidationError(message, field=field, value=value)


def service_error(message: str, service: str, operation: str = None) -> V2ServiceError:
    """Create a service error with service context."""
    return V2ServiceError(message, service_name=service, operation=operation)


def agent_error(message: str, agent: str) -> V2AgentError:
    """Create an agent error with agent context."""
    return V2AgentError(message, agent_name=agent)


def config_error(message: str, component: str) -> V2ConfigurationError:
    """Create a configuration error with component context."""
    return V2ConfigurationError(message, component=component)


def prompt_error(message: str, prompt_type: str, template_vars: Dict[str, Any] = None) -> PromptError:
    """Create a prompt error with prompt context."""
    return PromptError(message, prompt_type=prompt_type, template_vars=template_vars)


def gpt_error(message: str, model: str = None, prompt_length: int = None) -> GPTServiceError:
    """Create a GPT service error with model context."""
    return GPTServiceError(message, model=model, prompt_length=prompt_length)


def weaviate_error(message: str, collection: str = None, query: str = None) -> WeaviateServiceError:
    """Create a Weaviate service error with collection context."""
    return WeaviateServiceError(message, collection=collection, query=query)


def redis_error(message: str, key: str = None, operation: str = None) -> RedisServiceError:
    """Create a Redis service error with key context."""
    return RedisServiceError(message, key=key, operation=operation)


def session_error(message: str, session_id: str) -> SessionError:
    """Create a session error with session context."""
    return SessionError(message, session_id=session_id)


def message_error(message: str, message_type: str = None, sender: str = None) -> MessageError:
    """Create a message error with message context."""
    return MessageError(message, message_type=message_type, sender=sender)


# Aliases for backward compatibility and shorter names
ServiceError = V2ServiceError
ConfigurationError = V2ConfigurationError
AgentError = V2AgentError
FlowError = V2FlowError
ValidationError = V2ValidationError