# tests/v2/agents/conftest.py
"""
Shared fixtures for V2 agent tests.

Provides common mock objects and test data for agent testing.
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import Dict, Any, List
from dataclasses import dataclass

from src.agents.base_agent import AgentContext, MessageType, V2AgentMessage
from src.core.prompt_manager import PromptManager, PromptType
from src.services.gpt_service import GPTService
from src.services.weaviate_service import WeaviateService
from src.services.redis_service import RedisService


# Test data constants
MOCK_SESSION_ID = "test-session-123"
MOCK_USER_INPUT = "Mein Hund bellt ständig"
MOCK_GPT_RESPONSE = "Als Hund fühle ich mich in dieser Situation unsicher."


@pytest.fixture
def mock_prompt_manager():
    """
    Mock PromptManager with comprehensive prompt responses.
    
    Returns a properly configured mock that handles all PromptType enums.
    """
    mock = Mock(spec=PromptManager)
    
    # Define comprehensive prompt responses
    prompt_responses = {
        # Dog prompts
        PromptType.DOG_GREETING: "Hallo! Schön, dass Du da bist. Ich erkläre Dir Hundeverhalten aus der Hundeperspektive.",
        PromptType.DOG_GREETING_FOLLOWUP: "Bitte beschreibe ein Verhalten oder eine Situation!",
        PromptType.DOG_PERSPECTIVE: "Ich bin ein Hund und zeige dieses Verhalten: {symptom}. Aus meiner Sicht {match}.",
        # DOG_INSTINCT_PERSPECTIVE doesn't exist in current PromptType enum
        PromptType.DOG_DIAGNOSIS: "Ich erkenne bei diesem Verhalten hauptsächlich meinen {primary_instinct}-Instinkt. {primary_description}",
        PromptType.DOG_CONFIRMATION_QUESTION: "Magst Du mehr erfahren, warum ich mich so verhalte?",
        PromptType.DOG_CONTEXT_QUESTION: "Gut, dann brauche ich ein bisschen mehr Informationen. Bitte beschreibe die Situation genauer.",
        PromptType.DOG_EXERCISE_QUESTION: "Möchtest du eine Lernaufgabe, die dir in dieser Situation helfen kann?",
        PromptType.DOG_CONTINUE_OR_RESTART: "Möchtest du ein weiteres Hundeverhalten verstehen?",
        PromptType.DOG_NO_MATCH_ERROR: "Hmm, zu diesem Verhalten habe ich leider noch keine Antwort.",
        PromptType.DOG_INVALID_INPUT_ERROR: "Kannst Du das Verhalten bitte etwas ausführlicher beschreiben?",
        PromptType.DOG_TECHNICAL_ERROR: "Wuff! Entschuldige, ich bin gerade etwas verwirrt. Kannst du es nochmal versuchen?",
        PromptType.DOG_DESCRIBE_MORE: "Kannst du mir mehr erzählen?",
        PromptType.DOG_BE_SPECIFIC: "Kannst Du das bitte genauer beschreiben?",
        PromptType.DOG_ANOTHER_BEHAVIOR_QUESTION: "Gibt es ein weiteres Verhalten, das Du mit mir besprechen möchtest?",
        PromptType.DOG_FALLBACK_EXERCISE: "Eine hilfreiche Übung wäre, mit deinem Hund Impulskontrolle zu trainieren.",
        
        # Companion prompts
        PromptType.COMPANION_FEEDBACK_INTRO: "Ich würde mich freuen, wenn du mir noch ein kurzes Feedback gibst.",
        PromptType.COMPANION_FEEDBACK_Q1: "Hast Du das Gefühl, dass Dir die Beratung bei Deinem Anliegen weitergeholfen hat?",
        PromptType.COMPANION_FEEDBACK_Q2: "Wie fandest Du die Sichtweise des Hundes – was hat Dir daran gefallen oder vielleicht irritiert?",
        PromptType.COMPANION_FEEDBACK_Q3: "Was denkst Du über die vorgeschlagene Übung – passt sie zu Deiner Situation?",
        PromptType.COMPANION_FEEDBACK_Q4: "Auf einer Skala von 0-10: Wie wahrscheinlich ist es, dass Du Wuffchat weiterempfiehlst?",
        PromptType.COMPANION_FEEDBACK_Q5: "Optional: Deine E-Mail oder Telefonnummer für eventuelle Rückfragen.",
        PromptType.COMPANION_FEEDBACK_ACK: "Danke für deine Antwort.",
        PromptType.COMPANION_FEEDBACK_COMPLETE: "Danke für Dein Feedback! 🐾",
        PromptType.COMPANION_FEEDBACK_COMPLETE_NOSAVE: "Danke für dein Feedback! Es konnte leider nicht gespeichert werden.",
        PromptType.COMPANION_PROCEED_CONFIRMATION: "Möchtest du fortfahren?",
        PromptType.COMPANION_SKIP_CONFIRMATION: "Möchtest du überspringen?",
        PromptType.COMPANION_INVALID_FEEDBACK_ERROR: "Bitte gib eine gültige Antwort.",
        PromptType.COMPANION_SAVE_ERROR: "Das Feedback konnte nicht gespeichert werden.",
        PromptType.COMPANION_GENERAL_ERROR: "Es tut mir leid, es gab ein Problem. Bitte versuche es erneut.",
        
        # Other prompts
        PromptType.VALIDATION: "Antworte mit 'ja' oder 'nein'. Hat die folgende Eingabe mit Hundeverhalten zu tun? {text}",
        PromptType.COMBINED_INSTINCT: "Analysiere das Verhalten '{symptom}' mit Kontext '{context}' und identifiziere Instinkte.",
    }
    
    def get_prompt_side_effect(prompt_type, **kwargs):
        """Side effect for get_prompt that handles formatting"""
        # Handle the prompt_type properly - it's a PromptType enum
        template = None
        
        # Direct lookup by enum
        if prompt_type in prompt_responses:
            template = prompt_responses[prompt_type]
        else:
            # If not found, try to match by name
            for key, value in prompt_responses.items():
                if key == prompt_type or (hasattr(key, 'name') and key.name == str(prompt_type)):
                    template = value
                    break
        
        if template:
            # Simple template formatting
            try:
                return template.format(**kwargs)
            except KeyError:
                # Return template as-is if formatting fails
                return template
        
        # Default fallback
        return f"Mock prompt for {prompt_type}"
    
    mock.get_prompt.side_effect = get_prompt_side_effect
    mock.load_prompts.return_value = None
    mock.list_prompts.return_value = list(prompt_responses.keys())
    
    return mock


@pytest.fixture
def mock_gpt_service():
    """
    Mock GPTService with realistic behavior.
    
    Provides async methods and configurable responses.
    """
    mock = AsyncMock(spec=GPTService)
    
    # Default responses
    mock.complete.return_value = MOCK_GPT_RESPONSE
    mock.health_check.return_value = {
        "healthy": True,
        "status": "connected",
        "details": {"model": "gpt-4", "response_time_ms": 250}
    }
    mock.is_initialized = True
    
    # Add method to configure responses
    def configure_response(response: str):
        mock.complete.return_value = response
    
    mock.configure_response = configure_response
    
    return mock


@pytest.fixture
def mock_weaviate_service():
    """
    Mock WeaviateService with realistic search results.
    
    Provides vector search functionality with configurable results.
    """
    mock = AsyncMock(spec=WeaviateService)
    
    # Default search results
    default_results = [
        {
            "id": "uuid-1",
            "properties": {
                "text": "Hund bellt bei fremden Menschen aus territorialem Instinkt",
                "schnelldiagnose": "Der Hund zeigt territoriales Verhalten",
                "instinct": "territorial"
            },
            "metadata": {"distance": 0.15, "certainty": 0.85}
        }
    ]
    
    mock.vector_search.return_value = default_results
    mock.health_check.return_value = {
        "healthy": True,
        "status": "connected",
        "details": {"collections": ["Symptome", "Instinkte", "Erziehung"]}
    }
    mock.is_initialized = True
    
    # Add method to configure search results
    def configure_results(results: List[Dict[str, Any]]):
        mock.vector_search.return_value = results
    
    mock.configure_results = configure_results
    
    return mock


@pytest.fixture
def mock_redis_service():
    """
    Mock RedisService with realistic caching behavior.
    
    Provides in-memory cache simulation.
    """
    mock = AsyncMock(spec=RedisService)
    
    # Simple in-memory cache for testing
    cache = {}
    
    async def mock_get(key: str):
        return cache.get(key)
    
    async def mock_set(key: str, value: Any, ttl: int = None):
        cache[key] = value
        return True
    
    async def mock_delete(key: str):
        if key in cache:
            del cache[key]
        return True
    
    mock.get.side_effect = mock_get
    mock.set.side_effect = mock_set
    mock.delete.side_effect = mock_delete
    mock.health_check.return_value = {
        "healthy": True,
        "status": "connected",
        "details": {"memory_usage": "1.2MB", "keys": len(cache)}
    }
    mock.is_initialized = True
    
    # Add cache management methods
    mock.clear_cache = lambda: cache.clear()
    mock.get_cache = lambda: cache.copy()
    
    return mock


@pytest.fixture
def sample_analysis_data():
    """Realistic analysis data for testing"""
    return {
        'primary_instinct': 'territorial',
        'primary_description': 'Der Hund zeigt territoriales Verhalten zum Schutz seines Reviers und seiner Familie',
        'all_instincts': {
            'jagd': 'Der Jagdinstinkt lässt mich Dinge verfolgen und fangen wollen',
            'rudel': 'Der Rudelinstinkt regelt mein soziales Verhalten in der Gruppe',
            'territorial': 'Der territoriale Instinkt lässt mich mein Gebiet und meine Ressourcen schützen',
            'sexual': 'Der Sexualinstinkt steuert mein Fortpflanzungsverhalten'
        },
        'exercise': 'Übe mit deinem Hund die "Freund-Feind-Unterscheidung": Stelle deinen Hund Besuchern vor und belohne ruhiges Verhalten.',
        'confidence': 0.85,
        'match_quality': 'high'
    }


@pytest.fixture
def sample_contexts():
    """Common test contexts for all agents"""
    return {
        'simple': AgentContext(
            session_id=MOCK_SESSION_ID,
            user_input=MOCK_USER_INPUT,
            message_type=MessageType.RESPONSE
        ),
        'with_metadata': AgentContext(
            session_id=MOCK_SESSION_ID,
            user_input=MOCK_USER_INPUT,
            message_type=MessageType.RESPONSE,
            metadata={'response_mode': 'perspective_only'}
        ),
        'greeting': AgentContext(
            session_id=MOCK_SESSION_ID,
            message_type=MessageType.GREETING
        ),
        'error': AgentContext(
            session_id=MOCK_SESSION_ID,
            message_type=MessageType.ERROR,
            metadata={'error_type': 'technical'}
        )
    }


@dataclass
class AgentTestHelper:
    """Helper class for common agent test operations"""
    
    @staticmethod
    def assert_message_valid(message: V2AgentMessage, expected_sender: str = None):
        """Assert that a message has valid structure"""
        assert isinstance(message, V2AgentMessage)
        assert hasattr(message, 'sender')
        assert hasattr(message, 'text')
        assert hasattr(message, 'message_type')
        assert hasattr(message, 'metadata')
        
        assert isinstance(message.text, str)
        assert len(message.text) > 0
        assert isinstance(message.metadata, dict)
        
        if expected_sender:
            assert message.sender == expected_sender
    
    @staticmethod
    def assert_messages_valid(messages: List[V2AgentMessage], expected_sender: str = None, min_count: int = 1):
        """Assert that a list of messages is valid"""
        assert isinstance(messages, list)
        assert len(messages) >= min_count
        
        for message in messages:
            AgentTestHelper.assert_message_valid(message, expected_sender)
    
    @staticmethod
    def create_mock_messages(count: int, sender: str = "test") -> List[V2AgentMessage]:
        """Create mock messages for testing"""
        return [
            V2AgentMessage(
                sender=sender,
                text=f"Test message {i}",
                message_type=MessageType.RESPONSE.value,
                metadata={"index": i}
            )
            for i in range(count)
        ]
    
    @staticmethod
    async def assert_agent_responds(agent, context: AgentContext, expected_count: int = None):
        """Assert that agent responds properly to context"""
        messages = await agent.respond(context)
        AgentTestHelper.assert_messages_valid(messages, agent.role, min_count=1)
        
        if expected_count is not None:
            assert len(messages) == expected_count
            
        return messages


@pytest.fixture
def agent_test_helper():
    """Provide test helper instance"""
    return AgentTestHelper()


# Pytest configuration
def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, isolated, mocked dependencies)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (may use real components)"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take longer to run"
    )
    config.addinivalue_line(
        "markers", "flaky: Tests that may fail intermittently"
    )


# Async test utilities
@pytest.fixture
def async_timeout():
    """Timeout for async operations"""
    return 5.0  # 5 seconds


@pytest.fixture
async def cleanup_tasks():
    """Cleanup any pending async tasks after tests"""
    yield
    # Cleanup code if needed
    import asyncio
    tasks = [t for t in asyncio.all_tasks() if not t.done()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)