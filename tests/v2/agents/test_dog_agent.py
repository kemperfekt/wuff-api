# tests/v2/agents/test_dog_agent.py
"""
Unit tests for V2 DogAgent - Mock-first approach.

Tests all message types, response modes, and error handling.
All external dependencies are mocked for fast, reliable tests.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from typing import Dict, Any

from src.v2.agents.dog_agent import DogAgent
from src.v2.agents.base_agent import AgentContext, MessageType
from src.models.flow_models import AgentMessage
from src.v2.core.prompt_manager import PromptType
from src.v2.core.exceptions import V2AgentError, V2ValidationError


class TestDogAgentInitialization:
    """Test DogAgent initialization and configuration"""
    
    def test_initialization_default(self):
        """Test default initialization"""
        agent = DogAgent()
        
        assert agent.name == "Hund"
        assert agent.role == "dog"
        assert agent._default_temperature == 0.8
        assert MessageType.GREETING in agent.get_supported_message_types()
        assert MessageType.RESPONSE in agent.get_supported_message_types()
    
    def test_initialization_with_services(self):
        """Test initialization with service injection"""
        mock_prompt_manager = Mock()
        mock_gpt_service = Mock()
        
        agent = DogAgent(
            prompt_manager=mock_prompt_manager,
            gpt_service=mock_gpt_service
        )
        
        assert agent.prompt_manager is mock_prompt_manager
        assert agent.gpt_service is mock_gpt_service
    
    def test_supported_message_types(self):
        """Test that all expected message types are supported"""
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


class TestDogAgentGreeting:
    """Test greeting message generation"""
    
    @pytest.fixture
    def agent_with_mocks(self):
        """Create DogAgent with mocked dependencies"""
        mock_prompt_manager = Mock()
        mock_prompt_manager.get_prompt.side_effect = [
            "Wuff! Schön, dass Du da bist.",
            "Was ist los? Beschreib mir bitte, was du beobachtet hast."
        ]
        
        return DogAgent(prompt_manager=mock_prompt_manager)
    
    @pytest.mark.asyncio
    async def test_greeting_message(self, agent_with_mocks):
        """Test greeting message generation"""
        context = AgentContext(
            session_id="test-123",
            message_type=MessageType.GREETING
        )
        
        messages = await agent_with_mocks.respond(context)
        
        assert len(messages) == 2
        assert messages[0].sender == "dog"
        assert "Wuff" in messages[0].text
        assert messages[1].sender == "dog"
        
        # Check that correct prompts were requested
        agent_with_mocks.prompt_manager.get_prompt.assert_any_call(PromptType.DOG_GREETING)
        agent_with_mocks.prompt_manager.get_prompt.assert_any_call(PromptType.DOG_GREETING_FOLLOWUP)


class TestDogAgentResponse:
    """Test response message generation"""
    
    @pytest.fixture
    def agent_with_mocks(self):
        """Create DogAgent with mocked dependencies"""
        mock_prompt_manager = Mock()
        mock_gpt_service = AsyncMock()
        mock_gpt_service.complete.return_value = "Als Hund fühle ich mich in dieser Situation..."
        
        return DogAgent(
            prompt_manager=mock_prompt_manager,
            gpt_service=mock_gpt_service
        )
    
    @pytest.mark.asyncio
    async def test_perspective_only_response(self, agent_with_mocks):
        """Test dog perspective response generation"""
        context = AgentContext(
            session_id="test-123",
            user_input="Mein Hund bellt",
            message_type=MessageType.RESPONSE,
            metadata={
                'response_mode': 'perspective_only',
                'analysis_data': {
                    'primary_instinct': 'territorial',
                    'primary_description': 'Territorial behavior',
                    'all_instincts': {
                        'jagd': 'Hunting instinct',
                        'rudel': 'Pack instinct',
                        'territorial': 'Territory protection',
                        'sexual': 'Mating instinct'
                    }
                }
            }
        )
        
        messages = await agent_with_mocks.respond(context)
        
        assert len(messages) == 1
        assert messages[0].sender == "dog"
        assert "Als Hund fühle" in messages[0].text
        
        # Check GPT service was called with correct parameters
        agent_with_mocks.gpt_service.complete.assert_called_once()
        call_args = agent_with_mocks.gpt_service.complete.call_args
        assert call_args.kwargs['temperature'] == 0.8
    
    @pytest.mark.asyncio
    async def test_diagnosis_response(self, agent_with_mocks):
        """Test diagnosis response generation"""
        context = AgentContext(
            session_id="test-123",
            message_type=MessageType.RESPONSE,
            metadata={
                'response_mode': 'diagnosis',
                'analysis_data': {
                    'primary_instinct': 'territorial',
                    'primary_description': 'Territorial behavior detected'
                }
            }
        )
        
        messages = await agent_with_mocks.respond(context)
        
        assert len(messages) == 1
        assert messages[0].sender == "dog"
        
        # Check that generate_text_with_prompt was called for diagnosis
        agent_with_mocks.gpt_service.complete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_exercise_response(self, agent_with_mocks):
        """Test exercise response generation"""
        context = AgentContext(
            session_id="test-123",
            message_type=MessageType.RESPONSE,
            metadata={
                'response_mode': 'exercise',
                'exercise_data': 'Übe mit deinem Hund Impulskontrolle.'
            }
        )
        
        messages = await agent_with_mocks.respond(context)
        
        assert len(messages) == 1
        assert messages[0].sender == "dog"
        assert "Impulskontrolle" in messages[0].text
    
    @pytest.mark.asyncio
    async def test_full_response(self, agent_with_mocks):
        """Test full response flow generation"""
        context = AgentContext(
            session_id="test-123",
            user_input="Mein Hund bellt",
            message_type=MessageType.RESPONSE,
            metadata={
                'response_mode': 'full_response',
                'analysis_data': {
                    'primary_instinct': 'territorial',
                    'all_instincts': {}
                },
                'exercise_data': 'Training exercise here'
            }
        )
        
        # Mock the followup question prompt
        agent_with_mocks.prompt_manager.get_prompt.return_value = "Gibt es ein weiteres Verhalten?"
        
        messages = await agent_with_mocks.respond(context)
        
        # Should have perspective + exercise + followup question
        assert len(messages) >= 2
        assert all(msg.sender == "dog" for msg in messages)


class TestDogAgentQuestions:
    """Test question message generation"""
    
    @pytest.fixture
    def agent_with_mocks(self):
        """Create DogAgent with mocked dependencies"""
        mock_prompt_manager = Mock()
        return DogAgent(prompt_manager=mock_prompt_manager)
    
    @pytest.mark.asyncio
    async def test_confirmation_question(self, agent_with_mocks):
        """Test confirmation question generation"""
        agent_with_mocks.prompt_manager.get_prompt.return_value = "Magst Du mehr erfahren?"
        
        context = AgentContext(
            session_id="test-123",
            message_type=MessageType.QUESTION,
            metadata={'question_type': 'confirmation'}
        )
        
        messages = await agent_with_mocks.respond(context)
        
        assert len(messages) == 1
        assert messages[0].sender == "dog"
        agent_with_mocks.prompt_manager.get_prompt.assert_called_with(PromptType.DOG_CONFIRMATION_QUESTION)
    
    @pytest.mark.asyncio
    async def test_context_question(self, agent_with_mocks):
        """Test context question generation"""
        agent_with_mocks.prompt_manager.get_prompt.return_value = "Beschreibe die Situation genauer."
        
        context = AgentContext(
            session_id="test-123",
            message_type=MessageType.QUESTION,
            metadata={'question_type': 'context'}
        )
        
        messages = await agent_with_mocks.respond(context)
        
        assert len(messages) == 1
        assert messages[0].sender == "dog"
        agent_with_mocks.prompt_manager.get_prompt.assert_called_with(PromptType.DOG_CONTEXT_QUESTION)


class TestDogAgentErrors:
    """Test error message generation"""
    
    @pytest.fixture
    def agent_with_mocks(self):
        """Create DogAgent with mocked dependencies"""
        mock_prompt_manager = Mock()
        return DogAgent(prompt_manager=mock_prompt_manager)
    
    @pytest.mark.asyncio
    async def test_no_match_error(self, agent_with_mocks):
        """Test no match error message"""
        agent_with_mocks.prompt_manager.get_prompt.return_value = "Dazu habe ich keine Informationen."
        
        context = AgentContext(
            session_id="test-123",
            message_type=MessageType.ERROR,
            metadata={'error_type': 'no_match'}
        )
        
        messages = await agent_with_mocks.respond(context)
        
        assert len(messages) == 1
        assert messages[0].sender == "dog"
        agent_with_mocks.prompt_manager.get_prompt.assert_called_with(PromptType.DOG_NO_MATCH_ERROR)
    
    @pytest.mark.asyncio
    async def test_technical_error(self, agent_with_mocks):
        """Test technical error message"""
        agent_with_mocks.prompt_manager.get_prompt.return_value = "Es tut mir leid, ich habe ein Problem."
        
        context = AgentContext(
            session_id="test-123",
            message_type=MessageType.ERROR,
            metadata={'error_type': 'technical'}
        )
        
        messages = await agent_with_mocks.respond(context)
        
        assert len(messages) == 1
        assert messages[0].sender == "dog"
        agent_with_mocks.prompt_manager.get_prompt.assert_called_with(PromptType.DOG_TECHNICAL_ERROR)
    
    @pytest.mark.asyncio
    async def test_create_error_message_override(self, agent_with_mocks):
        """Test custom error message creation"""
        agent_with_mocks.prompt_manager.get_prompt.return_value = "Wuff! Entschuldige!"
        
        error_msg = agent_with_mocks.create_error_message("Technical failure")
        
        assert error_msg.sender == "dog"
        assert "Wuff" in error_msg.text


class TestDogAgentInstructions:
    """Test instruction message generation"""
    
    @pytest.fixture
    def agent_with_mocks(self):
        """Create DogAgent with mocked dependencies"""
        mock_prompt_manager = Mock()
        return DogAgent(prompt_manager=mock_prompt_manager)
    
    @pytest.mark.asyncio
    async def test_describe_more_instruction(self, agent_with_mocks):
        """Test 'describe more' instruction"""
        agent_with_mocks.prompt_manager.get_prompt.return_value = "Kannst du das genauer beschreiben?"
        
        context = AgentContext(
            session_id="test-123",
            message_type=MessageType.INSTRUCTION,
            metadata={'instruction_type': 'describe_more'}
        )
        
        messages = await agent_with_mocks.respond(context)
        
        assert len(messages) == 1
        assert messages[0].sender == "dog"
        agent_with_mocks.prompt_manager.get_prompt.assert_called_with(PromptType.DOG_DESCRIBE_MORE)


class TestDogAgentValidation:
    """Test context validation"""
    
    def test_valid_context_validation(self):
        """Test validation of valid context"""
        agent = DogAgent()
        
        context = AgentContext(
            session_id="test-123",
            message_type=MessageType.RESPONSE,
            metadata={'response_mode': 'perspective_only'}
        )
        
        # Should not raise
        agent.validate_context(context)
    
    def test_missing_response_mode_validation(self):
        """Test validation fails for missing response_mode"""
        agent = DogAgent()
        
        context = AgentContext(
            session_id="test-123",
            message_type=MessageType.RESPONSE,
            metadata={}
        )
        
        with pytest.raises(V2ValidationError, match="response_mode"):
            agent.validate_context(context)
    
    def test_missing_analysis_data_validation(self):
        """Test validation fails for missing analysis_data in diagnosis mode"""
        agent = DogAgent()
        
        context = AgentContext(
            session_id="test-123",
            message_type=MessageType.RESPONSE,
            metadata={'response_mode': 'diagnosis'}
        )
        
        with pytest.raises(V2ValidationError, match="analysis_data"):
            agent.validate_context(context)
    
    def test_missing_exercise_data_validation(self):
        """Test validation fails for missing exercise_data in exercise mode"""
        agent = DogAgent()
        
        context = AgentContext(
            session_id="test-123",
            message_type=MessageType.RESPONSE,
            metadata={'response_mode': 'exercise'}
        )
        
        with pytest.raises(V2ValidationError, match="exercise_data"):
            agent.validate_context(context)


class TestDogAgentErrorHandling:
    """Test error handling and fallbacks"""
    
    @pytest.mark.asyncio
    async def test_unsupported_message_type(self):
        """Test handling of unsupported message type"""
        agent = DogAgent()
        
        context = AgentContext(
            session_id="test-123",
            message_type=MessageType.CONFIRMATION  # Not supported by DogAgent
        )
        
        messages = await agent.respond(context)
        
        # Should fall back to error message
        assert len(messages) == 1
        assert messages[0].sender == "dog"
    
    @pytest.mark.asyncio
    async def test_unknown_response_mode(self, agent_with_mocks=None):
        """Test handling of unknown response mode"""
        if agent_with_mocks is None:
            agent_with_mocks = DogAgent()
        
        context = AgentContext(
            session_id="test-123",
            message_type=MessageType.RESPONSE,
            metadata={'response_mode': 'unknown_mode'}
        )
        
        messages = await agent_with_mocks.respond(context)
        
        # Should fall back to error message
        assert len(messages) == 1
        assert messages[0].sender == "dog"
    
    @pytest.mark.asyncio
    async def test_gpt_service_failure(self):
        """Test handling of GPT service failure"""
        mock_gpt_service = AsyncMock()
        mock_gpt_service.complete.side_effect = Exception("GPT API error")
        
        agent = DogAgent(gpt_service=mock_gpt_service)
        
        context = AgentContext(
            session_id="test-123",
            message_type=MessageType.RESPONSE,
            metadata={
                'response_mode': 'perspective_only',
                'analysis_data': {'primary_instinct': 'test'}
            }
        )
        
        messages = await agent.respond(context)
        
        # Should fall back to error message
        assert len(messages) == 1
        assert messages[0].sender == "dog"


class TestDogAgentHealthCheck:
    """Test health check functionality"""
    
    @pytest.mark.asyncio
    async def test_health_check_healthy(self):
        """Test health check with healthy services"""
        mock_prompt_manager = Mock()
        mock_prompt_manager.get_prompt.return_value = "test"
        
        mock_gpt_service = AsyncMock()
        mock_gpt_service.health_check.return_value = {"healthy": True}
        
        agent = DogAgent(
            prompt_manager=mock_prompt_manager,
            gpt_service=mock_gpt_service
        )
        
        health = await agent.health_check()
        
        assert health["healthy"] is True
        assert health["agent"] == "Hund"
        assert "prompt_manager" in health["services"]
        assert "gpt_service" in health["services"]
    
    @pytest.mark.asyncio
    async def test_health_check_unhealthy_gpt(self):
        """Test health check with unhealthy GPT service"""
        mock_prompt_manager = Mock()
        mock_prompt_manager.get_prompt.return_value = "test"
        
        mock_gpt_service = AsyncMock()
        mock_gpt_service.health_check.side_effect = Exception("Service down")
        
        agent = DogAgent(
            prompt_manager=mock_prompt_manager,
            gpt_service=mock_gpt_service
        )
        
        health = await agent.health_check()
        
        assert health["healthy"] is False  # GPT is critical
        assert "error" in health["services"]["gpt_service"]


# Fixtures for shared test data
@pytest.fixture
def sample_analysis_data():
    """Sample analysis data for testing"""
    return {
        'primary_instinct': 'territorial',
        'primary_description': 'The dog is protecting its territory',
        'all_instincts': {
            'jagd': 'Hunting behavior description',
            'rudel': 'Pack behavior description', 
            'territorial': 'Territorial behavior description',
            'sexual': 'Mating behavior description'
        },
        'exercise': 'Practice boundary training with your dog',
        'confidence': 0.8
    }


@pytest.fixture
def sample_context():
    """Sample context for testing"""
    return AgentContext(
        session_id="test-session-123",
        user_input="Mein Hund bellt ständig",
        message_type=MessageType.RESPONSE,
        metadata={
            'response_mode': 'perspective_only',
            'analysis_data': {
                'primary_instinct': 'territorial'
            }
        }
    )


if __name__ == "__main__":
    # Run tests with: python -m pytest tests/v2/agents/test_dog_agent.py -v
    pytest.main([__file__, "-v"])