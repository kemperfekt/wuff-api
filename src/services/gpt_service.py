# src/v2/services/gpt_service.py
"""
GPT Service for WuffChat V2.

Clean, async-only wrapper around OpenAI API with:
- Consistent error handling
- Proper initialization pattern
- Health checks
- No embedded prompts
- Testable design
"""
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import logging
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from src.core.service_base import BaseService, ServiceConfig
from src.core.exceptions import (
    GPTServiceError, 
    ConfigurationError,
    ValidationError
)

logger = logging.getLogger(__name__)


@dataclass
class GPTConfig(ServiceConfig):
    """Configuration for GPT Service"""
    api_key: Optional[str] = None
    model: str = "gpt-3.5-turbo"
    max_tokens: Optional[int] = None
    temperature: float = 0.7
    timeout: int = 30
    max_retries: int = 2


class GPTService(BaseService[GPTConfig]):
    """
    Async-only GPT service for text generation.
    
    This service provides a clean interface to OpenAI's GPT models,
    handling all the complexity of API interaction, retries, and errors.
    """
    
    def __init__(self, config: Optional[GPTConfig] = None):
        """
        Initialize GPT Service.
        
        Args:
            config: GPT configuration. If not provided, uses environment variables.
        """
        # Use provided config or create default
        if config is None:
            config = GPTConfig(
                api_key=os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_APIKEY"),
                model=os.getenv("GPT_MODEL", "gpt-3.5-turbo"),
                temperature=float(os.getenv("GPT_TEMPERATURE", "0.7"))
            )
        
        super().__init__(config, logger)
    
    def _validate_config(self) -> None:
        """Validate GPT configuration"""
        super()._validate_config()
        
        if not self.config.api_key:
            raise ConfigurationError(
                config_key="api_key",
                message="OpenAI API key is required. Set OPENAI_API_KEY environment variable."
            )
        
        if self.config.temperature < 0 or self.config.temperature > 2:
            raise ConfigurationError(
                config_key="temperature",
                message="Temperature must be between 0 and 2"
            )
    
    async def _initialize_client(self) -> AsyncOpenAI:
        """Initialize the OpenAI client"""
        return AsyncOpenAI(
            api_key=self.config.api_key,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries
        )
    
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate a completion for the given prompt.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt to set context
            temperature: Override default temperature
            max_tokens: Override default max tokens
            **kwargs: Additional OpenAI API parameters
            
        Returns:
            Generated text completion
            
        Raises:
            GPTServiceError: If generation fails
            ValidationError: If inputs are invalid
        """
        await self.ensure_initialized()
        
        # Validate inputs
        if not prompt or not prompt.strip():
            raise ValidationError(
                field="prompt",
                message="Prompt cannot be empty"
            )
        
        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Merge parameters
        params = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature or self.config.temperature,
        }
        
        if max_tokens or self.config.max_tokens:
            params["max_tokens"] = max_tokens or self.config.max_tokens
        
        # Merge any additional kwargs
        params.update(kwargs)
        
        try:
            self.logger.debug(f"Generating completion with model {params['model']}")
            
            response: ChatCompletion = await self.client.chat.completions.create(**params)
            
            if not response.choices:
                raise GPTServiceError(
                    message="No completion choices returned from API"
                )
            
            content = response.choices[0].message.content
            
            if not content:
                raise GPTServiceError(
                    message="Empty completion returned from API"
                )
            
            self.logger.debug(f"Generated completion: {len(content)} characters")
            return content.strip()
            
        except Exception as e:
            # Don't wrap if it's already our error
            if isinstance(e, (GPTServiceError, ValidationError)):
                raise
            
            # Wrap other errors
            error_msg = f"Failed to generate completion: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            
            raise GPTServiceError(
                message=error_msg,
                original_error=e
            )
    
    async def complete_structured(
        self,
        prompt: str,
        response_format: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a structured (JSON) completion.
        
        Args:
            prompt: The prompt requesting structured output
            response_format: Expected response format/schema
            **kwargs: Additional parameters for complete()
            
        Returns:
            Parsed JSON response
            
        Raises:
            GPTServiceError: If generation or parsing fails
        """
        import json
        
        # Add instruction for JSON output
        json_prompt = f"{prompt}\n\nRespond with valid JSON matching this format: {json.dumps(response_format, indent=2)}"
        
        # Use lower temperature for structured output
        kwargs.setdefault('temperature', 0.3)
        
        response = await self.complete(json_prompt, **kwargs)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            raise GPTServiceError(
                message=f"Failed to parse JSON response: {e}",
                original_error=e,
                details={"response": response}
            )
    
    async def validate_behavior_input(self, text: str) -> bool:
        """
        Check if text is related to dog behavior.
        
        Args:
            text: User input to validate
            
        Returns:
            True if dog-related, False otherwise
        """
        # Note: In V2, we get the prompt from PromptManager, not embed it here
        validation_prompt = f"""Antworte mit 'ja' oder 'nein'. 
Hat die folgende Eingabe mit Hundeverhalten oder Hundetraining zu tun?

{text}"""
        
        try:
            response = await self.complete(
                validation_prompt,
                temperature=0,
                max_tokens=1
            )
            
            return "ja" in response.lower()
            
        except Exception as e:
            # On error, default to allowing the input
            self.logger.warning(f"Validation failed, defaulting to True: {e}")
            return True
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check GPT service health.
        
        Returns:
            Health status including availability and response time
        """
        import time
        
        try:
            start_time = time.time()
            
            # Try a minimal completion
            await self.complete(
                "Respond with OK",
                temperature=0,
                max_tokens=5
            )
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            return {
                "healthy": True,
                "status": "connected",
                "details": {
                    "model": self.config.model,
                    "response_time_ms": response_time_ms,
                    "api_key_set": bool(self.config.api_key),
                    "api_key_prefix": self.config.api_key[:8] + "..." if self.config.api_key else None
                }
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "status": "error",
                "details": {
                    "error": str(e),
                    "model": self.config.model
                }
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics"""
        metrics = super().get_metrics()
        metrics.update({
            "model": self.config.model,
            "temperature": self.config.temperature,
            "timeout": self.config.timeout
        })
        return metrics


# Convenience function for quick access
async def create_gpt_service(
    api_key: Optional[str] = None,
    model: str = "gpt-3.5-turbo",
    **kwargs
) -> GPTService:
    """
    Create and initialize a GPT service instance.
    
    Args:
        api_key: OpenAI API key (uses env var if not provided)
        model: Model to use
        **kwargs: Additional config parameters
        
    Returns:
        Initialized GPTService
    """
    config = GPTConfig(
        api_key=api_key,
        model=model,
        **kwargs
    )
    service = GPTService(config)
    await service.initialize()
    return service