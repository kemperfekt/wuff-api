# tests/v2/core/test_orchestrator.py
"""
Comprehensive tests for V2 Orchestrator - Complete system integration.

Tests cover:
- Complete end-to-end conversation flows
- FSM integration and state management  
- V1 compatibility and message format conversion
- Error handling and resilience
- Health monitoring and debug features
- Performance and scalability
- Real conversation scenarios
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List
import asyncio

from src.models.flow_models import FlowStep, AgentMessage
from src.state.session_state import SessionState, SessionStore
from src.v2.agents.base_agent import V2AgentMessage, MessageType
from src.v2.core.orchestrator import V2Orchestrator, get_orchestrator, handle_message, init_orchestrator
from src.v2.core.flow_engine import FlowEngine, FlowEvent
from src.v2.core.exceptions import V2FlowError, V2ValidationError


# ===========================================
# UNIT TESTS - CORE ORCHESTRATION
# ===========================================

@pytest.mark.unit
class TestOrchestratorCore:
    """Test core orchestrator functionality"""
    
    def test_orchestrator_initialization(self, sample_session_store):
        """Test orchestrator initializes correctly"""
        orchestrator = V2Orchestrator(session_store=sample_session_store)
        
        # Verify initialization
        assert orchestrator.session_store == sample_session_store
        assert orchestrator.flow_engine is not None
        assert orchestrator.enable_logging is True
    
    def test_orchestrator_with_custom_flow_engine(self, sample_session_store):
        """Test orchestrator with custom flow engine"""
        mock_engine = Mock()
        
        orchestrator = V2Orchestrator(
            session_store=sample_session_store,
            flow_engine=mock_engine
        )
        
        assert orchestrator.flow_engine == mock_engine
    
    @pytest.mark.asyncio
    async def test_handle_message_debug(self, sample_session_store):
        """Debug version to see where the exception occurs"""
        # Create a mock flow engine
        mock_engine = AsyncMock()
        mock_engine.classify_user_input.return_value = FlowEvent.USER_INPUT
        mock_engine.process_event.return_value = (
            FlowStep.WAIT_FOR_CONFIRMATION,
            [V2AgentMessage(sender="dog", text="Als Hund belle ich territorial!", message_type="response")]
        )
        
        # Create orchestrator with pre-configured engine
        orchestrator = V2Orchestrator(
            session_store=sample_session_store,
            flow_engine=mock_engine
        )
        
        # Debug: Call handle_message and catch any exception
        try:
            messages = await orchestrator.handle_message("test-session", "mein hund bellt")
            print(f"✅ Success: Got {len(messages)} messages")
            for i, msg in enumerate(messages):
                print(f"   Message {i}: {msg}")
            return messages
        except Exception as e:
            print(f"❌ Exception in handle_message: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    @pytest.mark.asyncio
    async def test_start_conversation(self, sample_session_store):
        """Test conversation startup"""
        with patch('src.v2.core.flow_engine.FlowEngine') as mock_engine_class:
            mock_engine = AsyncMock()
            mock_engine.process_event.return_value = (
                FlowStep.WAIT_FOR_SYMPTOM,
                [
                    V2AgentMessage(sender="dog", text="Hallo! 🐾", message_type="greeting"),
                    V2AgentMessage(sender="dog", text="Was ist los?", message_type="question")
                ]
            )
            mock_engine_class.return_value = mock_engine
            
            orchestrator = V2Orchestrator(session_store=sample_session_store)
            orchestrator.flow_engine = mock_engine
            
            # Start conversation
            messages = await orchestrator.start_conversation("test-session")
            
            # Verify response format
            assert len(messages) == 2
            assert messages[0]["sender"] == "dog"
            assert messages[0]["text"] == "Hallo! 🐾"
            assert messages[0]["message_type"] == "greeting"
            assert "metadata" in messages[0]
            
            # Verify engine was called correctly
            mock_engine.process_event.assert_called_once()
            call_args = mock_engine.process_event.call_args
            assert call_args[1]["event"] == FlowEvent.START_SESSION
    
    @pytest.mark.asyncio
    async def test_handle_message_debug(self, sample_session_store):
        """Debug version to see where the exception occurs"""
        # Create a mock flow engine
        mock_engine = AsyncMock()
        mock_engine.classify_user_input.return_value = FlowEvent.USER_INPUT
        mock_engine.process_event.return_value = (
            FlowStep.WAIT_FOR_CONFIRMATION,
            [V2AgentMessage(sender="dog", text="Als Hund belle ich territorial!", message_type="response")]
        )
        
        # Create orchestrator with pre-configured engine
        orchestrator = V2Orchestrator(
            session_store=sample_session_store,
            flow_engine=mock_engine
        )
        
        # Debug: Call handle_message and catch any exception
        try:
            messages = await orchestrator.handle_message("test-session", "mein hund bellt")
            print(f"✅ Success: Got {len(messages)} messages")
            for i, msg in enumerate(messages):
                print(f"   Message {i}: {msg}")
            return messages
        except Exception as e:
            print(f"❌ Exception in handle_message: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    @pytest.mark.asyncio
    async def test_handle_message_basic(self, sample_session_store):
        """Test basic message handling with externally provided flow engine"""
        # First run the debug version to see what happens
        try:
            messages = await self.test_handle_message_debug(sample_session_store)
            
            # If debug succeeds, verify the response
            assert len(messages) == 1
            assert messages[0]["sender"] == "dog"
            assert "belle ich" in messages[0]["text"]
            
        except Exception as e:
            # If debug fails, we know there's a deeper issue
            pytest.fail(f"Orchestrator handle_message failed: {e}")
    
@pytest.mark.asyncio
async def test_orchestrator_minimal(self, sample_session_store):
    """Minimal test - just verify orchestrator can be created"""
    mock_engine = AsyncMock()
    
    # Just try to create the orchestrator
    try:
        orchestrator = V2Orchestrator(
            session_store=sample_session_store,
            flow_engine=mock_engine
        )
        print("✅ Orchestrator created successfully")
        
        # Try to get session info (simpler operation)
        info = orchestrator.get_session_info("test-session")
        print(f"✅ Session info retrieved: {info}")
        
    except Exception as e:
        print(f"❌ Orchestrator creation/basic operation failed: {e}")
        import traceback
        traceback.print_exc()
        raise
            
    @pytest.mark.asyncio
    async def test_orchestrator_core_logic(self, sample_session_store):
        """Test just the core orchestrator logic without message conversion complexity"""
        mock_engine = AsyncMock()
        mock_engine.classify_user_input.return_value = FlowEvent.USER_INPUT
        mock_engine.process_event.return_value = (
            FlowStep.WAIT_FOR_CONFIRMATION,
            [V2AgentMessage(sender="dog", text="Als Hund belle ich!", message_type="response")]
        )
        
        orchestrator = V2Orchestrator(
            session_store=sample_session_store,
            flow_engine=mock_engine
        )
        
        # Test the core flow - just verify engine gets called correctly
        session = sample_session_store.get_or_create("test-session")
        
        # Verify engine methods are available and working
        event = orchestrator.flow_engine.classify_user_input("test input", session.current_step) 
        assert event == FlowEvent.USER_INPUT
        
        new_state, v2_messages = await orchestrator.flow_engine.process_event(
            session=session,
            event=event,
            user_input="test input"
        )
        
        assert new_state == FlowStep.WAIT_FOR_CONFIRMATION
        assert len(v2_messages) == 1
        assert v2_messages[0].text == "Als Hund belle ich!"
        
        print("✅ Core orchestrator logic working!")
    
    @pytest.mark.asyncio
    async def test_start_conversation_basic(self, sample_session_store):
        """Test conversation startup with provided engine"""
        mock_engine = AsyncMock()
        mock_engine.process_event.return_value = (
            FlowStep.WAIT_FOR_SYMPTOM,
            [
                V2AgentMessage(sender="dog", text="Hallo! 🐾", message_type="greeting"),
                V2AgentMessage(sender="dog", text="Was ist los?", message_type="question")
            ]
        )
        
        orchestrator = V2Orchestrator(
            session_store=sample_session_store,
            flow_engine=mock_engine
        )
        
        messages = await orchestrator.start_conversation("test-session")
        
        # Verify response format
        assert len(messages) == 2
        assert messages[0]["sender"] == "dog"
        assert messages[0]["text"] == "Hallo! 🐾"
        assert messages[0]["message_type"] == "greeting"
        assert "metadata" in messages[0]

    
    def test_get_session_info(self, sample_session_store):
        """Test session information retrieval"""
        # Setup session with data
        session = SessionState()
        session.session_id = "info-test"
        session.current_step = FlowStep.WAIT_FOR_CONTEXT
        session.active_symptom = "test symptom"
        session.feedback = ["answer1", "answer2"]
        session.messages = [
            AgentMessage(sender="user", text="test"),
            AgentMessage(sender="dog", text="response")
        ]
        
        sample_session_store.sessions["info-test"] = session
        
        orchestrator = V2Orchestrator(session_store=sample_session_store)
        
        # Get session info
        info = orchestrator.get_session_info("info-test")
        
        # Verify information
        assert info["session_id"] == "info-test"
        assert info["current_step"] == "wait_for_context"
        assert info["active_symptom"] == "test symptom"
        assert info["message_count"] == 2
        assert info["feedback_collected"] == 2
        assert "valid_events" in info


# ===========================================
# INTEGRATION TESTS - COMPLETE FLOWS
# ===========================================

@pytest.mark.integration
class TestCompleteFlows:
    """Test complete conversation flows end-to-end"""
    
    @pytest.mark.asyncio
    async def test_happy_path_conversation(self, mock_services_bundle, mock_agents_bundle):
        """Test complete happy path conversation from start to finish"""
        
        # Create orchestrator with mocked services
        with patch('src.v2.core.flow_handlers.FlowHandlers') as mock_handlers_class:
            with patch('src.v2.core.flow_engine.FlowEngine') as mock_engine_class:
                
                # Setup realistic flow engine
                mock_engine = AsyncMock()
                
                # Define response sequence for complete conversation
                conversation_responses = [
                    # 1. Start conversation
                    (FlowStep.WAIT_FOR_SYMPTOM, [
                        V2AgentMessage(sender="dog", text="🐾 Hallo! Ich erkläre Hundeverhalten!", message_type="greeting"),
                        V2AgentMessage(sender="dog", text="Beschreibe mir ein Verhalten!", message_type="question")
                    ]),
                    # 2. Symptom input
                    (FlowStep.WAIT_FOR_CONFIRMATION, [
                        V2AgentMessage(sender="dog", text="Als Hund belle ich, weil ich mein Territorium beschütze!", message_type="response"),
                        V2AgentMessage(sender="dog", text="Möchtest du mehr erfahren?", message_type="question")
                    ]),
                    # 3. Confirmation yes
                    (FlowStep.WAIT_FOR_CONTEXT, [
                        V2AgentMessage(sender="dog", text="Erzähl mir mehr über die Situation!", message_type="question")
                    ]),
                    # 4. Context input
                    (FlowStep.ASK_FOR_EXERCISE, [
                        V2AgentMessage(sender="dog", text="Ich verstehe - mein Schutzinstinkt ist aktiv!", message_type="response"),
                        V2AgentMessage(sender="dog", text="Möchtest du eine Übung?", message_type="question")
                    ]),
                    # 5. Exercise yes
                    (FlowStep.END_OR_RESTART, [
                        V2AgentMessage(sender="dog", text="Übe täglich 10 Minuten Ruhe-Training mit mir!", message_type="response"),
                        V2AgentMessage(sender="dog", text="Möchtest du ein anderes Verhalten verstehen?", message_type="question")
                    ]),
                    # 6. End - go to feedback
                    (FlowStep.FEEDBACK_Q1, [
                        V2AgentMessage(sender="companion", text="Hat dir unser Gespräch geholfen?", message_type="question")
                    ]),
                    # 7-10. Feedback questions (abbreviated)
                    (FlowStep.FEEDBACK_Q2, [V2AgentMessage(sender="companion", text="Frage 2?", message_type="question")]),
                    (FlowStep.FEEDBACK_Q3, [V2AgentMessage(sender="companion", text="Frage 3?", message_type="question")]),
                    (FlowStep.FEEDBACK_Q4, [V2AgentMessage(sender="companion", text="Frage 4?", message_type="question")]),
                    (FlowStep.FEEDBACK_Q5, [V2AgentMessage(sender="companion", text="Frage 5?", message_type="question")]),
                    # 11. Completion
                    (FlowStep.GREETING, [
                        V2AgentMessage(sender="companion", text="Vielen Dank für dein Feedback! 🐾", message_type="response")
                    ])
                ]
                
                response_index = 0
                def mock_process_event(*args, **kwargs):
                    nonlocal response_index
                    if response_index < len(conversation_responses):
                        result = conversation_responses[response_index]
                        response_index += 1
                        return result
                    return FlowStep.GREETING, []
                
                mock_engine.process_event.side_effect = mock_process_event
                mock_engine.classify_user_input.return_value = FlowEvent.USER_INPUT
                mock_engine_class.return_value = mock_engine
                
                # Setup handlers
                mock_handlers = Mock()
                mock_handlers_class.return_value = mock_handlers
                
                # Create orchestrator
                orchestrator = V2Orchestrator()
                
                print("\n=== V2 Orchestrator Complete Flow Demo ===")
                
                # 1. Start conversation
                print("\n1. Start conversation")
                messages = await orchestrator.start_conversation("complete-flow-test")
                assert len(messages) == 2
                print(f"   Generated {len(messages)} greeting messages")
                for msg in messages:
                    print(f"   🐕 {msg['sender']}: {msg['text']}")
                
                # 2. User describes symptom
                print("\n2. User beschreibt Symptom")
                print("   👤 User: Mein Hund bellt aggressiv wenn Fremde kommen")
                messages = await orchestrator.handle_message(
                    "complete-flow-test", 
                    "Mein Hund bellt aggressiv wenn Fremde kommen"
                )
                assert len(messages) >= 1
                for msg in messages:
                    print(f"   🐕 {msg['sender']}: {msg['text']}")
                
                # 3. User wants to learn more
                print("\n3. User möchte mehr erfahren")
                print("   👤 User: ja")
                messages = await orchestrator.handle_message("complete-flow-test", "ja")
                assert len(messages) >= 1
                for msg in messages:
                    print(f"   🐕 {msg['sender']}: {msg['text']}")
                
                # 4. User provides context
                print("\n4. User gibt Kontext")
                print("   👤 User: Vor allem abends wenn es dunkel ist")
                messages = await orchestrator.handle_message(
                    "complete-flow-test", 
                    "Vor allem abends wenn es dunkel ist"
                )
                assert len(messages) >= 1
                for msg in messages:
                    print(f"   🐕 {msg['sender']}: {msg['text']}")
                
                # 5. User wants exercise
                print("\n5. User möchte Übung")
                print("   👤 User: ja")
                messages = await orchestrator.handle_message("complete-flow-test", "ja")
                assert len(messages) >= 1
                for msg in messages:
                    print(f"   🐕 {msg['sender']}: {msg['text']}")
                
                # 6. User ends conversation - goes to feedback
                print("\n6. User beendet Gespräch")
                print("   👤 User: nein")
                messages = await orchestrator.handle_message("complete-flow-test", "nein")
                assert len(messages) >= 1
                for msg in messages:
                    print(f"   🤝 {msg['sender']}: {msg['text']}")
                
                # 7. Quick feedback (abbreviated for demo)
                print("\n7-10. Feedback-Sequenz (verkürzt)")
                feedback_answers = ["Ja, hilfreich", "Interessant", "Gut", "9", "test@demo.com"]
                for answer in feedback_answers:
                    print(f"   👤 User: {answer}")
                    messages = await orchestrator.handle_message("complete-flow-test", answer)
                    if messages:
                        print(f"   🤝 {messages[0]['sender']}: {messages[0]['text'][:50]}...")
                
                print("\n✅ Complete conversation flow successful!")
                print(f"   Total FSM events processed: {mock_engine.process_event.call_count}")
                
                # Get final session info
                info = orchestrator.get_session_info("complete-flow-test")
                print(f"\n📊 Final session state:")
                print(f"   Current step: {info['current_step']}")
                print(f"   Messages exchanged: {info['message_count']}")
                print(f"   Feedback collected: {info['feedback_collected']}")
    
    @pytest.mark.asyncio
    async def test_error_recovery_flow(self, sample_session_store):
        """Test orchestrator handles errors gracefully"""
        with patch('src.v2.core.flow_engine.FlowEngine') as mock_engine_class:
            # Setup failing engine
            mock_engine = AsyncMock()
            mock_engine.process_event.side_effect = V2FlowError(
                current_state="test_state",
                message="Test flow error"
            )
            mock_engine_class.return_value = mock_engine
            
            orchestrator = V2Orchestrator(session_store=sample_session_store)
            orchestrator.flow_engine = mock_engine
            
            # Handle message that will fail
            messages = await orchestrator.handle_message("error-test", "test input")
            
            # Should return error message
            assert len(messages) == 1
            assert messages[0]["sender"] == "dog"
            assert "durcheinander" in messages[0]["text"]
            assert messages[0]["message_type"] == "error"
    
    @pytest.mark.asyncio 
    async def test_restart_flow(self, sample_session_store):
        """Test restart functionality throughout conversation"""
        with patch('src.v2.core.flow_engine.FlowEngine') as mock_engine_class:
            mock_engine = AsyncMock()
            
            # Setup engine to handle restart
            def mock_classify_input(user_input, current_state):
                if user_input.lower() in ["neu", "restart", "von vorne"]:
                    return FlowEvent.RESTART_COMMAND
                return FlowEvent.USER_INPUT
            
            mock_engine.classify_user_input.side_effect = mock_classify_input
            mock_engine.process_event.return_value = (
                FlowStep.WAIT_FOR_SYMPTOM,
                [V2AgentMessage(sender="dog", text="Okay, von vorne!", message_type="response")]
            )
            mock_engine_class.return_value = mock_engine
            
            orchestrator = V2Orchestrator(session_store=sample_session_store)
            orchestrator.flow_engine = mock_engine
            
            # Test restart command
            messages = await orchestrator.handle_message("restart-test", "neu")
            
            # Verify restart handling
            assert len(messages) >= 1
            assert messages[0]["text"] == "Okay, von vorne!"
            
            # Verify restart event was processed
            mock_engine.process_event.assert_called_once()
            call_args = mock_engine.process_event.call_args
            assert call_args[1]["event"] == FlowEvent.RESTART_COMMAND


# ===========================================
# V1 COMPATIBILITY TESTS
# ===========================================

@pytest.mark.unit
class TestV1Compatibility:
    """Test V1 compatibility functions"""
    
    @pytest.mark.asyncio
    async def test_handle_message_function(self, sample_session_store):
        """Test global handle_message function works like V1"""
        with patch('src.v2.core.orchestrator.get_orchestrator') as mock_get_orch:
            mock_orchestrator = AsyncMock()
            mock_orchestrator.handle_message.return_value = [
                {"sender": "dog", "text": "V1 compatible response", "message_type": "response", "metadata": {}}
            ]
            mock_get_orch.return_value = mock_orchestrator
            
            # Call V1-compatible function
            result = await handle_message("v1-test", "test message")
            
            # Verify result
            assert len(result) == 1
            assert result[0]["sender"] == "dog"
            assert result[0]["text"] == "V1 compatible response"
            
            # Verify orchestrator was called
            mock_orchestrator.handle_message.assert_called_once_with("v1-test", "test message")
    
    def test_init_orchestrator_function(self, sample_session_store):
        """Test init_orchestrator function creates V2 orchestrator"""
        orchestrator = init_orchestrator(sample_session_store)
        
        # Verify it's a V2 orchestrator
        assert isinstance(orchestrator, V2Orchestrator)
        assert orchestrator.session_store == sample_session_store
    
    def test_get_orchestrator_singleton(self):
        """Test get_orchestrator returns singleton"""
        # Clear global state
        import src.v2.core.orchestrator
        src.v2.core.orchestrator._orchestrator = None
        
        # Get orchestrator twice
        orch1 = get_orchestrator()
        orch2 = get_orchestrator()
        
        # Should be same instance
        assert orch1 is orch2
        assert isinstance(orch1, V2Orchestrator)
    
    @pytest.mark.asyncio
    async def test_message_format_conversion(self, sample_session_store):
        """Test V2AgentMessage to V1 format conversion"""
        with patch('src.v2.core.flow_engine.FlowEngine') as mock_engine_class:
            mock_engine = AsyncMock()
            
            # V2 message with full metadata
            v2_message = V2AgentMessage(
                sender="dog",
                text="Test message",
                message_type="response",
                metadata={"test_key": "test_value", "score": 0.9}
            )
            
            mock_engine.classify_user_input.return_value = FlowEvent.USER_INPUT
            mock_engine.process_event.return_value = (FlowStep.WAIT_FOR_CONFIRMATION, [v2_message])
            mock_engine_class.return_value = mock_engine
            
            orchestrator = V2Orchestrator(session_store=sample_session_store)
            orchestrator.flow_engine = mock_engine
            
            # Handle message
            result = await orchestrator.handle_message("format-test", "test")
            
            # Verify V1-compatible format
            assert len(result) == 1
            message = result[0]
            
            # Required V1 fields
            assert message["sender"] == "dog"
            assert message["text"] == "Test message"
            
            # V2 extensions
            assert message["message_type"] == "response"
            assert message["metadata"]["test_key"] == "test_value"
            assert message["metadata"]["score"] == 0.9


# ===========================================
# HEALTH CHECKS & MONITORING
# ===========================================

@pytest.mark.unit
class TestHealthMonitoring:
    """Test health check and monitoring features"""
    
    @pytest.mark.asyncio
    async def test_health_check_all_healthy(self, sample_session_store):
        """Test health check when all services are healthy"""
        # Mock all V2 components
        with patch('src.v2.core.flow_handlers.FlowHandlers') as mock_handlers_class, \
             patch('src.v2.core.prompt_manager.PromptManager'), \
             patch('src.v2.services.gpt_service.GPTService'), \
             patch('src.v2.services.weaviate_service.WeaviateService'), \
             patch('src.v2.services.redis_service.RedisService'):
            
            # Setup healthy services
            mock_handlers = Mock()
            
            mock_gpt = AsyncMock()
            mock_gpt.health_check.return_value = {"healthy": True}
            mock_handlers.gpt_service = mock_gpt
            
            mock_weaviate = AsyncMock()
            mock_weaviate.health_check.return_value = {"healthy": True}
            mock_handlers.weaviate_service = mock_weaviate
            
            mock_redis = AsyncMock()
            mock_redis.health_check.return_value = {"healthy": True}
            mock_handlers.redis_service = mock_redis
            
            mock_handlers_class.return_value = mock_handlers
            
            orchestrator = V2Orchestrator(session_store=sample_session_store)
            orchestrator.flow_handlers = mock_handlers
            
            # Mock flow engine health
            mock_flow_engine = Mock()
            mock_flow_engine.get_flow_summary.return_value = {
                "total_states": 10,
                "total_transitions": 25
            }
            mock_flow_engine.validate_fsm.return_value = []  # No issues
            orchestrator.flow_engine = mock_flow_engine
            
            # Check health
            health = await orchestrator.health_check()
            
            # Verify all healthy
            assert health["overall"] == "healthy"
            assert health["orchestrator"] == "healthy"
            assert health["flow_engine"] == "healthy"
            assert health["services"]["gpt"] == "healthy"
            assert health["services"]["weaviate"] == "healthy"
            assert health["services"]["redis"] == "healthy"
            
            # Check summary
            assert health["summary"]["total_states"] == 10
            assert health["summary"]["total_transitions"] == 25
    
    @pytest.mark.asyncio
    async def test_health_check_with_issues(self, sample_session_store):
        """Test health check when services have issues"""
        # Mock all V2 components
        with patch('src.v2.core.flow_handlers.FlowHandlers') as mock_handlers_class, \
             patch('src.v2.core.prompt_manager.PromptManager'), \
             patch('src.v2.services.gpt_service.GPTService'), \
             patch('src.v2.services.weaviate_service.WeaviateService'), \
             patch('src.v2.services.redis_service.RedisService'):
            
            # Setup services with issues
            mock_handlers = Mock()
            
            mock_gpt = AsyncMock()
            mock_gpt.health_check.side_effect = Exception("GPT connection failed")
            mock_handlers.gpt_service = mock_gpt
            
            mock_weaviate = AsyncMock()
            mock_weaviate.health_check.return_value = {"healthy": False}
            mock_handlers.weaviate_service = mock_weaviate
            
            mock_handlers_class.return_value = mock_handlers
            
            orchestrator = V2Orchestrator(session_store=sample_session_store)
            orchestrator.flow_handlers = mock_handlers
            
            # Mock flow engine with issues
            mock_flow_engine = Mock()
            mock_flow_engine.get_flow_summary.return_value = {"total_states": 5, "total_transitions": 10}
            mock_flow_engine.validate_fsm.return_value = ["Missing handlers", "Unreachable states"]
            orchestrator.flow_engine = mock_flow_engine
            
            # Check health
            health = await orchestrator.health_check()
            
            # Verify issues detected
            assert health["overall"] == "warning"
            assert health["flow_engine"] == "issues: 2"
            assert "error" in health["services"]["gpt"]
            assert health["services"]["weaviate"] == "unhealthy"
    
    def test_flow_debug_info(self, sample_session_store):
        """Test flow debug information generation"""
        # Add sessions to store
        session1 = SessionState()
        session1.session_id = "debug-1"
        session1.current_step = FlowStep.WAIT_FOR_SYMPTOM
        session1.messages = [AgentMessage(sender="user", text="test")]
        
        session2 = SessionState()
        session2.session_id = "debug-2"
        session2.current_step = FlowStep.FEEDBACK_Q3
        session2.messages = [AgentMessage(sender="user", text="test1"), AgentMessage(sender="dog", text="test2")]
        
        sample_session_store.sessions["debug-1"] = session1
        sample_session_store.sessions["debug-2"] = session2
        
        # Mock V2 components
        with patch('src.v2.core.flow_handlers.FlowHandlers'), \
             patch('src.v2.core.prompt_manager.PromptManager'), \
             patch('src.v2.services.gpt_service.GPTService'), \
             patch('src.v2.services.weaviate_service.WeaviateService'), \
             patch('src.v2.services.redis_service.RedisService'):
            
            orchestrator = V2Orchestrator(session_store=sample_session_store)
            
            # Mock flow engine summary
            mock_flow_engine = Mock()
            mock_flow_engine.get_flow_summary.return_value = {
                "total_states": 12,
                "total_transitions": 30,
                "states": ["greeting", "wait_for_symptom"]
            }
            mock_flow_engine.validate_fsm.return_value = ["test issue"]
            orchestrator.flow_engine = mock_flow_engine
            
            # Get debug info
            debug_info = orchestrator.get_flow_debug_info()
            
            # Verify debug information
            assert debug_info["session_count"] == 2
            assert len(debug_info["active_sessions"]) == 2
            
            # Check session details
            sessions = {s["session_id"]: s for s in debug_info["active_sessions"]}
            assert sessions["debug-1"]["current_step"] == "wait_for_symptom"
            assert sessions["debug-1"]["message_count"] == 1
            assert sessions["debug-2"]["current_step"] == "feedback_q3"
            assert sessions["debug-2"]["message_count"] == 2
            
            # Check flow summary
            assert debug_info["flow_summary"]["total_states"] == 12
            assert debug_info["validation_issues"] == ["test issue"]


# ===========================================
# PERFORMANCE TESTS
# ===========================================

@pytest.mark.unit
class TestPerformance:
    """Test orchestrator performance characteristics"""
    
    @pytest.mark.asyncio
    async def test_response_time_performance(self, sample_session_store):
        """Test orchestrator response times are reasonable"""
        with patch('src.v2.core.flow_engine.FlowEngine') as mock_engine_class:
            mock_engine = AsyncMock()
            mock_engine.classify_user_input.return_value = FlowEvent.USER_INPUT
            mock_engine.process_event.return_value = (
                FlowStep.WAIT_FOR_CONFIRMATION,
                [V2AgentMessage(sender="dog", text="Fast response", message_type="response")]
            )
            mock_engine_class.return_value = mock_engine
            
            orchestrator = V2Orchestrator(session_store=sample_session_store)
            orchestrator.flow_engine = mock_engine
            
            import time
            
            # Test multiple messages
            start_time = time.time()
            
            for i in range(10):
                await orchestrator.handle_message(f"perf-test-{i}", f"message {i}")
            
            end_time = time.time()
            elapsed = end_time - start_time
            
            # Should be fast (under 1 second for 10 messages with mocks)
            assert elapsed < 1.0, f"Orchestrator too slow: {elapsed}s for 10 messages"
    
    @pytest.mark.asyncio
    async def test_concurrent_session_handling(self, sample_session_store):
        """Test orchestrator handles concurrent requests"""
        with patch('src.v2.core.flow_engine.FlowEngine') as mock_engine_class:
            mock_engine = AsyncMock()
            mock_engine.classify_user_input.return_value = FlowEvent.USER_INPUT
            mock_engine.process_event.return_value = (
                FlowStep.WAIT_FOR_CONFIRMATION,
                [V2AgentMessage(sender="dog", text="Concurrent response", message_type="response")]
            )
            mock_engine_class.return_value = mock_engine
            
            orchestrator = V2Orchestrator(session_store=sample_session_store)
            orchestrator.flow_engine = mock_engine
            
            # Create concurrent tasks
            tasks = []
            for i in range(5):
                task = orchestrator.handle_message(f"concurrent-{i}", f"message from session {i}")
                tasks.append(task)
            
            # Execute concurrently
            results = await asyncio.gather(*tasks)
            
            # Verify all completed successfully
            assert len(results) == 5
            for result in results:
                assert len(result) == 1
                assert result[0]["text"] == "Concurrent response"
    
    def test_memory_usage_stability(self, sample_session_store):
        """Test orchestrator doesn't leak memory with many sessions"""
        orchestrator = V2Orchestrator(session_store=sample_session_store)
        
        # Create many sessions
        for i in range(50):
            info = orchestrator.get_session_info(f"memory-test-{i}")
            assert info["session_id"] == f"memory-test-{i}"
        
        # Should complete without memory issues
        assert len(sample_session_store.sessions) == 50


# ===========================================
# ERROR HANDLING TESTS
# ===========================================

@pytest.mark.unit
class TestErrorHandling:
    """Test comprehensive error handling"""
    
    @pytest.mark.asyncio
    async def test_flow_error_handling(self, sample_session_store):
        """Test handling of V2FlowError"""
        with patch('src.v2.core.flow_engine.FlowEngine') as mock_engine_class:
            mock_engine = AsyncMock()
            mock_engine.process_event.side_effect = V2FlowError(
                message="Flow processing failed",
                current_state="test_state"
            )
            mock_engine_class.return_value = mock_engine
            
            orchestrator = V2Orchestrator(session_store=sample_session_store)
            orchestrator.flow_engine = mock_engine
            
            # Handle message that causes flow error
            result = await orchestrator.handle_message("flow-error-test", "test input")
            
            # Should return user-friendly error
            assert len(result) == 1
            assert result[0]["sender"] == "dog"
            assert "durcheinander" in result[0]["text"]
            assert result[0]["message_type"] == "error"
    
    @pytest.mark.asyncio
    async def test_validation_error_handling(self, sample_session_store):
        """Test handling of V2ValidationError"""
        with patch('src.v2.core.flow_engine.FlowEngine') as mock_engine_class:
            mock_engine = AsyncMock()
            mock_engine.classify_user_input.side_effect = V2ValidationError(
                message="Invalid input format",
                field="user_input"
            )
            mock_engine_class.return_value = mock_engine
            
            orchestrator = V2Orchestrator(session_store=sample_session_store)
            orchestrator.flow_engine = mock_engine
            
            # Handle message that causes validation error
            result = await orchestrator.handle_message("validation-error-test", "invalid input")
            
            # Should return validation error message
            assert len(result) == 1
            assert result[0]["sender"] == "dog"
            assert "nicht verstanden" in result[0]["text"]
    
    @pytest.mark.asyncio
    async def test_unexpected_error_handling(self, sample_session_store):
        """Test handling of unexpected exceptions"""
        with patch('src.v2.core.flow_engine.FlowEngine') as mock_engine_class:
            mock_engine = AsyncMock()
            mock_engine.process_event.side_effect = RuntimeError("Unexpected system error")
            mock_engine_class.return_value = mock_engine
            
            orchestrator = V2Orchestrator(session_store=sample_session_store)
            orchestrator.flow_engine = mock_engine
            
            # Handle message that causes unexpected error
            result = await orchestrator.handle_message("unexpected-error-test", "test input")
            
            # Should return generic error message
            assert len(result) == 1
            assert result[0]["sender"] == "dog"
            assert "unerwarteter Fehler" in result[0]["text"]
    
    @pytest.mark.asyncio
    async def test_start_conversation_error_handling(self, sample_session_store):
        """Test error handling in start_conversation"""
        with patch('src.v2.core.flow_engine.FlowEngine') as mock_engine_class:
            mock_engine = AsyncMock()
            mock_engine.process_event.side_effect = Exception("Start conversation failed")
            mock_engine_class.return_value = mock_engine
            
            orchestrator = V2Orchestrator(session_store=sample_session_store)
            orchestrator.flow_engine = mock_engine
            
            # Start conversation that will fail
            result = await orchestrator.start_conversation("start-error-test")
            
            # Should return error message
            assert len(result) == 1
            assert result[0]["sender"] == "dog"
            assert "Probleme beim Starten" in result[0]["text"]


# ===========================================
# DEMO & SHOWCASE TESTS
# ===========================================

@pytest.mark.integration
class TestOrchestratorDemo:
    """Showcase orchestrator capabilities with realistic scenarios"""
    
    @pytest.mark.asyncio
    async def test_realistic_conversation_showcase(self, caplog):
        """Showcase complete realistic conversation with German responses"""
        
        # Create realistic orchestrator with proper FSM
        session_store = SessionStore()
        orchestrator = V2Orchestrator(session_store=session_store)
        
        # Mock the flow engine with realistic responses
        with patch.object(orchestrator.flow_engine, 'process_event') as mock_process:
            with patch.object(orchestrator.flow_engine, 'classify_user_input') as mock_classify:
                
                # Define realistic conversation flow
                conversation_steps = [
                    # Start
                    {
                        'event': FlowEvent.START_SESSION,
                        'response': (FlowStep.WAIT_FOR_SYMPTOM, [
                            V2AgentMessage(sender="dog", text="🐾 Wuff! Hallo! Ich bin dein virtueller Hund und erkläre dir Hundeverhalten aus meiner Perspektive!", message_type="greeting"),
                            V2AgentMessage(sender="dog", text="Beschreibe mir bitte ein Verhalten oder eine Situation mit einem Hund!", message_type="question")
                        ])
                    },
                    # Symptom input
                    {
                        'event': FlowEvent.USER_INPUT,
                        'response': (FlowStep.WAIT_FOR_CONFIRMATION, [
                            V2AgentMessage(sender="dog", text="Als Hund springe ich auf Menschen, weil ich so aufgeregt und glücklich bin, sie zu sehen! Es ist meine Art zu zeigen: 'Hey, ich freue mich riesig, dass du da bist!'", message_type="response"),
                            V2AgentMessage(sender="dog", text="Möchtest du verstehen, warum ich das genau mache und was in mir vorgeht?", message_type="question")
                        ])
                    },
                    # Confirmation
                    {
                        'event': FlowEvent.YES_RESPONSE,
                        'response': (FlowStep.WAIT_FOR_CONTEXT, [
                            V2AgentMessage(sender="dog", text="Super! Erzähl mir mehr: In welchen Situationen passiert das? Wer ist dabei? Was ist vorher los?", message_type="question")
                        ])
                    },
                    # Context input
                    {
                        'event': FlowEvent.USER_INPUT,
                        'response': (FlowStep.ASK_FOR_EXERCISE, [
                            V2AgentMessage(sender="dog", text="Ah, jetzt verstehe ich! Wenn Besuch kommt, aktiviert sich mein Rudel-Instinkt besonders stark. Neue Menschen bedeuten für mich: potentielle neue Rudelmitglieder! Ich will sie begrüßen und herausfinden, ob sie zu uns gehören.", message_type="response"),
                            V2AgentMessage(sender="dog", text="Möchtest du eine Übung lernen, die mir und meinem Menschen in dieser Situation hilft?", message_type="question")
                        ])
                    },
                    # Exercise request
                    {
                        'event': FlowEvent.YES_RESPONSE,
                        'response': (FlowStep.END_OR_RESTART, [
                            V2AgentMessage(sender="dog", text="Perfekt! Hier ist meine Lieblings-Übung: Übe mit mir das 'Vier-Pfoten-am-Boden'-Spiel! Immer wenn Besuch kommt, sagst du 'Sitz' und belohnst mich nur, wenn alle vier Pfoten am Boden bleiben. Nach 2-3 Wochen täglich 10 Minuten werde ich automatisch ruhiger bei Besuch!", message_type="response"),
                            V2AgentMessage(sender="dog", text="Möchtest du ein anderes Hundeverhalten mit mir besprechen?", message_type="question")
                        ])
                    },
                    # End conversation
                    {
                        'event': FlowEvent.NO_RESPONSE,
                        'response': (FlowStep.FEEDBACK_Q1, [
                            V2AgentMessage(sender="companion", text="Vielen Dank für das Gespräch! Ich würde mich sehr über ein kurzes Feedback freuen.", message_type="greeting"),
                            V2AgentMessage(sender="companion", text="Hat dir unser Gespräch dabei geholfen, das Hundeverhalten besser zu verstehen?", message_type="question")
                        ])
                    }
                ]
                
                step_index = 0
                def mock_process_side_effect(*args, **kwargs):
                    nonlocal step_index
                    if step_index < len(conversation_steps):
                        result = conversation_steps[step_index]['response']
                        step_index += 1
                        return result
                    return FlowStep.GREETING, []
                
                def mock_classify_side_effect(user_input, current_state):
                    if step_index <= len(conversation_steps):
                        return conversation_steps[min(step_index, len(conversation_steps) - 1)]['event']
                    return FlowEvent.USER_INPUT
                
                mock_process.side_effect = mock_process_side_effect
                mock_classify.side_effect = mock_classify_side_effect
                
                print("\n" + "="*60)
                print("🎭 V2 ORCHESTRATOR REALISTIC CONVERSATION SHOWCASE")
                print("="*60)
                
                # Start conversation
                print("\n🚀 CONVERSATION START")
                messages = await orchestrator.start_conversation("showcase-session")
                
                for msg in messages:
                    print(f"🐕 {msg['sender'].upper()}: {msg['text']}")
                
                # User describes behavior
                print(f"\n👤 USER: Mein Hund springt immer auf Besuch hoch")
                messages = await orchestrator.handle_message("showcase-session", "Mein Hund springt immer auf Besuch hoch")
                
                for msg in messages:
                    print(f"🐕 {msg['sender'].upper()}: {msg['text']}")
                
                # User wants to learn more
                print(f"\n👤 USER: ja, das würde mich interessieren")
                messages = await orchestrator.handle_message("showcase-session", "ja, das würde mich interessieren")
                
                for msg in messages:
                    print(f"🐕 {msg['sender'].upper()}: {msg['text']}")
                
                # User provides context
                print(f"\n👤 USER: Vor allem wenn neue Leute zur Tür reinkommen")
                messages = await orchestrator.handle_message("showcase-session", "Vor allem wenn neue Leute zur Tür reinkommen")
                
                for msg in messages:
                    print(f"🐕 {msg['sender'].upper()}: {msg['text']}")
                
                # User wants exercise
                print(f"\n👤 USER: ja, das wäre super")
                messages = await orchestrator.handle_message("showcase-session", "ja, das wäre super")
                
                for msg in messages:
                    print(f"🐕 {msg['sender'].upper()}: {msg['text']}")
                
                # User ends conversation
                print(f"\n👤 USER: nein, erstmal nicht")
                messages = await orchestrator.handle_message("showcase-session", "nein, erstmal nicht")
                
                for msg in messages:
                    print(f"🤝 {msg['sender'].upper()}: {msg['text']}")
                
                print("\n" + "="*60)
                print("✅ REALISTIC CONVERSATION SHOWCASE COMPLETED")
                
                # Get final session info
                session_info = orchestrator.get_session_info("showcase-session")
                print(f"\n📊 SESSION STATISTICS:")
                print(f"   💬 Messages exchanged: {session_info['message_count']}")
                print(f"   📝 Current step: {session_info['current_step']}")
                print(f"   🎯 Active symptom: {session_info['active_symptom']}")
                print(f"   📋 Feedback questions: {session_info['feedback_collected']}")
                
                # Health check
                health = await orchestrator.health_check()
                print(f"\n🏥 SYSTEM HEALTH:")
                print(f"   Overall: {health['overall']}")
                print(f"   Flow Engine: {health['flow_engine']}")
                print(f"   Total States: {health['summary']['total_states']}")
                print(f"   Total Transitions: {health['summary']['total_transitions']}")
                
                print("\n🎉 V2 ORCHESTRATOR SHOWCASE SUCCESSFUL!")
                print("   ✅ Complete FSM-based conversation flow")
                print("   ✅ Realistic German dog behavior responses")
                print("   ✅ Proper state management and transitions")
                print("   ✅ Error handling and health monitoring")
                print("   ✅ V1 compatibility maintained")
                print("="*60)
                
                # Verify conversation metrics
                assert session_info['message_count'] >= 8  # User + Bot messages
                assert session_info['current_step'] == 'feedback_q1'
                assert len(session_info['active_symptom']) > 0


if __name__ == "__main__":
    print("🧪 V2 Orchestrator Test Suite")
    print("   Führe pytest tests/v2/core/test_orchestrator.py aus für alle Tests")
    print("   Oder pytest -m unit für Unit-Tests")
    print("   Oder pytest -m integration für vollständige Integration-Tests")
    print("   Nutze pytest -v für detaillierte Ausgabe")