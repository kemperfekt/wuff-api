# src/core/error_handling.py
import logging
import traceback
from typing import Dict, Any, Optional, Callable, Type

# Logger einrichten
logger = logging.getLogger(__name__)

class ServiceError(Exception):
    """Basisklasse für alle Service-Fehler"""
    
    def __init__(self, service_name: str, original_error: Exception, is_critical: bool = False):
        self.service_name = service_name
        self.original_error = original_error
        self.is_critical = is_critical
        self.traceback = traceback.format_exc()
        
        super().__init__(f"Fehler in {service_name}: {original_error}")

class GPTServiceError(ServiceError):
    """Fehler im GPT-Service"""
    pass

class RAGServiceError(ServiceError):
    """Fehler im RAG-Service"""
    pass

class DatabaseError(ServiceError):
    """Fehler bei Datenbankoperationen"""
    pass

# Fehlerbehandlungsstrategie
def handle_service_error(error: Exception, fallback_value: Any, log_level: str = "error") -> Any:
    """
    Zentrale Fehlerbehandlung für Service-Fehler
    
    Args:
        error: Der aufgetretene Fehler
        fallback_value: Der Wert, der bei einem Fehler zurückgegeben werden soll
        log_level: Das Level für das Logging (info, warning, error, critical)
        
    Returns:
        Der Fallback-Wert
    """
    # Logging entsprechend dem Level
    log_method = getattr(logger, log_level.lower())
    
    if isinstance(error, ServiceError):
        log_method(
            f"{error.service_name}-Fehler: {error.original_error}\n"
            f"Critical: {error.is_critical}\n"
            f"Traceback: {error.traceback}"
        )
    else:
        log_method(f"Allgemeiner Fehler: {error}\n{traceback.format_exc()}")
    
    return fallback_value

# Decorator für Fehlerbehandlung in Services
def with_error_handling(error_class: Type[ServiceError], fallback_value: Any, log_level: str = "error"):
    """
    Decorator für Service-Methoden mit einheitlicher Fehlerbehandlung
    
    Args:
        error_class: Die zu verwendende Fehlerklasse
        fallback_value: Der Wert, der bei einem Fehler zurückgegeben werden soll
        log_level: Das Level für das Logging
        
    Returns:
        Die dekorierte Funktion
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                service_error = error_class(func.__name__, e)
                return handle_service_error(service_error, fallback_value, log_level)
        return wrapper
    return decorator