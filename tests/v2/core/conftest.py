# tests/v2/core/conftest.py
"""
Shared fixtures for V2 core component tests (Phase 5).

Provides mocked services, sample data, and utilities for testing
flow handlers, flow engine, and orchestrator.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from src.models.flow_models import FlowStep
from src.state.session_state import SessionState, SessionStore
from src.v2.agents.base_agent import AgentContext, MessageType, V2AgentMessage
from src.v2.core.flow_engine import FlowEvent


@pytest.fixture
def mock_gpt_service():
    """Mock GPTService for testing"""
    mock = AsyncMock()
    
    # Default responses for different scenarios
    def complete_side_effect(prompt, **kwargs):
        if "jagd" in prompt.lower():
            return "Als Hund will ich jagen und verfolgen."
        elif "territorial" in prompt.lower():
            return "Als Hund beschütze ich mein Gebiet."
        elif "rudel" in prompt.lower():
            return "Als Hund brauche ich mein Rudel."
        elif "instinkt" in prompt.lower():
            return "territorial"  # Primary instinct response
        else:
            return "Als Hund fühle ich mich in dieser Situation unsicher."
    
    mock.complete.side_effect = complete_side_effect
    mock.health_check.return_value = {"healthy": True}
    
    return mock


@pytest.fixture
def mock_weaviate_service():
    """Mock WeaviateService for testing"""
    mock = AsyncMock()
    
    # Default search results
    def vector_search_side_effect(query, collection_name=None, limit=3):
        if collection_name == "Symptome":
            if "bellt" in query.lower():
                return [
                    {
                        "text": "Hund bellt territorial zur Verteidigung",
                        "score": 0.9,
                        "metadata": {"instinct": "territorial"}
                    },
                    {
                        "text": "Bellverhalten bei Hunden",
                        "score": 0.8,
                        "metadata": {"behavior": "barking"}
                    }
                ]
            elif "springt" in query.lower():
                return [
                    {
                        "text": "Hund springt aus Rudelinstinkt",
                        "score": 0.85,
                        "metadata": {"instinct": "rudel"}
                    }
                ]
            else:
                return []  # No matches
        
        elif collection_name == "Instinkte":
            return [
                {
                    "text": "Territorial: Schutz des eigenen Gebiets",
                    "score": 0.9,
                    "metadata": {"type": "territorial"}
                },
                {
                    "text": "Jagd: Verfolgung und Fangen von Beute",
                    "score": 0.8,
                    "metadata": {"type": "jagd"}
                },
                {
                    "text": "Rudel: Soziales Gruppenverhalten",
                    "score": 0.7,
                    "metadata": {"type": "rudel"}
                }
            ]
        
        elif collection_name == "Erziehung":
            return [
                {
                    "text": "Übe täglich 10 Minuten Impulskontrolle mit klaren Kommandos",
                    "score": 0.9,
                    "metadata": {"exercise_type": "impulse_control"}
                }
            ]
        
        return []
    
    mock.vector_search.side_effect = vector_search_side_effect
    mock.health_check.return_value = {"healthy": True}
    
    return mock


@pytest.fixture
def mock_redis_service():
    """Mock RedisService for testing"""
    mock = AsyncMock()
    
    # Storage for testing
    redis_storage = {}
    
    def set_side_effect(*args, **kwargs):
        """Handle set calls with flexible arguments - no unpacking errors"""
        try:
            # Handle both positional and keyword arguments safely
            if len(args) >= 2:
                key = args[0]  
                value = args[1]
                expire = args[2] if len(args) > 2 else kwargs.get('expire')
            elif len(args) == 1:
                key = args[0]
                value = kwargs.get('value', {})
                expire = kwargs.get('expire')
            else:
                # Fallback - just return True
                return True
            
            redis_storage[key] = {"value": value, "expire": expire}
            return True
        except Exception as e:
            # If anything goes wrong, just return True (successful mock)
            print(f"Redis mock set error (ignored): {e}")
            return True
    
    def get_side_effect(key):
        try:
            return redis_storage.get(key, {}).get("value")
        except:
            return None
    
    mock.set.side_effect = set_side_effect
    mock.get.side_effect = get_side_effect  
    mock.health_check.return_value = {"healthy": True}
    
    return mock


@pytest.fixture
def mock_prompt_manager():
    """Mock PromptManager for testing"""
    mock = Mock()
    
    # Default prompts for different types
    prompt_responses = {
        # Dog prompts
        "dog.greeting": "Wuff! Hallo!",
        "dog.greeting.followup": "Was ist los?",
        "dog.confirmation.question": "Magst Du mehr erfahren?",
        "dog.context.question": "Erzähl mir mehr über die Situation.",
        "dog.exercise.question": "Möchtest du eine Übung?",
        "dog.restart.question": "Möchtest du ein weiteres Verhalten besprechen?",
        "dog.no.match.error": "Dazu habe ich keine Informationen.",
        "dog.technical.error": "Es tut mir leid, ich habe ein Problem.",
        "dog.describe.more": "Kannst du mehr erzählen?",
        "dog.fallback.exercise": "Übe Impulskontrolle mit deinem Hund.",
        
        # Companion prompts
        "companion.feedback.intro": "Ich würde mich über Feedback freuen.",
        "companion.feedback.q1": "Hat dir die Beratung geholfen?",
        "companion.feedback.q2": "Wie fandest du die Hundeperspektive?",
        "companion.feedback.q3": "Was denkst du über die Übung?",
        "companion.feedback.q4": "Würdest du uns weiterempfehlen?",
        "companion.feedback.q5": "Optional: Deine E-Mail für Rückfragen.",
        "companion.feedback.complete": "Danke für dein Feedback! 🐾",
        
        # Generation prompts
        "generation.dog_perspective": "Hundeperspektive: {symptom} mit {match}",
        "query.combined_instinct": "Analysiere: {symptom} mit Kontext: {context}",
    }
    
    def get_prompt_side_effect(prompt_type, **kwargs):
        key = str(prompt_type).lower().replace('prompttype.', '').replace('_', '.')
        template = prompt_responses.get(key, f"Mock prompt for {prompt_type}")
        
        # Simple template formatting
        try:
            return template.format(**kwargs)
        except KeyError:
            return template
    
    mock.get_prompt.side_effect = get_prompt_side_effect
    return mock


@pytest.fixture
def mock_dog_agent():
    """Mock DogAgent for testing"""
    mock = AsyncMock()
    
    def respond_side_effect(context):
        if context.message_type == MessageType.GREETING:
            return [
                V2AgentMessage(sender="dog", text="Wuff! Hallo!", message_type="greeting"),
                V2AgentMessage(sender="dog", text="Was ist los?", message_type="question")
            ]
        elif context.message_type == MessageType.RESPONSE:
            response_mode = context.metadata.get('response_mode', 'perspective_only')
            if response_mode == 'perspective_only':
                return [V2AgentMessage(sender="dog", text="Als Hund fühle ich mich...", message_type="response")]
            elif response_mode == 'diagnosis':
                return [V2AgentMessage(sender="dog", text="Ich erkenne territorialen Instinkt.", message_type="response")]
            elif response_mode == 'exercise':
                return [V2AgentMessage(sender="dog", text="Übe Impulskontrolle.", message_type="response")]
        elif context.message_type == MessageType.QUESTION:
            question_type = context.metadata.get('question_type', 'confirmation')
            return [V2AgentMessage(sender="dog", text=f"{question_type.title()} Frage?", message_type="question")]
        elif context.message_type == MessageType.ERROR:
            return [V2AgentMessage(sender="dog", text="Es tut mir leid.", message_type="error")]
        
        return [V2AgentMessage(sender="dog", text="Standard Antwort", message_type="response")]
    
    mock.respond.side_effect = respond_side_effect
    mock.health_check.return_value = {"healthy": True, "agent": "dog"}
    
    return mock


@pytest.fixture
def mock_companion_agent():
    """Mock CompanionAgent for testing"""
    mock = AsyncMock()
    
    def respond_side_effect(context):
        if context.message_type == MessageType.GREETING:
            return [V2AgentMessage(sender="companion", text="Feedback bitte!", message_type="greeting")]
        elif context.message_type == MessageType.QUESTION:
            question_number = context.metadata.get('question_number', 1)
            return [V2AgentMessage(sender="companion", text=f"Frage {question_number}?", message_type="question")]
        elif context.message_type == MessageType.RESPONSE:
            response_mode = context.metadata.get('response_mode', 'acknowledgment')
            if response_mode == 'acknowledgment':
                return [V2AgentMessage(sender="companion", text="Danke.", message_type="response")]
            elif response_mode == 'completion':
                return [V2AgentMessage(sender="companion", text="Feedback komplett! 🐾", message_type="response")]
        
        return [V2AgentMessage(sender="companion", text="Standard Companion Antwort", message_type="response")]
    
    mock.respond.side_effect = respond_side_effect
    mock.health_check.return_value = {"healthy": True, "agent": "companion"}
    
    return mock


@pytest.fixture
def sample_session():
    """Sample session for testing"""
    session = SessionState()
    session.session_id = "test-session-123"
    session.current_step = FlowStep.GREETING
    session.active_symptom = ""
    session.feedback = []
    return session


@pytest.fixture
def sample_session_store():
    """Sample session store with test sessions"""
    store = SessionStore()
    
    # Add a few test sessions
    session1 = SessionState()
    session1.session_id = "session-1"
    session1.current_step = FlowStep.WAIT_FOR_SYMPTOM
    store.sessions["session-1"] = session1
    
    session2 = SessionState()
    session2.session_id = "session-2"  
    session2.current_step = FlowStep.FEEDBACK_Q2
    session2.active_symptom = "bellt"
    session2.feedback = ["Ja, hilfreich"]
    store.sessions["session-2"] = session2
    
    return store


@pytest.fixture
def sample_conversation_flow():
    """Sample conversation flow data for testing"""
    return {
        "session_id": "flow-test",
        "steps": [
            {"step": FlowStep.GREETING, "input": "", "expected_messages": 2},
            {"step": FlowStep.WAIT_FOR_SYMPTOM, "input": "Mein Hund bellt", "expected_messages": 2},
            {"step": FlowStep.WAIT_FOR_CONFIRMATION, "input": "ja", "expected_messages": 1},
            {"step": FlowStep.WAIT_FOR_CONTEXT, "input": "bei Besuch", "expected_messages": 2},
            {"step": FlowStep.ASK_FOR_EXERCISE, "input": "ja", "expected_messages": 2},
            {"step": FlowStep.END_OR_RESTART, "input": "nein", "expected_messages": 1},
            {"step": FlowStep.FEEDBACK_Q1, "input": "hilfreich", "expected_messages": 1},
        ]
    }


@pytest.fixture
def sample_analysis_data():
    """Sample instinct analysis data"""
    return {
        'primary_instinct': 'territorial',
        'primary_description': 'Der Hund zeigt territoriales Verhalten',
        'all_instincts': {
            'jagd': 'Jagdinstinkt beschreibung',
            'rudel': 'Rudelinstinkt beschreibung', 
            'territorial': 'Territorialinstinkt beschreibung',
            'sexual': 'Sexualinstinkt beschreibung'
        },
        'confidence': 0.85
    }


@pytest.fixture
def mock_services_bundle(
    mock_gpt_service, 
    mock_weaviate_service, 
    mock_redis_service, 
    mock_prompt_manager
):
    """Bundle of all mocked services"""
    return {
        'gpt_service': mock_gpt_service,
        'weaviate_service': mock_weaviate_service,
        'redis_service': mock_redis_service,
        'prompt_manager': mock_prompt_manager
    }


@pytest.fixture
def mock_agents_bundle(mock_dog_agent, mock_companion_agent):
    """Bundle of all mocked agents"""
    return {
        'dog_agent': mock_dog_agent,
        'companion_agent': mock_companion_agent
    }


# Test utilities
class TestUtils:
    """Utility functions for core component testing"""
    
    @staticmethod
    def assert_v2_message_properties(message, expected_sender=None, contains_text=None):
        """Assert V2AgentMessage properties"""
        assert isinstance(message, V2AgentMessage)
        assert hasattr(message, 'sender')
        assert hasattr(message, 'text')
        assert hasattr(message, 'message_type')
        assert hasattr(message, 'metadata')
        
        if expected_sender:
            assert message.sender == expected_sender
        
        if contains_text:
            assert contains_text.lower() in message.text.lower()
    
    @staticmethod
    def assert_flow_transition(old_state, new_state, expected_transition=None):
        """Assert flow state transition"""
        assert isinstance(old_state, FlowStep)
        assert isinstance(new_state, FlowStep)
        
        if expected_transition:
            assert new_state == expected_transition
    
    @staticmethod
    def create_test_context(
        session_id="test", 
        user_input="", 
        message_type=MessageType.RESPONSE,
        metadata=None
    ):
        """Create test AgentContext"""
        return AgentContext(
            session_id=session_id,
            user_input=user_input,
            message_type=message_type,
            metadata=metadata or {}
        )
    
    @staticmethod
    def simulate_conversation_step(current_step, user_input, expected_event=None):
        """Simulate a conversation step for testing"""
        return {
            'current_step': current_step,
            'user_input': user_input,
            'expected_event': expected_event,
            'timestamp': 'test-time'
        }


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
        "markers", "flow: marks tests as flow-specific tests"
    )
    config.addinivalue_line(
        "markers", "handlers: marks tests as handler-specific tests"
    )
    config.addinivalue_line(
        "markers", "orchestrator: marks tests as orchestrator-specific tests"
    )