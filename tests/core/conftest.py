# tests/v2/core/conftest.py
"""
Fixed shared fixtures for V2 core component tests.

Provides properly mocked services, sample data, and utilities for testing
flow handlers, flow engine, and orchestrator.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List

from src.models.flow_models import FlowStep
from src.models.session_state import SessionState, SessionStore
from src.agents.base_agent import AgentContext, MessageType, V2AgentMessage
from src.core.flow_engine import FlowEvent


@pytest.fixture
def mock_gpt_service():
    """Mock GPTService for testing"""
    mock = AsyncMock()
    
    # Default responses for different scenarios
    async def complete_side_effect(prompt, **kwargs):
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
    async def search_side_effect(collection=None, query=None, limit=3, properties=None, return_metadata=True, **kwargs):
        # Map collection to collection_name for compatibility
        collection_name = collection
        if collection_name == "Symptome":
            if "bellt" in query.lower():
                return [
                    {
                        "id": "uuid-1",
                        "properties": {
                            "text": "Hund bellt territorial zur Verteidigung",
                            "schnelldiagnose": "Der Hund zeigt territoriales Verhalten zum Schutz seines Reviers",
                            "instinct": "territorial"
                        },
                        "metadata": {"distance": 0.1, "certainty": 0.9}
                    },
                    {
                        "id": "uuid-2",
                        "properties": {
                            "text": "Bellverhalten bei Hunden",
                            "schnelldiagnose": "Bellen ist ein normales Kommunikationsmittel",
                            "behavior": "barking"
                        },
                        "metadata": {"distance": 0.2, "certainty": 0.8}
                    }
                ]
            elif "springt" in query.lower():
                return [
                    {
                        "id": "uuid-3",
                        "properties": {
                            "text": "Hund springt aus Rudelinstinkt",
                            "schnelldiagnose": "Das Springen zeigt Aufregung und Begrüßungsverhalten im Rudel",
                            "instinct": "rudel"
                        },
                        "metadata": {"distance": 0.15, "certainty": 0.85}
                    }
                ]
            else:
                return []  # No matches
        
        elif collection_name == "Instinkte":
            return [
                {
                    "id": "inst-1",
                    "properties": {
                        "text": "Territorial: Schutz des eigenen Gebiets",
                        "type": "territorial"
                    },
                    "metadata": {"distance": 0.1, "certainty": 0.9}
                },
                {
                    "id": "inst-2",
                    "properties": {
                        "text": "Jagd: Verfolgung und Fangen von Beute",
                        "type": "jagd"
                    },
                    "metadata": {"distance": 0.2, "certainty": 0.8}
                },
                {
                    "id": "inst-3",
                    "properties": {
                        "text": "Rudel: Soziales Gruppenverhalten",
                        "type": "rudel"
                    },
                    "metadata": {"distance": 0.3, "certainty": 0.7}
                }
            ]
        
        elif collection_name == "Erziehung":
            return [
                {
                    "id": "exercise-1",
                    "properties": {
                        "text": "Übe täglich 10 Minuten Impulskontrolle mit klaren Kommandos",
                        "anleitung": "Übe täglich 10 Minuten Impulskontrolle mit klaren Kommandos",
                        "exercise_type": "impulse_control"
                    },
                    "metadata": {"distance": 0.1, "certainty": 0.9}
                }
            ]
        
        return []
    
    # The flow handlers use 'search' not 'vector_search'
    mock.search.side_effect = search_side_effect
    # Also keep vector_search for compatibility  
    mock.vector_search.side_effect = search_side_effect
    mock.health_check.return_value = {"healthy": True}
    
    return mock


@pytest.fixture
def mock_redis_service():
    """Mock RedisService for testing with flexible argument handling"""
    mock = Mock()  # Use regular Mock, not AsyncMock for Redis
    
    # Storage for testing
    redis_storage = {}
    
    def set_side_effect(*args, **kwargs):
        """Handle set calls with maximum flexibility"""
        try:
            # Initialize variables
            key = None
            value = None
            expire = None
            
            # Try to extract from positional arguments
            if args:
                if len(args) >= 1:
                    key = args[0]
                if len(args) >= 2:
                    value = args[1]
                if len(args) >= 3:
                    expire = args[2]
            
            # Override with keyword arguments if present
            key = kwargs.get('key', key)
            value = kwargs.get('value', value)
            expire = kwargs.get('expire', expire)
            
            # Store if we have at least key and value
            if key is not None and value is not None:
                redis_storage[key] = {"value": value, "expire": expire}
                return True
            
            # Default success even if no valid args
            return True
            
        except Exception as e:
            print(f"Redis mock set error (ignored): {e}")
            return True
    
    def get_side_effect(key, **kwargs):
        """Handle get calls"""
        try:
            stored = redis_storage.get(key, {})
            return stored.get("value")
        except Exception:
            return None
    
    mock.set = Mock(side_effect=set_side_effect)
    mock.get = Mock(side_effect=get_side_effect)
    mock.health_check = Mock(return_value={"healthy": True})
    
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
    """Mock DogAgent for testing - always returns lists"""
    mock = AsyncMock()
    
    async def respond_side_effect(context):
        # Always return a list of messages, never None
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
            else:
                return [V2AgentMessage(sender="dog", text="Standard response", message_type="response")]
        elif context.message_type == MessageType.QUESTION:
            question_type = context.metadata.get('question_type', 'confirmation')
            return [V2AgentMessage(sender="dog", text=f"{question_type.title()} Frage?", message_type="question")]
        elif context.message_type == MessageType.ERROR:
            return [V2AgentMessage(sender="dog", text="Es tut mir leid.", message_type="error")]
        elif context.message_type == MessageType.INSTRUCTION:
            return [V2AgentMessage(sender="dog", text="Bitte mehr Details.", message_type="instruction")]
        
        # Default fallback - always return at least one message
        return [V2AgentMessage(sender="dog", text="Standard Antwort", message_type="response")]
    
    mock.respond.side_effect = respond_side_effect
    mock.health_check.return_value = {"healthy": True, "agent": "dog"}
    
    return mock


@pytest.fixture
def mock_companion_agent():
    """Mock CompanionAgent for testing - always returns lists"""
    mock = AsyncMock()
    
    async def respond_side_effect(context):
        # Always return a list of messages, never None
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
            else:
                return [V2AgentMessage(sender="companion", text="OK", message_type="response")]
        
        # Default fallback - always return at least one message
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


# Fully mocked orchestrator fixture for integration tests
@pytest.fixture
def fully_mocked_orchestrator(sample_session_store, mock_services_bundle, mock_agents_bundle):
    """Create a fully mocked orchestrator for testing"""
    from src.core.orchestrator import V2Orchestrator
    from src.core.flow_engine import FlowEngine
    from src.core.flow_handlers import FlowHandlers
    
    # Create mocked flow handlers with all services
    mock_handlers = FlowHandlers(
        dog_agent=mock_agents_bundle['dog_agent'],
        companion_agent=mock_agents_bundle['companion_agent'],
        **mock_services_bundle
    )
    
    # Create flow engine with mocked handlers
    mock_engine = FlowEngine(mock_handlers)
    
    # Create orchestrator with mocks
    orchestrator = V2Orchestrator(
        session_store=sample_session_store,
        flow_engine=mock_engine
    )
    
    return orchestrator


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


# Additional helper fixtures
@pytest.fixture
def mock_flow_engine():
    """Mock FlowEngine for isolated testing"""
    from src.core.flow_engine import FlowEngine, FlowEvent
    
    mock = AsyncMock(spec=FlowEngine)
    mock.classify_user_input.return_value = FlowEvent.USER_INPUT
    mock.process_event.return_value = (
        FlowStep.WAIT_FOR_SYMPTOM,
        [V2AgentMessage(sender="dog", text="Test", message_type="response")]
    )
    mock.get_valid_transitions.return_value = []
    mock.get_flow_summary.return_value = {
        "total_states": 10,
        "total_transitions": 25,
        "states": ["greeting", "wait_for_symptom"],
        "events": ["user_input", "yes_response"],
        "transitions": []
    }
    mock.validate_fsm.return_value = []
    
    return mock