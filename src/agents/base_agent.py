# src/v2/agents/base_agent.py
"""
V2 Base Agent - Clean interface focused on message formatting only.

Key principles:
- No business logic (handled by services)
- Use PromptManager for all content
- Async-only methods
- Clean error handling with V2 exceptions
- Message formatting and response structure only
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum

from src.core.prompt_manager import PromptManager, PromptType
from src.core.exceptions import V2AgentError, V2ValidationError
from src.services.gpt_service import GPTService
from src.services.weaviate_service import WeaviateService
from src.services.redis_service import RedisService


@dataclass
class V2AgentMessage:
    """V2 Agent message - clean and independent from V1"""
    sender: str
    text: str
    message_type: str = "response"
    metadata: Dict[str, Any] = field(default_factory=dict)


class MessageType(str, Enum):
    """Types of messages an agent can generate"""
    GREETING = "greeting"
    QUESTION = "question"
    RESPONSE = "response"
    ERROR = "error"
    CONFIRMATION = "confirmation"
    INSTRUCTION = "instruction"


@dataclass
class AgentContext:
    """Context passed to agents for message generation"""
    session_id: str
    user_input: str = ""
    message_type: MessageType = MessageType.RESPONSE
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseAgent(ABC):
    """
    Base class for all V2 agents.
    
    Agents in V2 are responsible ONLY for:
    1. Message formatting and structure
    2. Prompt selection and parameter filling
    3. Response formatting
    
    Business logic is handled by services.
    """
    
    def __init__(
        self, 
        name: str, 
        role: str,
        prompt_manager: Optional[PromptManager] = None,
        gpt_service: Optional[GPTService] = None,
        weaviate_service: Optional[WeaviateService] = None,
        redis_service: Optional[RedisService] = None
    ):
        """
        Initialize the agent with required services.
        
        Args:
            name: Human-readable name of the agent
            role: Role identifier for message attribution
            prompt_manager: Centralized prompt management
            gpt_service: GPT service for text generation
            weaviate_service: Vector search service
            redis_service: Caching/storage service
        """
        self.name = name
        self.role = role
        
        # Services - injected for testability
        self.prompt_manager = prompt_manager or PromptManager()
        self.gpt_service = gpt_service
        self.weaviate_service = weaviate_service
        self.redis_service = redis_service
        
        # Agent configuration
        self._default_model = "gpt-4"
        self._max_tokens = 1000
        self._temperature = 0.7
    
    @abstractmethod
    async def respond(
        self, 
        context: AgentContext
    ) -> List[V2AgentMessage]:
        """
        Generate response messages based on context.
        
        This is the main entry point for agent interaction.
        Implementation should focus on message formatting only.
        
        Args:
            context: Agent context with user input and metadata
            
        Returns:
            List of formatted agent messages
            
        Raises:
            V2AgentError: If message generation fails
            V2ValidationError: If context is invalid
        """
        pass
    
    @abstractmethod
    def get_supported_message_types(self) -> List[MessageType]:
        """
        Return list of message types this agent can generate.
        
        Returns:
            List of supported MessageType values
        """
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check if agent and its dependencies are healthy.
        
        Returns:
            Dict with health status information
        """
        status = {
            "agent": self.name,
            "role": self.role,
            "healthy": True,
            "services": {}
        }
        
        # Check prompt manager
        try:
            self.prompt_manager.get_prompt(PromptType.VALIDATION, text="test")
            status["services"]["prompt_manager"] = "healthy"
        except Exception as e:
            status["services"]["prompt_manager"] = f"error: {str(e)}"
            status["healthy"] = False
        
        # Check optional services
        for service_name, service in [
            ("gpt_service", self.gpt_service),
            ("weaviate_service", self.weaviate_service),
            ("redis_service", self.redis_service)
        ]:
            if service:
                try:
                    service_status = await service.health_check()
                    status["services"][service_name] = "healthy" if service_status.get("healthy", False) else "unhealthy"
                except Exception as e:
                    status["services"][service_name] = f"error: {str(e)}"
                    if service_name == "gpt_service":  # GPT is critical for most agents
                        status["healthy"] = False
        
        return status
    
    # Helper methods for common message formatting tasks
    
    def create_message(
        self, 
        text: str, 
        message_type: MessageType = MessageType.RESPONSE,
        metadata: Optional[Dict[str, Any]] = None
    ) -> V2AgentMessage:
        """
        Create a formatted V2AgentMessage.
        
        Args:
            text: Message text content
            message_type: Type of message
            metadata: Optional metadata
            
        Returns:
            Formatted V2AgentMessage
        """
        return V2AgentMessage(
            sender=self.role,
            text=text.strip(),
            message_type=message_type.value,
            metadata=metadata or {}
        )
    
    def create_error_message(self, error_msg: str) -> V2AgentMessage:
        """
        Create a user-friendly error message.
        
        Args:
            error_msg: Technical error message
            
        Returns:
            User-friendly error message
        """
        # Don't expose technical details to users
        friendly_msg = "Es tut mir leid, ich habe gerade ein technisches Problem. Kannst du es später noch einmal versuchen?"
        return self.create_message(friendly_msg, MessageType.ERROR)
    
    async def generate_text_with_prompt(
        self,
        prompt_type: PromptType,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **prompt_params
    ) -> str:
        """
        Generate text using a prompt from PromptManager.
        
        Args:
            prompt_type: Type of prompt to use
            model: GPT model (defaults to agent default)
            max_tokens: Max tokens (defaults to agent default)
            temperature: Temperature (defaults to agent default)
            **prompt_params: Parameters for prompt formatting
            
        Returns:
            Generated text
            
        Raises:
            V2AgentError: If generation fails
        """
        if not self.gpt_service:
            raise V2AgentError(f"GPT service not available for agent {self.name}")
        
        try:
            # Get prompt from manager
            prompt = self.prompt_manager.get_prompt(prompt_type, **prompt_params)
            
            # Generate text
            result = await self.gpt_service.complete(
                prompt=prompt,
                system_prompt=self._system_prompt if hasattr(self, '_system_prompt') else None,
                model=model or self._default_model,
                max_tokens=max_tokens or self._max_tokens,
                temperature=temperature or self._temperature
            )
            
            return result.strip()
            
        except Exception as e:
            raise V2AgentError(f"Text generation failed for {self.name}: {str(e)}") from e
    
    async def search_knowledge(
        self,
        query: str,
        collection_name: Optional[str] = None,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge base for relevant information.
        
        Args:
            query: Search query
            collection_name: Optional collection to search in
            limit: Number of results to return
            
        Returns:
            List of search results
            
        Raises:
            V2AgentError: If search fails
        """
        if not self.weaviate_service:
            raise V2AgentError(f"Weaviate service not available for agent {self.name}")
        
        try:
            results = await self.weaviate_service.vector_search(
                query=query,
                collection_name=collection_name,
                limit=limit
            )
            return results
            
        except Exception as e:
            raise V2AgentError(f"Knowledge search failed for {self.name}: {str(e)}") from e
    
    def validate_context(self, context: AgentContext) -> None:
        """
        Validate agent context.
        
        Args:
            context: Context to validate
            
        Raises:
            V2ValidationError: If context is invalid
        """
        if not isinstance(context, AgentContext):
            raise V2ValidationError("Context must be an AgentContext instance")
        
        if not context.session_id:
            raise V2ValidationError("Context must have a session_id")
        
        if not isinstance(context.message_type, MessageType):
            raise V2ValidationError("Context must have a valid message_type")
        
        # Allow subclasses to add validation
        self._validate_context_impl(context)
    
    def _validate_context_impl(self, context: AgentContext) -> None:
        """
        Override this in subclasses for custom validation.
        
        Args:
            context: Context to validate
            
        Raises:
            V2ValidationError: If context is invalid
        """
        pass
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', role='{self.role}')"
    
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"name='{self.name}', "
            f"role='{self.role}', "
            f"services={list(filter(None, [self.gpt_service, self.weaviate_service, self.redis_service]))}"
            f")"
        )