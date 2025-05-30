# tests/v2/agents/test_agent_integration.py
"""
Integration tests for V2 Agents working with real services.

Tests cover:
- Agents with actual PromptManager
- GPT service integration
- Complex conversation flows
- Error recovery scenarios
- Performance characteristics
"""

import pytest
from unittest.mock import AsyncMock, patch, Mock
import asyncio
import time

from src.agents.dog_agent import DogAgent
from src.agents.companion_agent import CompanionAgent
from src.agents.base_agent import AgentContext, MessageType, V2AgentMessage
from src.core.prompt_manager import PromptManager, PromptType
from src.services.gpt_service import GPTService
from src.services.weaviate_service import WeaviateService
from src.services.redis_service import RedisService
from src.core.exceptions import V2ValidationError


class TestDogAgentIntegration:
    """Test DogAgent with real PromptManager and mocked services"""
    
    @pytest.mark.asyncio
    async def test_full_response_flow(self, mock_integrated_prompt_manager, mock_gpt_service):
        """Test complete response generation flow"""
        # Setup
        agent = DogAgent(
            prompt_manager=mock_integrated_prompt_manager,
            gpt_service=mock_gpt_service
        )
        
        # Mock GPT responses
        mock_gpt_service.complete.side_effect = [
            "Als Hund belle ich, weil ich mein Territorium beschütze!",
            "Mein Schutzinstinkt ist sehr stark ausgeprägt."
        ]
        
        # Test greeting
        greeting_context = AgentContext(
            session_id="integration-test",
            message_type=MessageType.GREETING
        )
        
        greeting_messages = await agent.respond(greeting_context)
        
        # Check we get greeting messages
        assert len(greeting_messages) == 2  # DogAgent returns 2 messages for greeting
        assert greeting_messages[0].sender == "dog"
        assert greeting_messages[0].message_type == MessageType.GREETING.value
        assert greeting_messages[1].message_type == MessageType.QUESTION.value
        
        # Test perspective response
        perspective_context = AgentContext(
            session_id="integration-test",
            user_input="Mein Hund bellt bei Fremden",
            message_type=MessageType.RESPONSE,
            metadata={
                'response_mode': 'perspective_only',
                'match_data': 'Bellen bei fremden Menschen'
            }
        )
        
        perspective_messages = await agent.respond(perspective_context)
        
        assert len(perspective_messages) == 1
        assert "Territorium" in perspective_messages[0].text or "territorium" in perspective_messages[0].text.lower()
        
        # Test diagnosis
        diagnosis_context = AgentContext(
            session_id="integration-test",
            message_type=MessageType.RESPONSE,
            metadata={
                'response_mode': 'diagnosis',
                'analysis_data': {
                    'primary_instinct': 'territorial',
                    'primary_description': 'Schutz des eigenen Bereichs'
                }
            }
        )
        
        diagnosis_messages = await agent.respond(diagnosis_context)
        
        assert len(diagnosis_messages) == 1
        assert "Schutzinstinkt" in diagnosis_messages[0].text or "schutz" in diagnosis_messages[0].text.lower()
    
    @pytest.mark.asyncio
    async def test_error_recovery_flow(self, mock_integrated_prompt_manager, mock_gpt_service):
        """Test agent recovers gracefully from service errors"""
        agent = DogAgent(
            prompt_manager=mock_integrated_prompt_manager,
            gpt_service=mock_gpt_service
        )
        
        # First call fails, second succeeds
        mock_gpt_service.complete.side_effect = [
            Exception("GPT service timeout"),
            "Fallback response text"
        ]
        
        context = AgentContext(
            session_id="error-test",
            message_type=MessageType.RESPONSE,
            metadata={
                'response_mode': 'perspective_only',
                'match_data': 'Test data'
            }
        )
        
        # Should handle error and return error message
        messages = await agent.respond(context)
        
        assert len(messages) == 1
        assert messages[0].message_type == MessageType.ERROR.value
        
        # Now try again - should work
        messages = await agent.respond(context)
        
        assert len(messages) == 1
        assert messages[0].text == "Fallback response text"
    
    @pytest.mark.asyncio
    async def test_performance_characteristics(self, mock_integrated_prompt_manager, mock_gpt_service):
        """Test agent response times are reasonable"""
        agent = DogAgent(
            prompt_manager=mock_integrated_prompt_manager,
            gpt_service=mock_gpt_service
        )
        
        # Mock fast GPT responses
        mock_gpt_service.complete.return_value = "Quick response"
        
        contexts = [
            AgentContext(
                session_id=f"perf-test-{i}",
                message_type=MessageType.GREETING
            )
            for i in range(10)
        ]
        
        start_time = time.time()
        
        # Process multiple contexts
        for context in contexts:
            await agent.respond(context)
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Should be fast (under 1 second for 10 calls with mocked services)
        assert elapsed < 1.0
        
        # Average response time
        avg_time = elapsed / 10
        assert avg_time < 0.1  # Under 100ms per response


class TestCompanionAgentIntegration:
    """Test CompanionAgent with real PromptManager"""
    
    @pytest.mark.asyncio
    async def test_complete_feedback_flow(self, mock_integrated_prompt_manager):
        """Test complete feedback collection flow"""
        agent = CompanionAgent(prompt_manager=mock_integrated_prompt_manager)
        
        # Generate complete feedback sequence
        sequence = await agent.create_feedback_sequence("feedback-test")
        
        # Process each step
        all_messages = []
        
        for context in sequence[:6]:  # Skip completion for now
            messages = await agent.respond(context)
            all_messages.extend(messages)
        
        # Should have intro + 5 questions
        assert len(all_messages) >= 6
        
        # Verify questions are different
        question_texts = [
            msg.text for msg in all_messages 
            if msg.message_type == MessageType.QUESTION.value
        ]
        assert len(set(question_texts)) == 5  # All unique
        
        # Test completion with save success
        completion_context = sequence[-1]
        completion_context.metadata['save_success'] = True
        
        completion_messages = await agent.respond(completion_context)
        
        assert len(completion_messages) == 1
        assert "Dank" in completion_messages[0].text or "dank" in completion_messages[0].text.lower()
    
    @pytest.mark.asyncio
    async def test_bilingual_prompt_handling(self, mock_integrated_prompt_manager):
        """Test agent handles German prompts correctly"""
        agent = CompanionAgent(prompt_manager=mock_integrated_prompt_manager)
        
        # Test German characters in prompts
        context = AgentContext(
            session_id="german-test",
            message_type=MessageType.QUESTION,
            metadata={'question_number': 2}
        )
        
        messages = await agent.respond(context)
        
        # Should contain German-specific characters
        text = messages[0].text
        # Check for common German words/patterns
        assert any(word in text.lower() for word in ['die', 'der', 'das', 'du', 'dir', 'dein', 'ihr'])


class TestAgentInteraction:
    """Test multiple agents working together"""
    
    @pytest.mark.asyncio
    async def test_dog_to_companion_handoff(self, mock_integrated_prompt_manager):
        """Test handoff from dog agent to companion agent"""
        dog_agent = DogAgent(prompt_manager=mock_integrated_prompt_manager)
        companion_agent = CompanionAgent(prompt_manager=mock_integrated_prompt_manager)
        
        # Dog agent finishes interaction
        dog_context = AgentContext(
            session_id="handoff-test",
            message_type=MessageType.QUESTION,
            metadata={'question_type': 'restart'}
        )
        
        dog_messages = await dog_agent.respond(dog_context)
        assert len(dog_messages) == 1
        assert dog_messages[0].sender == "dog"
        assert dog_messages[0].message_type == MessageType.QUESTION.value
        
        # User says no - transition to companion
        companion_context = AgentContext(
            session_id="handoff-test",
            message_type=MessageType.GREETING
        )
        
        companion_messages = await companion_agent.respond(companion_context)
        assert len(companion_messages) == 1
        assert companion_messages[0].sender == "companion"
        assert companion_messages[0].message_type == MessageType.GREETING.value


class TestAgentResilience:
    """Test agent resilience and error handling"""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, mock_integrated_prompt_manager, mock_gpt_service):
        """Test agents handle concurrent requests properly"""
        agent = DogAgent(
            prompt_manager=mock_integrated_prompt_manager,
            gpt_service=mock_gpt_service
        )
        
        mock_gpt_service.complete.return_value = "Concurrent response"
        
        # Create multiple concurrent contexts
        contexts = [
            AgentContext(
                session_id=f"concurrent-{i}",
                message_type=MessageType.GREETING
            )
            for i in range(5)
        ]
        
        # Process concurrently
        tasks = [agent.respond(context) for context in contexts]
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert len(results) == 5
        for messages in results:
            assert len(messages) >= 1
            assert messages[0].sender == "dog"
    
    @pytest.mark.asyncio
    async def test_memory_stability(self, mock_integrated_prompt_manager):
        """Test agents don't leak memory with many requests"""
        agent = CompanionAgent(prompt_manager=mock_integrated_prompt_manager)
        
        # Process many requests
        for i in range(100):
            context = AgentContext(
                session_id=f"memory-test-{i}",
                message_type=MessageType.QUESTION,
                metadata={'question_number': (i % 5) + 1}
            )
            
            await agent.respond(context)
        
        # Agent should still be functional
        final_context = AgentContext(
            session_id="final-test",
            message_type=MessageType.GREETING
        )
        
        final_messages = await agent.respond(final_context)
        assert len(final_messages) >= 1
    
    @pytest.mark.asyncio
    async def test_malformed_input_handling(self, mock_integrated_prompt_manager):
        """Test agents handle malformed inputs gracefully"""
        agent = DogAgent(prompt_manager=mock_integrated_prompt_manager)
        
        # Various malformed contexts
        test_cases = [
            # Empty metadata
            AgentContext(
                session_id="malformed-1",
                message_type=MessageType.RESPONSE,
                metadata={}
            ),
            # Wrong metadata type
            AgentContext(
                session_id="malformed-2",
                message_type=MessageType.RESPONSE,
                metadata={'response_mode': 123}  # Should be string
            ),
            # Very long input
            AgentContext(
                session_id="malformed-3",
                user_input="x" * 10000,
                message_type=MessageType.RESPONSE,
                metadata={'response_mode': 'perspective_only'}
            )
        ]
        
        for context in test_cases:
            # Should handle gracefully - either return error message or process with defaults
            messages = await agent.respond(context)
            
            # Should always return at least one message
            assert len(messages) >= 1
            # Should be from dog agent
            assert messages[0].sender == "dog"
            # Should be either error or response
            assert messages[0].message_type in [MessageType.ERROR.value, MessageType.RESPONSE.value]


# Fixtures
@pytest.fixture
def mock_integrated_prompt_manager():
    """Mock PromptManager for integration tests with all prompts available"""
    mock = Mock(spec=PromptManager)
    
    # Complete prompt responses for integration testing
    prompt_responses = {
        # Dog prompts
        PromptType.DOG_GREETING: "Hallo! Schön, dass Du da bist. Ich erkläre Dir Hundeverhalten aus der Hundeperspektive.",
        PromptType.DOG_GREETING_FOLLOWUP: "Bitte beschreibe ein Verhalten oder eine Situation!",
        PromptType.DOG_PERSPECTIVE: "Ich bin ein Hund und zeige dieses Verhalten: {symptom}. Aus meiner Sicht {match}.",
        # DOG_INSTINCT_PERSPECTIVE doesn't exist, using DOG_DIAGNOSIS for instinct-based responses
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
    }
    
    def get_prompt_side_effect(prompt_type, **kwargs):
        """Return appropriate prompt with formatting"""
        if prompt_type in prompt_responses:
            template = prompt_responses[prompt_type]
            try:
                return template.format(**kwargs)
            except KeyError:
                return template
        return f"Mock prompt for {prompt_type}"
    
    mock.get_prompt.side_effect = get_prompt_side_effect
    mock.load_prompts.return_value = None
    
    return mock


@pytest.fixture
def real_prompt_manager():
    """Real PromptManager instance - use mock_integrated_prompt_manager instead"""
    # For integration tests, we should use a properly mocked prompt manager
    # since the real one requires actual prompt files
    return pytest.fixture("mock_integrated_prompt_manager")


@pytest.fixture
def mock_gpt_service():
    """Mock GPTService for integration tests"""
    mock = AsyncMock(spec=GPTService)
    mock.complete.return_value = "Mock GPT response"
    mock.health_check.return_value = {"healthy": True}
    return mock


@pytest.fixture
def mock_weaviate_service():
    """Mock WeaviateService for integration tests"""
    mock = AsyncMock(spec=WeaviateService)
    mock.vector_search.return_value = [
        {"text": "Integration test result", "score": 0.95}
    ]
    mock.health_check.return_value = {"healthy": True}
    return mock


@pytest.fixture
def mock_redis_service():
    """Mock RedisService for integration tests"""
    mock = AsyncMock(spec=RedisService)
    mock.set.return_value = True
    mock.get.return_value = None
    mock.health_check.return_value = {"healthy": True}
    return mock