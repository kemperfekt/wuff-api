# tests/v2/agents/conftest.py
"""
Shared fixtures for V2 agent tests.

Provides common mock objects and test data for both DogAgent and CompanionAgent tests.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any

from src.v2.agents.base_agent import AgentContext, MessageType
from src.v2.core.prompt_manager import PromptType


@pytest.fixture
def mock_prompt_manager():
    """Mock PromptManager with common responses for testing"""
    mock = Mock()
    
    # Default responses for different prompt types
    prompt_responses = {
        # Dog prompts
        PromptType.DOG_GREETING: "Wuff! Schön, dass Du da bist.",
        PromptType.DOG_GREETING_FOLLOWUP: "Was ist los? Beschreib mir bitte, was du beobachtet hast.",
        PromptType.DOG_CONFIRMATION_QUESTION: "Magst Du mehr erfahren, warum ich mich so verhalte?",
        PromptType.DOG_CONTEXT_QUESTION: "Gut, dann brauche ich ein bisschen mehr Informationen.",
        PromptType.DOG_EXERCISE_QUESTION: "Möchtest du eine Lernaufgabe, die dir helfen kann?",
        PromptType.DOG_RESTART_QUESTION: "Möchtest du ein weiteres Hundeverhalten verstehen?",
        PromptType.DOG_NO_MATCH_ERROR: "Hmm, zu diesem Verhalten habe ich leider noch keine Antwort.",
        PromptType.DOG_INVALID_INPUT_ERROR: "Kannst Du das Verhalten bitte etwas ausführlicher beschreiben?",
        PromptType.DOG_TECHNICAL_ERROR: "Wuff! Entschuldige, ich bin gerade etwas verwirrt.",
        PromptType.DOG_DESCRIBE_MORE: "Kannst du mir mehr erzählen?",
        PromptType.DOG_BE_SPECIFIC: "Kannst Du das bitte genauer beschreiben?",
        PromptType.DOG_ANOTHER_BEHAVIOR_QUESTION: "Gibt es ein weiteres Verhalten?",
        PromptType.DOG_FALLBACK_EXERCISE: "Eine hilfreiche Übung wäre, klare Grenzen zu setzen.",
        
        # Companion prompts
        PromptType.COMPANION_FEEDBACK_INTRO: "Ich würde mich freuen, wenn du mir noch ein kurzes Feedback gibst.",
        PromptType.COMPANION_FEEDBACK_Q1: "Hast Du das Gefühl, dass Dir die Beratung weitergeholfen hat?",
        PromptType.COMPANION_FEEDBACK_Q2: "Wie fandest Du die Sichtweise des Hundes?",
        PromptType.COMPANION_FEEDBACK_Q3: "Was denkst Du über die vorgeschlagene Übung?",
        PromptType.COMPANION_FEEDBACK_Q4: "Auf einer Skala von 0-10: Wie wahrscheinlich empfiehlst Du uns weiter?",
        PromptType.COMPANION_FEEDBACK_Q5: "Optional: Deine E-Mail für eventuelle Rückfragen.",
        PromptType.COMPANION_FEEDBACK_ACK: "Danke für deine Antwort.",
        PromptType.COMPANION_FEEDBACK_COMPLETE: "Danke für Dein Feedback! 🐾",
        PromptType.COMPANION_FEEDBACK_COMPLETE_NOSAVE: "Danke für dein Feedback! Es konnte leider nicht gespeichert werden.",
        PromptType.COMPANION_PROCEED_CONFIRMATION: "Möchtest du fortfahren?",
        PromptType.COMPANION_SKIP_CONFIRMATION: "Möchtest du überspringen?",
        PromptType.COMPANION_INVALID_FEEDBACK_ERROR: "Bitte gib eine gültige Antwort.",
        PromptType.COMPANION_SAVE_ERROR: "Feedback konnte nicht gespeichert werden.",
        PromptType.COMPANION_GENERAL_ERROR: "Es gab ein Problem. Bitte versuche es erneut.",
        
        # Generic validation prompt
        PromptType.VALIDATION: "Test validation prompt"
    }
    
    def get_prompt_side_effect(prompt_type, **kwargs):
        """Return appropriate prompt based on type"""
        return prompt_responses.get(prompt_type, f"Mock prompt for {prompt_type}")
    
    mock.get_prompt.side_effect = get_prompt_side_effect
    return mock


@pytest.fixture
def mock_gpt_service():
    """Mock GPTService for testing"""
    mock = AsyncMock()
    
    # Default completion response
    mock.complete.return_value = "Als Hund fühle ich mich in dieser Situation unsicher und verwirrt."
    
    # Health check response
    mock.health_check.return_value = {"healthy": True}
    
    return mock


@pytest.fixture
def mock_weaviate_service():
    """Mock WeaviateService for testing"""
    mock = AsyncMock()
    
    # Default search results
    mock.vector_search.return_value = [
        {
            "text": "Sample dog behavior information",
            "score": 0.9,
            "metadata": {"instinct": "territorial"}
        }
    ]
    
    # Health check response
    mock.health_check.return_value = {"healthy": True}
    
    return mock


@pytest.fixture
def mock_redis_service():
    """Mock RedisService for testing"""
    mock = AsyncMock()
    
    # Default cache operations
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = True
    
    # Health check response
    mock.health_check.return_value = {"healthy": True}
    
    return mock


@pytest.fixture
def sample_analysis_data():
    """Sample analysis data for testing dog responses"""
    return {
        'primary_instinct': 'territorial',
        'primary_description': 'Der Hund zeigt territoriales Verhalten zum Schutz seines Reviers',
        'all_instincts': {
            'jagd': 'Jagdinstinkt - der Hund will Dinge verfolgen und fangen',
            'rudel': 'Rudelinstinkt - soziales Verhalten in der Gruppe',
            'territorial': 'Territorialinstinkt - Schutz des eigenen Gebiets',
            'sexual': 'Sexualinstinkt - Fortpflanzungsverhalten'
        },
        'exercise': 'Übe mit deinem Hund Impulskontrolle durch klare Grenzen',
        'confidence': 0.85
    }


@pytest.fixture
def sample_exercise_data():
    """Sample exercise data for testing"""
    return "Übe mit deinem Hund täglich 10 Minuten Impulskontrolle. Beginne mit einfachen Kommandos wie 'Sitz' und 'Bleib'."


@pytest.fixture
def sample_dog_contexts():
    """Sample contexts for DogAgent testing"""
    return {
        'greeting': AgentContext(
            session_id="test-session",
            message_type=MessageType.GREETING
        ),
        'perspective_response': AgentContext(
            session_id="test-session",
            user_input="Mein Hund bellt ständig",
            message_type=MessageType.RESPONSE,
            metadata={
                'response_mode': 'perspective_only',
                'analysis_data': {
                    'primary_instinct': 'territorial',
                    'all_instincts': {}
                }
            }
        ),
        'diagnosis_response': AgentContext(
            session_id="test-session",
            message_type=MessageType.RESPONSE,
            metadata={
                'response_mode': 'diagnosis',
                'analysis_data': {
                    'primary_instinct': 'territorial',
                    'primary_description': 'Territorial behavior'
                }
            }
        ),
        'exercise_response': AgentContext(
            session_id="test-session",
            message_type=MessageType.RESPONSE,
            metadata={
                'response_mode': 'exercise',
                'exercise_data': 'Sample exercise'
            }
        ),
        'confirmation_question': AgentContext(
            session_id="test-session",
            message_type=MessageType.QUESTION,
            metadata={'question_type': 'confirmation'}
        ),
        'error_no_match': AgentContext(
            session_id="test-session",
            message_type=MessageType.ERROR,
            metadata={'error_type': 'no_match'}
        )
    }


@pytest.fixture
def sample_companion_contexts():
    """Sample contexts for CompanionAgent testing"""
    return {
        'feedback_intro': AgentContext(
            session_id="test-session",
            message_type=MessageType.GREETING
        ),
        'feedback_q1': AgentContext(
            session_id="test-session",
            message_type=MessageType.QUESTION,
            metadata={'question_number': 1}
        ),
        'feedback_q3': AgentContext(
            session_id="test-session",
            message_type=MessageType.QUESTION,
            metadata={'question_number': 3}
        ),
        'feedback_acknowledgment': AgentContext(
            session_id="test-session",
            message_type=MessageType.RESPONSE,
            metadata={'response_mode': 'acknowledgment'}
        ),
        'feedback_completion': AgentContext(
            session_id="test-session",
            message_type=MessageType.RESPONSE,
            metadata={
                'response_mode': 'completion',
                'save_success': True
            }
        ),
        'feedback_error': AgentContext(
            session_id="test-session",
            message_type=MessageType.ERROR,
            metadata={'error_type': 'save_failed'}
        )
    }


@pytest.fixture
def mock_services_bundle(mock_prompt_manager, mock_gpt_service, mock_weaviate_service, mock_redis_service):
    """Bundle of all mocked services for easy injection"""
    return {
        'prompt_manager': mock_prompt_manager,
        'gpt_service': mock_gpt_service,
        'weaviate_service': mock_weaviate_service,
        'redis_service': mock_redis_service
    }


# Test utilities
class TestUtils:
    """Utility functions for agent testing"""
    
    @staticmethod
    def assert_message_properties(message, expected_sender, contains_text=None):
        """Assert basic message properties"""
        assert hasattr(message, 'sender')
        assert hasattr(message, 'text')
        assert message.sender == expected_sender
        assert isinstance(message.text, str)
        assert len(message.text) > 0
        
        if contains_text:
            assert contains_text.lower() in message.text.lower()
    
    @staticmethod
    def assert_all_messages(messages, expected_sender, min_count=1):
        """Assert properties for all messages in a list"""
        assert isinstance(messages, list)
        assert len(messages) >= min_count
        
        for message in messages:
            TestUtils.assert_message_properties(message, expected_sender)


@pytest.fixture
def test_utils():
    """Provide test utility functions"""
    return TestUtils


# Markers for different test categories
def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests (fast, no external dependencies)"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (slower, may use real services)"
    )
    config.addinivalue_line(
        "markers", "agent: marks tests as agent-specific tests"
    )