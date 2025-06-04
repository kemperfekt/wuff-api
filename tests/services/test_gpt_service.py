# tests/v2/services/test_gpt_service.py
"""
Unit tests for V2 GPT Service.

Uses mock-first approach to test without making real API calls.
"""
import os
import pytest
from unittest.mock import Mock, AsyncMock, patch
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion import CompletionUsage

from src.services.gpt_service import GPTService, GPTConfig, create_gpt_service
from src.core.exceptions import GPTServiceError, ConfigurationError, ValidationError


@pytest.fixture
def mock_config():
    """Create a test configuration"""
    return GPTConfig(
        api_key="test-api-key",
        model="gpt-4",
        temperature=0.7,
        timeout=30
    )


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client"""
    client = Mock()
    client.chat = Mock()
    client.chat.completions = Mock()
    
    # Create a mock response
    mock_message = ChatCompletionMessage(
        role="assistant",
        content="Test response"
    )
    
    mock_choice = Choice(
        index=0,
        message=mock_message,
        finish_reason="stop"
    )
    
    mock_response = ChatCompletion(
        id="test-id",
        object="chat.completion",
        created=1234567890,
        model="gpt-4",
        choices=[mock_choice],
        usage=CompletionUsage(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30
        )
    )
    
    # Make create return async mock
    client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    return client


@pytest.fixture
async def gpt_service(mock_config, mock_openai_client):
    """Create a GPT service with mocked client"""
    service = GPTService(mock_config)
    
    # Patch the client initialization
    with patch.object(service, '_initialize_client', return_value=mock_openai_client):
        await service.initialize()
    
    return service


class TestGPTService:
    """Test GPT Service functionality"""
    
    async def test_initialization(self, mock_config):
        """Test service initialization"""
        service = GPTService(mock_config)
        
        assert service.config == mock_config
        assert not service.is_initialized
        
        # Mock the client initialization
        with patch.object(service, '_initialize_client', return_value=Mock()):
            await service.initialize()
        
        assert service.is_initialized
    
    async def test_initialization_from_env(self):
        """Test initialization from environment variables"""
        with patch.dict('os.environ', {
            'OPENAI_API_KEY': 'env-api-key',
            'GPT_MODEL': 'gpt-3.5-turbo',
            'GPT_TEMPERATURE': '0.5'
        }):
            service = GPTService()
            
            assert service.config.api_key == 'env-api-key'
            assert service.config.model == 'gpt-3.5-turbo'
            assert service.config.temperature == 0.5
    
    async def test_missing_api_key(self):
        """Test error when API key is missing"""
        config = GPTConfig(api_key=None)
        service = GPTService(config)
        
        with pytest.raises(ConfigurationError) as exc_info:
            await service.initialize()
        
        assert "API key is required" in str(exc_info.value)
    
    async def test_invalid_temperature(self):
        """Test error for invalid temperature"""
        config = GPTConfig(api_key="test", temperature=3.0)
        service = GPTService(config)
        
        with pytest.raises(ConfigurationError) as exc_info:
            await service.initialize()
        
        assert "Temperature must be between" in str(exc_info.value)
    
    async def test_complete_success(self, gpt_service):
        """Test successful completion"""
        result = await gpt_service.complete("Test prompt")
        
        assert result == "Test response"
        
        # Verify API was called correctly
        call_args = gpt_service.client.chat.completions.create.call_args
        assert call_args[1]['model'] == 'gpt-4'
        assert call_args[1]['messages'][0]['content'] == 'Test prompt'
        assert call_args[1]['temperature'] == 0.7
    
    async def test_complete_with_system_prompt(self, gpt_service):
        """Test completion with system prompt"""
        result = await gpt_service.complete(
            "User prompt",
            system_prompt="System instructions"
        )
        
        call_args = gpt_service.client.chat.completions.create.call_args
        messages = call_args[1]['messages']
        
        assert len(messages) == 2
        assert messages[0]['role'] == 'system'
        assert messages[0]['content'] == 'System instructions'
        assert messages[1]['role'] == 'user'
        assert messages[1]['content'] == 'User prompt'
    
    async def test_complete_empty_prompt(self, gpt_service):
        """Test error on empty prompt"""
        with pytest.raises(ValidationError) as exc_info:
            await gpt_service.complete("")
        
        assert "Prompt cannot be empty" in str(exc_info.value)
    
    async def test_complete_api_error(self, gpt_service):
        """Test handling of API errors"""
        # Make the API call fail
        gpt_service.client.chat.completions.create.side_effect = Exception("API Error")
        
        with pytest.raises(GPTServiceError) as exc_info:
            await gpt_service.complete("Test prompt")
        
        assert "Failed to generate completion" in str(exc_info.value)
        assert exc_info.value.original_error is not None
    
    async def test_complete_structured(self, gpt_service):
        """Test structured JSON completion"""
        # Mock a JSON response
        json_response = ChatCompletionMessage(
            role="assistant",
            content='{"key": "value", "number": 42}'
        )
        
        gpt_service.client.chat.completions.create.return_value.choices[0].message = json_response
        
        result = await gpt_service.complete_structured(
            "Generate JSON",
            {"key": "string", "number": "integer"}
        )
        
        assert result == {"key": "value", "number": 42}
        
        # Check temperature was lowered for structured output
        call_args = gpt_service.client.chat.completions.create.call_args
        assert call_args[1]['temperature'] == 0.3
    
    async def test_complete_structured_invalid_json(self, gpt_service):
        """Test error handling for invalid JSON response"""
        # Mock an invalid JSON response
        bad_response = ChatCompletionMessage(
            role="assistant",
            content='Not valid JSON'
        )
        
        gpt_service.client.chat.completions.create.return_value.choices[0].message = bad_response
        
        with pytest.raises(GPTServiceError) as exc_info:
            await gpt_service.complete_structured(
                "Generate JSON",
                {"key": "value"}
            )
        
        assert "Failed to parse JSON" in str(exc_info.value)
    
    async def test_validate_behavior_input(self, gpt_service):
        """Test behavior validation"""
        # Mock a positive validation
        gpt_service.client.chat.completions.create.return_value.choices[0].message.content = "ja"
        
        result = await gpt_service.validate_behavior_input("Mein Hund bellt")
        assert result is True
        
        # Mock a negative validation
        gpt_service.client.chat.completions.create.return_value.choices[0].message.content = "nein"
        
        result = await gpt_service.validate_behavior_input("Das Wetter ist schön")
        assert result is False
    
    async def test_health_check_healthy(self, gpt_service):
        """Test health check when service is healthy"""
        health = await gpt_service.health_check()
        
        assert health['healthy'] is True
        assert health['status'] == 'connected'
        assert 'response_time_ms' in health['details']
        assert health['details']['model'] == 'gpt-4'
    
    async def test_health_check_unhealthy(self, gpt_service):
        """Test health check when service is unhealthy"""
        # Make health check fail
        gpt_service.client.chat.completions.create.side_effect = Exception("Connection error")
        
        health = await gpt_service.health_check()
        
        assert health['healthy'] is False
        assert health['status'] == 'error'
        assert 'error' in health['details']
    
    async def test_get_metrics(self, gpt_service):
        """Test metrics collection"""
        metrics = gpt_service.get_metrics()
        
        assert metrics['service_name'] == 'GPTService'
        assert metrics['initialized'] is True
        assert metrics['model'] == 'gpt-4'
        assert metrics['temperature'] == 0.7
        assert metrics['timeout'] == 30


class TestGPTServiceFactory:
    """Test the factory function"""
    
    async def test_create_gpt_service(self):
        """Test service creation via factory"""
        with patch('src.services.gpt_service.AsyncOpenAI'):
            service = await create_gpt_service(
                api_key="test-key",
                model="gpt-3.5-turbo",
                temperature=0.5
            )
            
            assert isinstance(service, GPTService)
            assert service.is_initialized
            assert service.config.api_key == "test-key"
            assert service.config.model == "gpt-3.5-turbo"
            assert service.config.temperature == 0.5


# Integration tests (optional, skipped by default)
@pytest.mark.integration
class TestGPTServiceIntegration:
    """Integration tests that make real API calls"""
    
    @pytest.mark.skipif(
        not os.getenv("RUN_INTEGRATION_TESTS"),
        reason="Integration tests disabled"
    )
    async def test_real_completion(self):
        """Test with real OpenAI API"""
        service = await create_gpt_service()
        
        result = await service.complete(
            "Say hello in one word",
            temperature=0,
            max_tokens=5
        )
        
        assert len(result) > 0
        assert isinstance(result, str)