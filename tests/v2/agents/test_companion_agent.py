# tests/v2/agents/test_companion_agent.py
"""
Unit tests for V2 CompanionAgent - Mock-first approach.

Tests all feedback message types, question sequences, and error handling.
All external dependencies are mocked for fast, reliable tests.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from typing import Dict, Any

from src.v2.agents.companion_agent import CompanionAgent
from src.v2.agents.base_agent import AgentContext, MessageType
from src.models.flow_models import AgentMessage
from src.v2.core.prompt_manager import PromptType
from src.v2.core.exceptions import V2AgentError, V2ValidationError


class TestCompanionAgentInitialization:
    """Test CompanionAgent initialization and configuration"""
    
    def test_initialization_default(self):
        """Test default initialization"""
        agent = CompanionAgent()
        
        assert agent.name == "Begleiter"
        assert agent.role == "companion"
        assert agent._default_temperature == 0.3  # More consistent for feedback
        assert agent._feedback_question_count == 5
        assert MessageType.GREETING in agent.get_supported_message_types()
        assert MessageType.QUESTION in agent.get_supported_message_types()
    
    def test_initialization_with_services(self):
        """Test initialization with service injection"""
        mock_prompt_manager = Mock()
        mock_redis_service = Mock()
        
        agent = CompanionAgent(
            prompt_manager=mock_prompt_manager,
            redis_service=mock_redis_service
        )
        
        assert agent.prompt_manager is mock_prompt_manager
        assert agent.redis_service is mock_redis_service
    
    def test_supported_message_types(self):
        """Test that all expected message types are supported"""
        agent = CompanionAgent()
        supported = agent.get_supported_message_types()
        
        expected_types = [
            MessageType.GREETING,
            MessageType.QUESTION,
            MessageType.RESPONSE,
            MessageType.CONFIRMATION,
            MessageType.ERROR
        ]
        
        for msg_type in expected_types:
            assert msg_type in supported
    
    def test_feedback_question_count(self):
        """Test feedback question count configuration"""
        agent = CompanionAgent()
        
        assert agent.get_feedback_question_count() == 5
        assert agent.validate_question_number(1) is True
        assert agent.validate_question_number(5) is True
        assert agent.validate_question_number(0) is False
        assert agent.validate_question_number(6) is False


class TestCompanionAgentGreeting:
    """Test feedback introduction message generation"""
    
    @pytest.fixture
    def agent_with_mocks(self):
        """Create CompanionAgent with mocked dependencies"""
        mock_prompt_manager = Mock()
        mock_prompt_manager.get_prompt.return_value = "Ich würde mich freuen, wenn du mir noch ein kurzes Feedback gibst."
        
        return CompanionAgent(prompt_manager=mock_prompt_manager)
    
    @pytest.mark.asyncio
    async def test_feedback_intro_message(self, agent_with_mocks):
        """Test feedback introduction message generation"""
        context = AgentContext(
            session_id="test-123",
            message_type=MessageType.GREETING
        )
        
        messages = await agent_with_mocks.respond(context)
        
        assert len(messages) == 1
        assert messages[0].sender == "companion"
        assert "Feedback" in messages[0].text
        
        # Check that correct prompt was requested
        agent_with_mocks.prompt_manager.get_prompt.assert_called_with(PromptType.COMPANION_FEEDBACK_INTRO)


class TestCompanionAgentQuestions:
    """Test feedback question generation"""
    
    @pytest.fixture
    def agent_with_mocks(self):
        """Create CompanionAgent with mocked dependencies"""
        mock_prompt_manager = Mock()
        return CompanionAgent(prompt_manager=mock_prompt_manager)
    
    @pytest.mark.asyncio
    async def test_feedback_question_1(self, agent_with_mocks):
        """Test first feedback question"""
        agent_with_mocks.prompt_manager.get_prompt.return_value = "Hast Du das Gefühl, dass Dir die Beratung weitergeholfen hat?"
        
        context = AgentContext(
            session_id="test-123",
            message_type=MessageType.QUESTION,
            metadata={'question_number': 1}
        )
        
        messages = await agent_with_mocks.respond(context)
        
        assert len(messages) == 1
        assert messages[0].sender == "companion"
        agent_with_mocks.prompt_manager.get_prompt.assert_called_with(PromptType.COMPANION_FEEDBACK_Q1)
    
    @pytest.mark.asyncio
    async def test_feedback_question_3(self, agent_with_mocks):
        """Test third feedback question"""
        agent_with_mocks.prompt_manager.get_prompt.return_value = "Was denkst Du über die vorgeschlagene Übung?"
        
        context = AgentContext(
            session_id="test-123",
            message_type=MessageType.QUESTION,
            metadata={'question_number': 3}
        )
        
        messages = await agent_with_mocks.respond(context)
        
        assert len(messages) == 1
        assert messages[0].sender == "companion"
        agent_with_mocks.prompt_manager.get_prompt.assert_called_with(PromptType.COMPANION_FEEDBACK_Q3)
    
    @pytest.mark.asyncio
    async def test_feedback_question_5_final(self, agent_with_mocks):
        """Test final feedback question (GDPR-compliant)"""
        agent_with_mocks.prompt_manager.get_prompt.return_value = "Optional: Deine E-Mail für eventuelle Rückfragen."
        
        context = AgentContext(
            session_id="test-123",
            message_type=MessageType.QUESTION,
            metadata={'question_number': 5}
        )
        
        messages = await agent_with_mocks.respond(context)
        
        assert len(messages) == 1
        assert messages[0].sender == "companion"
        agent_with_mocks.prompt_manager.get_prompt.assert_called_with(PromptType.COMPANION_FEEDBACK_Q5)
    
    @pytest.mark.asyncio
    async def test_invalid_question_number(self, agent_with_mocks):
        """Test handling of invalid question number"""
        context = AgentContext(
            session_id="test-123",
            message_type=MessageType.QUESTION,
            metadata={'question_number': 7}  # Invalid - only 1-5 supported
        )
        
        messages = await agent_with_mocks.respond(context)
        
        # Should fall back to error message
        assert len(messages) == 1
        assert messages[0].sender == "companion"


class TestCompanionAgentResponses:
    """Test feedback response message generation"""
    
    @pytest.fixture
    def agent_with_mocks(self):
        """Create CompanionAgent with mocked dependencies"""
        mock_prompt_manager = Mock()
        return CompanionAgent(prompt_manager=mock_prompt_manager)
    
    @pytest.mark.asyncio
    async def test_acknowledgment_response(self, agent_with_mocks):
        """Test acknowledgment response between questions"""
        agent_with_mocks.prompt_manager.get_prompt.return_value = "Danke für deine Antwort."
        
        context = AgentContext(
            session_id="test-123",
            message_type=MessageType.RESPONSE,
            metadata={'response_mode': 'acknowledgment'}
        )
        
        messages = await agent_with_mocks.respond(context)
        
        assert len(messages) == 1
        assert messages[0].sender == "companion"
        agent_with_mocks.prompt_manager.get_prompt.assert_called_with(PromptType.COMPANION_FEEDBACK_ACK)
    
    @pytest.mark.asyncio
    async def test_completion_response_success(self, agent_with_mocks):
        """Test completion response when feedback saved successfully"""
        agent_with_mocks.prompt_manager.get_prompt.return_value = "Danke für Dein Feedback! 🐾"
        
        context = AgentContext(
            session_id="test-123",
            message_type=MessageType.RESPONSE,
            metadata={
                'response_mode': 'completion',
                'save_success': True
            }
        )
        
        messages = await agent_with_mocks.respond(context)
        
        assert len(messages) == 1
        assert messages[0].sender == "companion"
        agent_with_mocks.prompt_manager.get_prompt.assert_called_with(PromptType.COMPANION_FEEDBACK_COMPLETE)
    
    @pytest.mark.asyncio
    async def test_completion_response_save_failed(self, agent_with_mocks):
        """Test completion response when feedback save failed"""
        agent_with_mocks.prompt_manager.get_prompt.return_value = "Danke für dein Feedback! Es konnte leider nicht gespeichert werden."
        
        context = AgentContext(
            session_id="test-123",
            message_type=MessageType.RESPONSE,
            metadata={
                'response_mode': 'completion',
                'save_success': False
            }
        )
        
        messages = await agent_with_mocks.respond(context)
        
        assert len(messages) == 1
        assert messages[0].sender == "companion"
        agent_with_mocks.prompt_manager.get_prompt.assert_called_with(PromptType.COMPANION_FEEDBACK_COMPLETE_NOSAVE)
    
    @pytest.mark.asyncio
    async def test_progress_response(self, agent_with_mocks):
        """Test progress response (currently returns empty list)"""
        context = AgentContext(
            session_id="test-123",
            message_type=MessageType.RESPONSE,
            metadata={'response_mode': 'progress'}
        )
        
        messages = await agent_with_mocks.respond(context)
        
        # Currently progress messages are empty - this could be enhanced later
        assert len(messages) == 0


class TestCompanionAgentConfirmations:
    """Test confirmation message generation"""
    
    @pytest.fixture
    def agent_with_mocks(self):
        """Create CompanionAgent with mocked dependencies"""
        mock_prompt_manager = Mock()
        return CompanionAgent(prompt_manager=mock_prompt_manager)
    
    @pytest.mark.asyncio
    async def test_proceed_confirmation(self, agent_with_mocks):
        """Test proceed confirmation message"""
        agent_with_mocks.prompt_manager.get_prompt.return_value = "Möchtest du fortfahren?"
        
        context = AgentContext(
            session_id="test-123",
            message_type=MessageType.CONFIRMATION,
            metadata={'confirmation_type': 'proceed'}
        )
        
        messages = await agent_with_mocks.respond(context)
        
        assert len(messages) == 1
        assert messages[0].sender == "companion"
        agent_with_mocks.prompt_manager.get_prompt.assert_called_with(PromptType.COMPANION_PROCEED_CONFIRMATION)
    
    @pytest.mark.asyncio
    async def test_skip_confirmation(self, agent_with_mocks):
        """Test skip confirmation message"""
        agent_with_mocks.prompt_manager.get_prompt.return_value = "Möchtest du überspringen?"
        
        context = AgentContext(
            session_id="test-123",
            message_type=MessageType.CONFIRMATION,
            metadata={'confirmation_type': 'skip'}
        )
        
        messages = await agent_with_mocks.respond(context)
        
        assert len(messages) == 1
        assert messages[0].sender == "companion"
        agent_with_mocks.prompt_manager.get_prompt.assert_called_with(PromptType.COMPANION_SKIP_CONFIRMATION)


class TestCompanionAgentErrors:
    """Test error message generation"""
    
    @pytest.fixture
    def agent_with_mocks(self):
        """Create CompanionAgent with mocked dependencies"""
        mock_prompt_manager = Mock()
        return CompanionAgent(prompt_manager=mock_prompt_manager)
    
    @pytest.mark.asyncio
    async def test_invalid_feedback_error(self, agent_with_mocks):
        """Test invalid feedback error message"""
        agent_with_mocks.prompt_manager.get_prompt.return_value = "Bitte gib eine gültige Antwort."
        
        context = AgentContext(
            session_id="test-123",
            message_type=MessageType.ERROR,
            metadata={'error_type': 'invalid_feedback'}
        )
        
        messages = await agent_with_mocks.respond(context)
        
        assert len(messages) == 1
        assert messages[0].sender == "companion"
        agent_with_mocks.prompt_manager.get_prompt.assert_called_with(PromptType.COMPANION_INVALID_FEEDBACK_ERROR)
    
    @pytest.mark.asyncio
    async def test_save_failed_error(self, agent_with_mocks):
        """Test save failed error message"""
        agent_with_mocks.prompt_manager.get_prompt.return_value = "Feedback konnte nicht gespeichert werden."
        
        context = AgentContext(
            session_id="test-123",
            message_type=MessageType.ERROR,
            metadata={'error_type': 'save_failed'}
        )
        
        messages = await agent_with_mocks.respond(context)
        
        assert len(messages) == 1
        assert messages[0].sender == "companion"
        agent_with_mocks.prompt_manager.get_prompt.assert_called_with(PromptType.COMPANION_SAVE_ERROR)
    
    @pytest.mark.asyncio
    async def test_create_error_message_override(self, agent_with_mocks):
        """Test custom error message creation"""
        agent_with_mocks.prompt_manager.get_prompt.return_value = "Es gab ein Problem. Bitte versuche es erneut."
        
        error_msg = agent_with_mocks.create_error_message("Technical failure")
        
        assert error_msg.sender == "companion"
        assert "Problem" in error_msg.text


class TestCompanionAgentValidation:
    """Test context validation"""
    
    def test_valid_question_context_validation(self):
        """Test validation of valid question context"""
        agent = CompanionAgent()
        
        context = AgentContext(
            session_id="test-123",
            message_type=MessageType.QUESTION,
            metadata={'question_number': 3}
        )
        
        # Should not raise
        agent.validate_context(context)
    
    def test_missing_question_number_validation(self):
        """Test validation fails for missing question_number"""
        agent = CompanionAgent()
        
        context = AgentContext(
            session_id="test-123",
            message_type=MessageType.QUESTION,
            metadata={}
        )
        
        with pytest.raises(V2ValidationError, match="question_number"):
            agent.validate_context(context)
    
    def test_invalid_question_number_validation(self):
        """Test validation fails for invalid question_number"""
        agent = CompanionAgent()
        
        context = AgentContext(
            session_id="test-123",
            message_type=MessageType.QUESTION,
            metadata={'question_number': 7}  # Only 1-5 are valid
        )
        
        with pytest.raises(V2ValidationError, match="Invalid question number"):
            agent.validate_context(context)
    
    def test_missing_response_mode_validation(self):
        """Test validation fails for missing response_mode"""
        agent = CompanionAgent()
        
        context = AgentContext(
            session_id="test-123",
            message_type=MessageType.RESPONSE,
            metadata={}
        )
        
        with pytest.raises(V2ValidationError, match="response_mode"):
            agent.validate_context(context)
    
    def test_valid_response_context_validation(self):
        """Test validation of valid response context"""
        agent = CompanionAgent()
        
        context = AgentContext(
            session_id="test-123",
            message_type=MessageType.RESPONSE,
            metadata={'response_mode': 'completion'}
        )
        
        # Should not raise
        agent.validate_context(context)


class TestCompanionAgentUtilities:
    """Test utility methods"""
    
    @pytest.mark.asyncio
    async def test_create_feedback_sequence(self):
        """Test feedback sequence generation utility"""
        agent = CompanionAgent()
        
        contexts = await agent.create_feedback_sequence("test-session")
        
        # Should have intro + 5 questions + completion = 7 contexts
        assert len(contexts) == 7
        
        # First should be intro (greeting)
        assert contexts[0].message_type == MessageType.GREETING
        assert contexts[0].metadata['sequence_step'] == 'intro'
        
        # Next 5 should be questions
        for i in range(1, 6):
            assert contexts[i].message_type == MessageType.QUESTION
            assert contexts[i].metadata['question_number'] == i
            assert contexts[i].metadata['sequence_step'] == f'question_{i}'
        
        # Last should be completion
        assert contexts[6].message_type == MessageType.RESPONSE
        assert contexts[6].metadata['response_mode'] == 'completion'
        assert contexts[6].metadata['sequence_step'] == 'completion'
        
        # All should have same session_id
        for context in contexts:
            assert context.session_id == "test-session"
    
    def test_question_number_validation_utility(self):
        """Test question number validation utility"""
        agent = CompanionAgent()
        
        # Valid question numbers
        for i in range(1, 6):
            assert agent.validate_question_number(i) is True
        
        # Invalid question numbers
        invalid_numbers = [0, -1, 6, 7, 10, "1", None]
        for num in invalid_numbers:
            assert agent.validate_question_number(num) is False
    
    def test_get_feedback_question_private_method(self):
        """Test private _get_feedback_question method"""
        mock_prompt_manager = Mock()
        mock_prompt_manager.get_prompt.return_value = "Test question"
        
        agent = CompanionAgent(prompt_manager=mock_prompt_manager)
        
        # Test valid question numbers
        for i in range(1, 6):
            question = agent._get_feedback_question(i)
            assert question == "Test question"
        
        # Test invalid question number
        with pytest.raises(V2AgentError, match="No prompt found"):
            agent._get_feedback_question(7)


class TestCompanionAgentErrorHandling:
    """Test error handling and fallbacks"""
    
    @pytest.mark.asyncio
    async def test_unsupported_message_type(self):
        """Test handling of unsupported message type"""
        agent = CompanionAgent()
        
        context = AgentContext(
            session_id="test-123",
            message_type=MessageType.INSTRUCTION  # Not supported by CompanionAgent
        )
        
        messages = await agent.respond(context)
        
        # Should fall back to error message
        assert len(messages) == 1
        assert messages[0].sender == "companion"
    
    @pytest.mark.asyncio
    async def test_unknown_response_mode(self):
        """Test handling of unknown response mode"""
        agent = CompanionAgent()
        
        context = AgentContext(
            session_id="test-123",
            message_type=MessageType.RESPONSE,
            metadata={'response_mode': 'unknown_mode'}
        )
        
        messages = await agent.respond(context)
        
        # Should fall back to error message
        assert len(messages) == 1
        assert messages[0].sender == "companion"
    
    @pytest.mark.asyncio
    async def test_prompt_manager_failure(self):
        """Test handling of prompt manager failure"""
        mock_prompt_manager = Mock()
        mock_prompt_manager.get_prompt.side_effect = Exception("Prompt not found")
        
        agent = CompanionAgent(prompt_manager=mock_prompt_manager)
        
        context = AgentContext(
            session_id="test-123",
            message_type=MessageType.GREETING
        )
        
        messages = await agent.respond(context)
        
        # Should fall back to error message
        assert len(messages) == 1
        assert messages[0].sender == "companion"


class TestCompanionAgentHealthCheck:
    """Test health check functionality"""
    
    @pytest.mark.asyncio
    async def test_health_check_healthy(self):
        """Test health check with healthy services"""
        mock_prompt_manager = Mock()
        mock_prompt_manager.get_prompt.return_value = "test"
        
        mock_redis_service = AsyncMock()
        mock_redis_service.health_check.return_value = {"healthy": True}
        
        agent = CompanionAgent(
            prompt_manager=mock_prompt_manager,
            redis_service=mock_redis_service
        )
        
        health = await agent.health_check()
        
        assert health["healthy"] is True
        assert health["agent"] == "Begleiter"
        assert "prompt_manager" in health["services"]
        assert "redis_service" in health["services"]
    
    @pytest.mark.asyncio
    async def test_health_check_unhealthy_redis(self):
        """Test health check with unhealthy Redis service"""
        mock_prompt_manager = Mock()
        mock_prompt_manager.get_prompt.return_value = "test"
        
        mock_redis_service = AsyncMock()
        mock_redis_service.health_check.side_effect = Exception("Redis connection failed")
        
        agent = CompanionAgent(
            prompt_manager=mock_prompt_manager,
            redis_service=mock_redis_service
        )
        
        health = await agent.health_check()
        
        # Redis is not critical for CompanionAgent, so overall health should still be true
        assert health["healthy"] is True  # Different from DogAgent where GPT is critical
        assert "error" in health["services"]["redis_service"]


class TestCompanionAgentIntegration:
    """Integration-style tests for complete feedback flows"""
    
    @pytest.mark.asyncio
    async def test_complete_feedback_flow_simulation(self):
        """Test simulated complete feedback flow"""
        mock_prompt_manager = Mock()
        
        # Set up prompt responses for a complete flow
        prompt_responses = {
            PromptType.COMPANION_FEEDBACK_INTRO: "Feedback bitte!",
            PromptType.COMPANION_FEEDBACK_Q1: "Frage 1?",
            PromptType.COMPANION_FEEDBACK_ACK: "Danke.",
            PromptType.COMPANION_FEEDBACK_COMPLETE: "Fertig! 🐾"
        }
        
        def get_prompt_side_effect(prompt_type, **kwargs):
            return prompt_responses.get(prompt_type, f"Mock: {prompt_type}")
        
        mock_prompt_manager.get_prompt.side_effect = get_prompt_side_effect
        
        agent = CompanionAgent(prompt_manager=mock_prompt_manager)
        
        # 1. Intro
        intro_context = AgentContext(
            session_id="test-flow",
            message_type=MessageType.GREETING
        )
        intro_messages = await agent.respond(intro_context)
        assert len(intro_messages) == 1
        assert "Feedback" in intro_messages[0].text
        
        # 2. Question 1
        q1_context = AgentContext(
            session_id="test-flow",
            message_type=MessageType.QUESTION,
            metadata={'question_number': 1}
        )
        q1_messages = await agent.respond(q1_context)
        assert len(q1_messages) == 1
        assert "Frage 1" in q1_messages[0].text
        
        # 3. Acknowledgment
        ack_context = AgentContext(
            session_id="test-flow",
            message_type=MessageType.RESPONSE,
            metadata={'response_mode': 'acknowledgment'}
        )
        ack_messages = await agent.respond(ack_context)
        assert len(ack_messages) == 1
        assert "Danke" in ack_messages[0].text
        
        # 4. Completion
        completion_context = AgentContext(
            session_id="test-flow",
            message_type=MessageType.RESPONSE,
            metadata={
                'response_mode': 'completion',
                'save_success': True
            }
        )
        completion_messages = await agent.respond(completion_context)
        assert len(completion_messages) == 1
        assert "🐾" in completion_messages[0].text


# Fixtures for shared test data
@pytest.fixture
def sample_feedback_responses():
    """Sample feedback responses for testing"""
    return [
        "Ja, sehr hilfreich!",
        "Die Hundeperspektive war interessant",
        "Die Übung passt gut zu meiner Situation",
        "8 von 10",
        "test@example.com"
    ]


if __name__ == "__main__":
    # Run tests with: python -m pytest tests/v2/agents/test_companion_agent.py -v
    pytest.main([__file__, "-v"])