# tests/v2/agents/test_dog_agent.py
"""
Test suite for V2 DogAgent - focused on message formatting and response generation.

Tests cover:
- Message type routing
- Prompt-based responses
- Error handling
- Context validation
- GPT integration (mocked)
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from src.agents.dog_agent import DogAgent
from src.agents.base_agent import AgentContext, MessageType, V2AgentMessage
from src.core.prompt_manager import PromptManager, PromptType
from src.core.exceptions import V2AgentError, V2ValidationError


class TestDogAgentBasics:
    """Test basic DogAgent functionality"""
    
    def test_agent_initialization(self):
        """Test agent initializes with correct properties"""
        agent = DogAgent()
        
        assert agent.name == "Hund"
        assert agent.role == "dog"
        assert agent._default_temperature == 0.8
        assert MessageType.GREETING in agent.get_supported_message_types()
    
    def test_supported_message_types(self):
        """Test agent reports correct supported message types"""
        agent = DogAgent()
        supported = agent.get_supported_message_types()
        
        expected_types = [
            MessageType.GREETING,
            MessageType.RESPONSE,
            MessageType.QUESTION,
            MessageType.ERROR,
            MessageType.INSTRUCTION
        ]
        
        for msg_type in expected_types:
            assert msg_type in supported


class TestGreetingMessages:
    """Test greeting message generation"""
    
    @pytest.mark.asyncio
    async def test_greeting_format(self, mock_prompt_manager):
        """Test greeting returns two messages with correct format"""
        # Setup
        agent = DogAgent(prompt_manager=mock_prompt_manager)
        context = AgentContext(
            session_id="test-session",
            message_type=MessageType.GREETING
        )
        
        # Configure mock to return greeting prompts
        def mock_get_prompt(prompt_type, **kwargs):
            if prompt_type == PromptType.DOG_GREETING:
                return "Hallo! Ich bin dein Hund!"
            elif prompt_type == PromptType.DOG_GREETING_FOLLOWUP:
                return "Was möchtest du wissen?"
            return "Mock prompt"
        
        mock_prompt_manager.get_prompt.side_effect = mock_get_prompt
        
        # Execute
        messages = await agent.respond(context)
        
        # Verify
        assert len(messages) == 2
        assert messages[0].sender == "dog"
        assert "Hallo! Ich bin dein Hund!" in messages[0].text
        assert messages[0].message_type == MessageType.GREETING.value
        
        assert messages[1].sender == "dog"
        assert "Was möchtest du wissen?" in messages[1].text
        assert messages[1].message_type == MessageType.QUESTION.value
    
    @pytest.mark.asyncio
    async def test_greeting_uses_correct_prompts(self, mock_prompt_manager):
        """Test greeting uses the correct prompt types"""
        agent = DogAgent(prompt_manager=mock_prompt_manager)
        context = AgentContext(
            session_id="test-session",
            message_type=MessageType.GREETING
        )
        
        await agent.respond(context)
        
        # Verify prompts were called (at least once each)
        assert mock_prompt_manager.get_prompt.call_count >= 2


class TestResponseMessages:
    """Test response message generation with different modes"""
    
    @pytest.mark.asyncio
    async def test_perspective_only_response(self, mock_gpt_service, mock_prompt_manager):
        """Test dog perspective response generation"""
        # Setup
        agent = DogAgent(
            prompt_manager=mock_prompt_manager,
            gpt_service=mock_gpt_service
        )
        
        context = AgentContext(
            session_id="test-session",
            user_input="Mein Hund bellt",
            message_type=MessageType.RESPONSE,
            metadata={
                'response_mode': 'perspective_only',
                'match_data': 'Hund bellt territorial'
            }
        )
        
        # Configure mocks
        mock_gpt_service.complete.return_value = "Als Hund belle ich, weil ich mein Revier verteidige!"
        
        # Execute
        messages = await agent.respond(context)
        
        # Verify
        assert len(messages) == 1
        assert "belle ich" in messages[0].text
        assert messages[0].message_type == MessageType.RESPONSE.value
        
        # Verify GPT was called
        mock_gpt_service.complete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_diagnosis_response(self, mock_gpt_service, mock_prompt_manager):
        """Test diagnosis response format"""
        agent = DogAgent(
            prompt_manager=mock_prompt_manager,
            gpt_service=mock_gpt_service
        )
        
        context = AgentContext(
            session_id="test-session",
            message_type=MessageType.RESPONSE,
            metadata={
                'response_mode': 'diagnosis',
                'analysis_data': {
                    'primary_instinct': 'territorial',
                    'primary_description': 'Schutz des Reviers'
                }
            }
        )
        
        mock_gpt_service.complete.return_value = "Mein Territorialinstinkt ist hier aktiv."
        
        messages = await agent.respond(context)
        
        assert len(messages) == 1
        assert "Territorialinstinkt" in messages[0].text
    
    @pytest.mark.asyncio
    async def test_exercise_response(self, mock_prompt_manager):
        """Test exercise recommendation response"""
        agent = DogAgent(prompt_manager=mock_prompt_manager)
        
        context = AgentContext(
            session_id="test-session",
            message_type=MessageType.RESPONSE,
            metadata={
                'response_mode': 'exercise',
                'exercise_data': 'Übe täglich 10 Minuten Impulskontrolle'
            }
        )
        
        messages = await agent.respond(context)
        
        assert len(messages) == 1
        assert messages[0].text == "Übe täglich 10 Minuten Impulskontrolle"
    
    @pytest.mark.asyncio
    async def test_exercise_fallback(self, mock_prompt_manager):
        """Test exercise fallback when no data provided"""
        agent = DogAgent(prompt_manager=mock_prompt_manager)
        
        # Mock fallback prompt
        mock_prompt_manager.get_prompt.return_value = "Standard-Übung: Grundgehorsam"
        
        context = AgentContext(
            session_id="test-session",
            message_type=MessageType.RESPONSE,
            metadata={
                'response_mode': 'exercise',
                # No exercise_data - should use fallback
            }
        )
        
        messages = await agent.respond(context)
        
        assert len(messages) == 1
        assert messages[0].text == "Standard-Übung: Grundgehorsam"
        
        # Verify fallback prompt was requested
        mock_prompt_manager.get_prompt.assert_called_with(PromptType.DOG_FALLBACK_EXERCISE)


class TestQuestionMessages:
    """Test question message generation"""
    
    @pytest.mark.asyncio
    async def test_question_types(self, mock_prompt_manager):
        """Test different question types"""
        agent = DogAgent(prompt_manager=mock_prompt_manager)
        
        question_types = {
            'confirmation': "Möchtest du mehr erfahren?",
            'context': "Erzähl mir mehr über die Situation",
            'exercise': "Möchtest du eine Übung?",
            'restart': "Noch ein anderes Verhalten?"
        }
        
        for q_type, expected_text in question_types.items():
            mock_prompt_manager.get_prompt.return_value = expected_text
            
            context = AgentContext(
                session_id="test-session",
                message_type=MessageType.QUESTION,
                metadata={'question_type': q_type}
            )
            
            messages = await agent.respond(context)
            
            assert len(messages) == 1
            assert messages[0].text == expected_text
            assert messages[0].message_type == MessageType.QUESTION.value


class TestErrorHandling:
    """Test error message handling"""
    
    @pytest.mark.asyncio
    async def test_error_types(self, mock_prompt_manager):
        """Test different error types"""
        agent = DogAgent(prompt_manager=mock_prompt_manager)
        
        # Configure mock to return the dog technical error message
        mock_prompt_manager.get_prompt.return_value = "Wuff! Entschuldige, ich bin gerade etwas verwirrt. Kannst du es nochmal versuchen?"
        
        error_types = ['no_match', 'invalid_input', 'technical', 'general']
        
        for error_type in error_types:
            context = AgentContext(
                session_id="test-session",
                message_type=MessageType.ERROR,
                metadata={'error_type': error_type}
            )
            
            messages = await agent.respond(context)
            
            assert len(messages) == 1
            assert messages[0].message_type == MessageType.ERROR.value
            # The actual text depends on the prompt manager configuration
    
    @pytest.mark.asyncio
    async def test_exception_handling(self, mock_gpt_service, mock_prompt_manager):
        """Test agent handles exceptions gracefully"""
        agent = DogAgent(
            prompt_manager=mock_prompt_manager,
            gpt_service=mock_gpt_service
        )
        
        # Make GPT service fail
        mock_gpt_service.complete.side_effect = Exception("GPT failed")
        
        # Configure fallback error message
        mock_prompt_manager.get_prompt.return_value = "Wuff! Entschuldige, ich bin gerade etwas verwirrt. Kannst du es nochmal versuchen?"
        
        context = AgentContext(
            session_id="test-session",
            message_type=MessageType.RESPONSE,
            metadata={'response_mode': 'perspective_only', 'match_data': 'test'}
        )
        
        # Should return error message, not raise exception
        messages = await agent.respond(context)
        
        assert len(messages) == 1
        assert messages[0].message_type == MessageType.ERROR.value


class TestContextValidation:
    """Test context validation"""
    
    @pytest.mark.asyncio
    async def test_invalid_context_type(self):
        """Test agent handles invalid context type"""
        agent = DogAgent()
        
        # Pass invalid context - this should be caught by validate_context
        with pytest.raises(V2ValidationError):
            agent.validate_context("not a context object")
    
    @pytest.mark.asyncio
    async def test_missing_response_mode(self, mock_prompt_manager):
        """Test validation for response mode"""
        agent = DogAgent(prompt_manager=mock_prompt_manager)
        
        context = AgentContext(
            session_id="test-session",
            message_type=MessageType.RESPONSE
            # Missing response_mode in metadata
        )
        
        # Should handle gracefully by returning error message
        messages = await agent.respond(context)
        
        assert len(messages) == 1
        assert messages[0].message_type == MessageType.ERROR.value
        assert "verstehe" in messages[0].text  # Should contain friendly error
    
    @pytest.mark.asyncio
    async def test_unsupported_message_type(self, mock_prompt_manager):
        """Test handling of unsupported message type"""
        agent = DogAgent(prompt_manager=mock_prompt_manager)
        
        # Configure error message
        mock_prompt_manager.get_prompt.return_value = "Wuff! Entschuldige, ich bin gerade etwas verwirrt. Kannst du es nochmal versuchen?"
        
        context = AgentContext(
            session_id="test-session",
            message_type=MessageType.CONFIRMATION  # Not supported by DogAgent
        )
        
        messages = await agent.respond(context)
        
        assert len(messages) == 1
        assert messages[0].message_type == MessageType.ERROR.value


class TestHealthCheck:
    """Test agent health check functionality"""
    
    @pytest.mark.asyncio
    async def test_health_check_all_services_healthy(self, mock_gpt_service, mock_prompt_manager):
        """Test health check when all services are healthy"""
        agent = DogAgent(
            prompt_manager=mock_prompt_manager,
            gpt_service=mock_gpt_service
        )
        
        # Mock healthy services
        mock_gpt_service.health_check.return_value = {"healthy": True}
        mock_prompt_manager.get_prompt.return_value = "test prompt"
        
        health = await agent.health_check()
        
        assert health["agent"] == "Hund"
        assert health["role"] == "dog"
        assert "services" in health
    
    @pytest.mark.asyncio
    async def test_health_check_service_unhealthy(self, mock_gpt_service, mock_prompt_manager):
        """Test health check when a service is unhealthy"""
        agent = DogAgent(
            prompt_manager=mock_prompt_manager,
            gpt_service=mock_gpt_service
        )
        
        # Mock unhealthy GPT service
        mock_gpt_service.health_check.side_effect = Exception("Service down")
        mock_prompt_manager.get_prompt.return_value = "test prompt"
        
        health = await agent.health_check()
        
        assert health["healthy"] is False  # GPT is critical
        assert "error" in str(health["services"]["gpt_service"])


# Fixtures
@pytest.fixture
def mock_prompt_manager():
    """Mock PromptManager for testing"""
    mock = Mock(spec=PromptManager)
    mock.get_prompt.return_value = "Mock prompt"
    return mock


@pytest.fixture
def mock_gpt_service():
    """Mock GPTService for testing"""
    mock = AsyncMock()
    mock.complete.return_value = "Mock GPT response"
    mock.health_check.return_value = {"healthy": True}
    return mock


@pytest.fixture
def mock_weaviate_service():
    """Mock WeaviateService for testing"""
    mock = AsyncMock()
    mock.vector_search.return_value = [
        {"text": "Mock result", "score": 0.9}
    ]
    mock.health_check.return_value = {"healthy": True}
    return mock