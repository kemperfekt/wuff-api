# src/v2/core/service_base.py
"""
Base service class for standardized service implementation in WuffChat V2.

All services should inherit from BaseService to ensure consistent:
- Initialization patterns
- Error handling
- Health checks
- Resource cleanup
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, TypeVar, Generic
import logging
from contextlib import asynccontextmanager
from src.core.exceptions import ServiceError, ConfigurationError

# Type variable for service configuration
ConfigType = TypeVar('ConfigType')


class ServiceConfig:
    """Base configuration class for services"""
    pass


class BaseService(ABC, Generic[ConfigType]):
    """
    Abstract base class for all V2 services.
    
    Provides:
    - Lazy initialization pattern
    - Consistent error handling
    - Health check interface
    - Resource management
    - Logging setup
    """
    
    def __init__(
        self, 
        config: Optional[ConfigType] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the service.
        
        Args:
            config: Service-specific configuration
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self._initialized = False
        self._client = None
        
        # Service metadata
        self.service_name = self.__class__.__name__
        self.service_version = "2.0"
        
    @abstractmethod
    async def _initialize_client(self) -> Any:
        """
        Initialize the underlying client/connection.
        
        This method should:
        - Create and configure the client
        - Establish connections
        - Validate configuration
        
        Returns:
            The initialized client
            
        Raises:
            ConfigurationError: If configuration is invalid
            ServiceError: If initialization fails
        """
        pass
    
    async def initialize(self) -> None:
        """
        Initialize the service (lazy loading pattern).
        
        This method is idempotent - multiple calls are safe.
        """
        if self._initialized:
            self.logger.debug(f"{self.service_name} already initialized")
            return
        
        try:
            self.logger.info(f"Initializing {self.service_name}...")
            
            # Validate configuration before initialization
            self._validate_config()
            
            # Initialize the client
            self._client = await self._initialize_client()
            
            # Mark as initialized
            self._initialized = True
            
            self.logger.info(f"{self.service_name} initialized successfully")
            
        except ConfigurationError:
            # Re-raise configuration errors as-is
            raise
        except Exception as e:
            # Wrap other errors as ServiceError
            error_msg = f"Failed to initialize {self.service_name}"
            self.logger.error(error_msg, exc_info=True)
            raise ServiceError(
                service_name=self.service_name,
                message=error_msg,
                details={'original_error': str(e), 'error_type': type(e).__name__}
            )
    
    def _validate_config(self) -> None:
        """
        Validate service configuration.
        
        Override this method to add service-specific validation.
        
        Raises:
            ConfigurationError: If configuration is invalid
        """
        if self.config is None:
            self.logger.debug(f"No configuration provided for {self.service_name}")
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the service.
        
        Returns:
            Dict containing:
            - healthy: bool indicating if service is healthy
            - status: string status message
            - details: optional additional information
            
        Example:
            {
                "healthy": True,
                "status": "connected",
                "details": {
                    "response_time_ms": 45,
                    "version": "1.2.3"
                }
            }
        """
        pass
    
    async def ensure_initialized(self) -> None:
        """
        Ensure the service is initialized before use.
        
        Call this at the start of any public method that requires
        the service to be initialized.
        """
        if not self._initialized:
            await self.initialize()
    
    @property
    def is_initialized(self) -> bool:
        """Check if the service is initialized"""
        return self._initialized
    
    @property
    def client(self) -> Any:
        """
        Get the underlying client.
        
        Returns:
            The client instance
            
        Raises:
            ServiceError: If service is not initialized
        """
        if not self._initialized or self._client is None:
            raise ServiceError(
                service_name=self.service_name,
                message=f"{self.service_name} is not initialized. Call initialize() first."
            )
        return self._client
    
    async def shutdown(self) -> None:
        """
        Gracefully shutdown the service and cleanup resources.
        
        Override this method to add service-specific cleanup.
        """
        if not self._initialized:
            return
        
        try:
            self.logger.info(f"Shutting down {self.service_name}...")
            
            # Service-specific cleanup
            await self._cleanup()
            
            # Reset state
            self._client = None
            self._initialized = False
            
            self.logger.info(f"{self.service_name} shut down successfully")
            
        except Exception as e:
            self.logger.error(f"Error during {self.service_name} shutdown", exc_info=True)
            # Don't raise - we want cleanup to be as graceful as possible
    
    async def _cleanup(self) -> None:
        """
        Service-specific cleanup logic.
        
        Override this method to add cleanup for your service.
        """
        pass
    
    @asynccontextmanager
    async def transaction(self):
        """
        Context manager for service transactions.
        
        Usage:
            async with service.transaction():
                await service.operation1()
                await service.operation2()
        """
        await self.ensure_initialized()
        
        try:
            yield self
        except Exception as e:
            self.logger.error(f"Transaction failed in {self.service_name}", exc_info=True)
            raise
        finally:
            # Any transaction cleanup can go here
            pass
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get service metrics for monitoring.
        
        Override this method to provide service-specific metrics.
        
        Returns:
            Dict of metric name to value
        """
        return {
            "service_name": self.service_name,
            "service_version": self.service_version,
            "initialized": self._initialized,
        }
    
    async def test_connection(self) -> bool:
        """
        Test if the service can connect to its dependencies.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            health = await self.health_check()
            return health.get("healthy", False)
        except Exception:
            return False


class SingletonServiceMixin:
    """
    Mixin to make a service a singleton.
    
    Usage:
        class MyService(SingletonServiceMixin, BaseService):
            pass
    """
    _instances: Dict[type, Any] = {}
    
    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__new__(cls)
        return cls._instances[cls]
    
    @classmethod
    def get_instance(cls) -> 'SingletonServiceMixin':
        """Get the singleton instance"""
        if cls not in cls._instances:
            cls._instances[cls] = cls()
        return cls._instances[cls]
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (useful for testing)"""
        if cls in cls._instances:
            del cls._instances[cls]