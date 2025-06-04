# tests/v2/agents/test_companion_agent.py
"""
Test suite for V2 CompanionAgent - focused on feedback collection formatting.

Tests cover:
- Feedback question generation
- Response formatting
- Context validation
- Error handling
- Feedback sequence management
"""

import pytest
from unittest.mock import Mock, AsyncMock
from typing import List

from src.agents.companion_agent import CompanionAgent
from src.agents.base_agent import AgentContext, MessageType, V2AgentMessage
from src.core.prompt_manager import PromptManager, PromptType
from src.core.exceptions import V2AgentError, V2ValidationError


class TestCompanionAgentBasics:
    """Test basic CompanionAgent functionality"""
    
    def test_agent_initialization(self):
        """Test agent initializes with correct properties"""
        agent = CompanionAgent()
        
        assert agent.name == "Begleiter"
        assert agent.role == "companion"
        assert agent._default_temperature == 0.3  # Lower for consistency
        assert agent._feedback_question_count == 5
    
    def test_supported_message_types(self):
        """Test agent reports correct supported message types"""
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
    
    def test_question_count(self):
        """Test feedback question count is accessible"""
        agent = CompanionAgent()
        assert agent.get_feedback_question_count() == 5


class TestFeedbackQuestions:
    """Test feedback question generation"""
    
    @pytest.mark.asyncio
    async def test_feedback_intro(self, mock_prompt_manager):
        """Test feedback introduction message"""
        agent = CompanionAgent(prompt_manager=mock_prompt_manager)
        
        mock_prompt_manager.get_prompt.return_value = "Ich würde mich über Feedback freuen!"
        
        context = AgentContext(
            session_id="test-session",
            message_type=MessageType.GREETING
        )
        
        messages = await agent.respond(context)
        
        assert len(messages) == 1
        assert messages[0].text == "Ich würde mich über Feedback freuen!"
        assert messages[0].message_type == MessageType.GREETING.value
    
    @pytest.mark.asyncio
    async def test_feedback_questions_sequence(self, mock_prompt_manager):
        """Test all 5 feedback questions in sequence"""
        agent = CompanionAgent(prompt_manager=mock_prompt_manager)
        
        questions = [
            "Hat dir die Beratung geholfen?",
            "Wie fandest du die Hundeperspektive?",
            "War die Übung passend?",
            "Würdest du uns weiterempfehlen?",
            "Deine E-Mail für Rückfragen?"
        ]
        
        for i, expected_question in enumerate(questions, 1):
            mock_prompt_manager.get_prompt.return_value = expected_question
            
            context = AgentContext(
                session_id="test-session",
                message_type=MessageType.QUESTION,
                metadata={'question_number': i}
            )
            
            messages = await agent.respond(context)
            
            assert len(messages) == 1
            assert messages[0].text == expected_question
            assert messages[0].message_type == MessageType.QUESTION.value
    
    @pytest.mark.asyncio
    async def test_invalid_question_number(self, mock_prompt_manager):
        """Test handling of invalid question numbers"""
        agent = CompanionAgent(prompt_manager=mock_prompt_manager)
        
        # Configure error message
        mock_prompt_manager.get_prompt.return_value = "Es tut mir leid, es gab ein Problem. Bitte versuche es erneut."
        
        # Test question number too high
        context = AgentContext(
            session_id="test-session",
            message_type=MessageType.QUESTION,
            metadata={'question_number': 10}  # Only 5 questions exist
        )
        
        messages = await agent.respond(context)
        
        assert len(messages) == 1
        assert messages[0].message_type == MessageType.ERROR.value
    
    def test_validate_question_number(self):
        """Test question number validation utility"""
        agent = CompanionAgent()
        
        # Valid numbers
        assert agent.validate_question_number(1) is True
        assert agent.validate_question_number(5) is True
        
        # Invalid numbers
        assert agent.validate_question_number(0) is False
        assert agent.validate_question_number(6) is False
        assert agent.validate_question_number("not a number") is False


class TestResponseMessages:
    """Test response message formatting"""
    
    @pytest.mark.asyncio
    async def test_acknowledgment_response(self, mock_prompt_manager):
        """Test acknowledgment message formatting"""
        agent = CompanionAgent(prompt_manager=mock_prompt_manager)
        
        mock_prompt_manager.get_prompt.return_value = "Danke für deine Antwort!"
        
        context = AgentContext(
            session_id="test-session",
            user_input="Ja, sehr hilfreich",
            message_type=MessageType.RESPONSE,
            metadata={'response_mode': 'acknowledgment'}
        )
        
        messages = await agent.respond(context)
        
        assert len(messages) == 1
        assert messages[0].text == "Danke für deine Antwort!"
        assert messages[0].message_type == MessageType.RESPONSE.value
    
    @pytest.mark.asyncio
    async def test_completion_response_success(self, mock_prompt_manager):
        """Test completion message when save successful"""
        agent = CompanionAgent(prompt_manager=mock_prompt_manager)
        
        mock_prompt_manager.get_prompt.return_value = "Vielen Dank für dein Feedback! 🐾"
        
        context = AgentContext(
            session_id="test-session",
            message_type=MessageType.RESPONSE,
            metadata={
                'response_mode': 'completion',
                'save_success': True
            }
        )
        
        messages = await agent.respond(context)
        
        assert len(messages) == 1
        assert "Dank" in messages[0].text
        assert "🐾" in messages[0].text
        
        # Verify correct prompt was requested
        mock_prompt_manager.get_prompt.assert_called_with(
            PromptType.COMPANION_FEEDBACK_COMPLETE
        )
    
    @pytest.mark.asyncio
    async def test_completion_response_save_failed(self, mock_prompt_manager):
        """Test completion message when save failed"""
        agent = CompanionAgent(prompt_manager=mock_prompt_manager)
        
        mock_prompt_manager.get_prompt.return_value = "Danke! (Speichern fehlgeschlagen)"
        
        context = AgentContext(
            session_id="test-session",
            message_type=MessageType.RESPONSE,
            metadata={
                'response_mode': 'completion',
                'save_success': False
            }
        )
        
        messages = await agent.respond(context)
        
        assert len(messages) == 1
        
        # Verify fallback prompt was requested
        mock_prompt_manager.get_prompt.assert_called_with(
            PromptType.COMPANION_FEEDBACK_COMPLETE_NOSAVE
        )


class TestConfirmationMessages:
    """Test confirmation message formatting"""
    
    @pytest.mark.asyncio
    async def test_confirmation_types(self, mock_prompt_manager):
        """Test different confirmation types"""
        agent = CompanionAgent(prompt_manager=mock_prompt_manager)
        
        confirmation_types = {
            'proceed': "Möchtest du fortfahren?",
            'skip': "Möchtest du überspringen?",
            'other': "Möchtest du fortfahren?"  # Default
        }
        
        for conf_type, expected_text in confirmation_types.items():
            mock_prompt_manager.get_prompt.return_value = expected_text
            
            context = AgentContext(
                session_id="test-session",
                message_type=MessageType.CONFIRMATION,
                metadata={'confirmation_type': conf_type}
            )
            
            messages = await agent.respond(context)
            
            assert len(messages) == 1
            assert messages[0].text == expected_text
            assert messages[0].message_type == MessageType.CONFIRMATION.value


class TestErrorHandling:
    """Test error handling"""
    
    @pytest.mark.asyncio
    async def test_error_types(self, mock_prompt_manager):
        """Test different error types"""
        agent = CompanionAgent(prompt_manager=mock_prompt_manager)
        
        # Configure the mock to return companion-specific error message
        mock_prompt_manager.get_prompt.return_value = "Es tut mir leid, es gab ein Problem. Bitte versuche es erneut."
        
        error_types = ['invalid_feedback', 'save_failed', 'general']
        
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
    async def test_companion_specific_error_message(self, mock_prompt_manager):
        """Test companion-specific error formatting"""
        agent = CompanionAgent(prompt_manager=mock_prompt_manager)
        
        mock_prompt_manager.get_prompt.return_value = "Es gab ein Problem. Bitte versuche es erneut."
        
        error_msg = agent.create_error_message("Technical error")
        
        assert error_msg.sender == "companion"
        assert error_msg.message_type == MessageType.ERROR.value
        assert "Problem" in error_msg.text


class TestContextValidation:
    """Test context validation"""
    
    @pytest.mark.asyncio
    async def test_question_without_number(self, mock_prompt_manager):
        """Test validation when question number is missing"""
        agent = CompanionAgent(prompt_manager=mock_prompt_manager)
        
        # Configure error message
        mock_prompt_manager.get_prompt.return_value = "Es tut mir leid, es gab ein Problem. Bitte versuche es erneut."
        
        context = AgentContext(
            session_id="test-session",
            message_type=MessageType.QUESTION
            # Missing question_number
        )
        
        messages = await agent.respond(context)
        
        assert len(messages) == 1
        assert messages[0].message_type == MessageType.ERROR.value
    
    @pytest.mark.asyncio
    async def test_response_without_mode(self, mock_prompt_manager):
        """Test validation when response mode is missing"""
        agent = CompanionAgent(prompt_manager=mock_prompt_manager)
        
        # Configure error message
        mock_prompt_manager.get_prompt.return_value = "Es tut mir leid, es gab ein Problem. Bitte versuche es erneut."
        
        context = AgentContext(
            session_id="test-session",
            message_type=MessageType.RESPONSE
            # Missing response_mode
        )
        
        messages = await agent.respond(context)
        
        assert len(messages) == 1
        assert messages[0].message_type == MessageType.ERROR.value


class TestFeedbackSequenceHelper:
    """Test feedback sequence helper method"""
    
    @pytest.mark.asyncio
    async def test_create_feedback_sequence(self):
        """Test creating complete feedback sequence"""
        agent = CompanionAgent()
        
        contexts = await agent.create_feedback_sequence("test-session")
        
        # Should have intro + 5 questions + completion = 7 contexts
        assert len(contexts) == 7
        
        # Check intro
        assert contexts[0].message_type == MessageType.GREETING
        assert contexts[0].metadata['sequence_step'] == 'intro'
        
        # Check questions
        for i in range(1, 6):
            assert contexts[i].message_type == MessageType.QUESTION
            assert contexts[i].metadata['question_number'] == i
            assert contexts[i].metadata['sequence_step'] == f'question_{i}'
        
        # Check completion
        assert contexts[6].message_type == MessageType.RESPONSE
        assert contexts[6].metadata['response_mode'] == 'completion'
        assert contexts[6].metadata['sequence_step'] == 'completion'
    
    @pytest.mark.asyncio
    async def test_feedback_sequence_session_id(self):
        """Test all contexts have correct session ID"""
        agent = CompanionAgent()
        session_id = "unique-session-123"
        
        contexts = await agent.create_feedback_sequence(session_id)
        
        for context in contexts:
            assert context.session_id == session_id


# Fixtures
@pytest.fixture
def mock_prompt_manager():
    """Mock PromptManager for testing"""
    mock = Mock(spec=PromptManager)
    mock.get_prompt.return_value = "Mock prompt"
    return mock


@pytest.fixture
def mock_redis_service():
    """Mock RedisService for testing"""
    mock = AsyncMock()
    mock.set.return_value = True
    mock.get.return_value = None
    mock.health_check.return_value = {"healthy": True}
    return mock