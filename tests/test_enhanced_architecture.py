# tests/test_enhanced_architecture.py

"""
Tests for the enhanced agentic architecture components.

This test suite validates that the new architecture components work correctly
and integrate properly for natural conversation flow.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.models.unified_state import UnifiedConversationState, HandoffPackage
from src.core.conversation_memory import ConversationMemory, ConversationTurn, ExtractedFact
from src.core.information_extractor import InformationExtractor
from src.core.adaptive_conversation_planner import AdaptiveConversationPlanner
from src.core.handoff_manager import HandoffManager
from src.agents.enhanced_agentic_dog_agent import EnhancedAgenticDogAgent
from src.models.agentic_models import ConversationPhase


class TestConversationMemory:
    """Test the ConversationMemory system"""
    
    def test_memory_initialization(self):
        """Test memory initializes correctly"""
        memory = ConversationMemory()
        
        assert memory.turn_counter == 0
        assert len(memory.turns) == 0
        assert len(memory.extracted_facts) == 0
    
    def test_add_turn_with_extraction(self):
        """Test adding a turn with extracted information"""
        memory = ConversationMemory()
        
        extracted_info = {
            "dog_name": "Max",
            "confidence": {"dog_name": 0.9}
        }
        
        memory.add_turn(
            user_input="Mein Hund heißt Max",
            agent_response="*aufmerksam* Hallo Max!",
            extracted_info=extracted_info
        )
        
        assert memory.turn_counter == 1
        assert len(memory.turns) == 1
        assert "dog_name" in memory.extracted_facts
        assert memory.extracted_facts["dog_name"].value == "Max"
        assert memory.extracted_facts["dog_name"].confidence == 0.9
    
    def test_get_missing_information(self):
        """Test missing information detection"""
        memory = ConversationMemory()
        
        # Add partial information
        extracted_info = {
            "dog_name": "Max",
            "dog_breed": "Labrador",
            "confidence": {"dog_name": 0.9, "dog_breed": 0.8}
        }
        
        memory.add_turn("", "", extracted_info)
        
        missing = memory.get_missing_information()
        assert "main_concern" in missing
        assert "dog_name" not in missing
        assert "dog_breed" not in missing
    
    def test_context_summary(self):
        """Test context summary generation"""
        memory = ConversationMemory()
        
        # Add some conversation
        memory.add_turn(
            "Mein Golden Retriever Max bellt ständig",
            "*verständnisvoll* Erzähl mir mehr über Max.",
            {
                "dog_name": "Max",
                "dog_breed": "Golden Retriever", 
                "main_concern": "bellt ständig",
                "confidence": {"dog_name": 0.9, "dog_breed": 0.9, "main_concern": 0.8}
            }
        )
        
        summary = memory.get_context_summary()
        
        assert "Max" in summary
        assert "Golden Retriever" in summary
        assert "bellt ständig" in summary
        assert "Conversation length: 1 turns" in summary


class TestUnifiedConversationState:
    """Test the UnifiedConversationState model"""
    
    def test_state_initialization(self):
        """Test state initializes correctly"""
        state = UnifiedConversationState(session_id="test-123")
        
        assert state.session_id == "test-123"
        assert state.current_phase == ConversationPhase.COLLECTING
        assert state.dog_name is None
        assert state.get_completion_percentage() == 0.0
    
    def test_update_from_extraction(self):
        """Test updating state from extraction results"""
        state = UnifiedConversationState(session_id="test-123")
        
        extraction_result = {
            "dog_name": "Bella",
            "dog_breed": "Border Collie",
            "confidence": {"dog_name": 0.9, "dog_breed": 0.85}
        }
        
        state.update_from_extraction(extraction_result)
        
        assert state.dog_name == "Bella"
        assert state.dog_breed == "Border Collie"
        assert state.confidence["dog_name"] == 0.9
        assert state.confidence["dog_breed"] == 0.85
        assert state.get_completion_percentage() > 0
    
    def test_readiness_for_perspective(self):
        """Test perspective readiness check"""
        state = UnifiedConversationState(session_id="test-123")
        
        # Not ready initially
        assert not state.is_ready_for_perspective()
        
        # Add all required information
        state.dog_name = "Rex"
        state.dog_breed = "German Shepherd"
        state.main_concern = "aggression towards strangers"
        state.confidence = {"dog_name": 0.9, "dog_breed": 0.8, "main_concern": 0.85}
        
        # Now ready
        assert state.is_ready_for_perspective()
    
    def test_handoff_dict_generation(self):
        """Test handoff dictionary generation"""
        state = UnifiedConversationState(session_id="test-123")
        
        # Set up complete state
        state.dog_name = "Luna"
        state.dog_breed = "Husky"
        state.main_concern = "excessive barking"
        state.dog_perspective = "Luna is protecting her territory"
        state.llm_calls_count = 5
        state.total_tokens_used = 1200
        
        handoff_dict = state.to_handoff_dict()
        
        assert handoff_dict["dog_name"] == "Luna"
        assert handoff_dict["dog_breed"] == "Husky"
        assert handoff_dict["symptom"] == "excessive barking"
        assert handoff_dict["dog_perspective"] == "Luna is protecting her territory"
        assert handoff_dict["metadata"]["llm_calls"] == 5
        assert handoff_dict["metadata"]["tokens_used"] == 1200


class TestInformationExtractor:
    """Test the InformationExtractor"""
    
    @pytest.fixture
    def mock_gpt_service(self):
        """Mock GPT service for testing"""
        service = AsyncMock()
        return service
    
    @pytest.fixture
    def extractor(self, mock_gpt_service):
        """Create extractor with mocked service"""
        return InformationExtractor(mock_gpt_service)
    
    @pytest.mark.asyncio
    async def test_extraction_with_valid_json(self, extractor, mock_gpt_service):
        """Test extraction with valid JSON response"""
        # Mock GPT response
        mock_response = json.dumps({
            "dog_name": "Buddy",
            "dog_breed": "Golden Retriever",
            "main_concern": "jumps on visitors",
            "user_name": None,
            "confidence": {
                "dog_name": 0.95,
                "dog_breed": 0.9,
                "main_concern": 0.85,
                "user_name": 0.0
            },
            "reasoning": "Clear mention of dog name and breed"
        })
        
        mock_gpt_service.complete.return_value = mock_response
        
        # Mock conversation context
        from src.models.agentic_models import ConversationContext, InformationStatus
        context = ConversationContext()
        context.information_status = InformationStatus()
        
        result = await extractor.extract_from_input(
            "Mein Golden Retriever Buddy springt immer auf Besucher",
            context
        )
        
        assert result["dog_name"] == "Buddy"
        assert result["dog_breed"] == "Golden Retriever"
        assert result["main_concern"] == "jumps on visitors"
        assert result["confidence"]["dog_name"] == 0.95
    
    @pytest.mark.asyncio
    async def test_breed_normalization(self, extractor):
        """Test breed name normalization using LLM+Weaviate architecture"""
        # Test that the method returns reasonable results
        # (Exact results depend on LLM response and Weaviate data)
        
        # Test that it returns a string for valid inputs
        result = await extractor._normalize_breed("golden retriever")
        assert isinstance(result, str)
        assert len(result) > 0
        
        result = await extractor._normalize_breed("mix")
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Test empty/invalid inputs
        assert await extractor._normalize_breed("") is None
        assert await extractor._normalize_breed("x") is None
        
        # Test that it handles reasonable breed input
        result = await extractor._normalize_breed("labrador")
        assert isinstance(result, str)
        assert len(result) > 1


class TestAdaptiveConversationPlanner:
    """Test the AdaptiveConversationPlanner"""
    
    @pytest.fixture
    def mock_gpt_service(self):
        """Mock GPT service"""
        service = AsyncMock()
        return service
    
    @pytest.fixture
    def planner(self, mock_gpt_service):
        """Create planner with mocked service"""
        return AdaptiveConversationPlanner(mock_gpt_service)
    
    @pytest.mark.asyncio
    async def test_plan_next_response_missing_info(self, planner, mock_gpt_service):
        """Test planning when information is missing"""
        # Mock GPT response for question generation
        mock_gpt_service.complete.return_value = "*neugierig* Wie heißt denn dein Hund?"
        
        # Create state with missing dog name
        state = UnifiedConversationState(session_id="test")
        state.dog_breed = "Beagle"
        state.main_concern = "barks too much"
        state.confidence = {"dog_breed": 0.8, "main_concern": 0.9}
        
        action_plan = await planner.plan_next_response(state)
        
        assert action_plan.information_needed == "dog_name"
        assert not action_plan.should_handoff
        assert "Wie heißt" in action_plan.next_question
    
    def test_prioritize_missing_field(self, planner):
        """Test field prioritization logic"""
        state = UnifiedConversationState(session_id="test")
        
        # Test normal priority order
        missing = ["dog_breed", "dog_name", "main_concern"]
        priority = planner._prioritize_missing_field(missing, state)
        assert priority == "dog_name"
        
        # Test when we have concern but no dog name
        state.main_concern = "aggressive behavior"
        state.confidence["main_concern"] = 0.9
        missing = ["dog_name", "dog_breed"]
        priority = planner._prioritize_missing_field(missing, state)
        assert priority == "dog_name"


class TestHandoffManager:
    """Test the HandoffManager"""
    
    @pytest.fixture
    def handoff_manager(self):
        """Create handoff manager"""
        return HandoffManager()
    
    @pytest.mark.asyncio
    async def test_prepare_handoff_success(self, handoff_manager):
        """Test successful handoff preparation"""
        # Create ready state
        state = UnifiedConversationState(session_id="test-123")
        state.dog_name = "Oscar"
        state.dog_breed = "Poodle"
        state.main_concern = "separation anxiety"
        state.confidence = {"dog_name": 0.9, "dog_breed": 0.85, "main_concern": 0.9}
        state.perspective_generated = True
        state.dog_perspective = "Oscar feels anxious when alone"
        
        package = await handoff_manager.prepare_handoff(state)
        
        assert package.dog_name == "Oscar"
        assert package.dog_breed == "Poodle"
        assert package.symptom == "separation anxiety"
        assert package.dog_perspective == "Oscar feels anxious when alone"
        assert package.validated
    
    @pytest.mark.asyncio
    async def test_prepare_handoff_missing_info(self, handoff_manager):
        """Test handoff preparation with missing information"""
        # Create incomplete state
        state = UnifiedConversationState(session_id="test-123")
        state.dog_name = "Fido"
        # Missing breed and concern
        
        with pytest.raises(Exception):  # Should raise HandoffError
            await handoff_manager.prepare_handoff(state)
    
    def test_validate_handoff_readiness(self, handoff_manager):
        """Test handoff readiness validation"""
        state = UnifiedConversationState(session_id="test-123")
        
        # Not ready initially
        readiness = handoff_manager.validate_handoff_readiness(state)
        assert not readiness["ready"]
        assert len(readiness["missing_fields"]) > 0
        assert readiness["completion_percentage"] == 0.0
        
        # Make ready
        state.dog_name = "Spot"
        state.dog_breed = "Dalmatian"
        state.main_concern = "hyperactivity"
        state.confidence = {"dog_name": 0.9, "dog_breed": 0.8, "main_concern": 0.85}
        state.perspective_generated = True
        state.handoff_ready = True
        
        readiness = handoff_manager.validate_handoff_readiness(state)
        assert readiness["ready"]
        assert len(readiness["missing_fields"]) == 0
        assert readiness["completion_percentage"] == 100.0


class TestHandoffPackage:
    """Test the HandoffPackage model"""
    
    def test_package_validation_success(self):
        """Test successful package validation"""
        package = HandoffPackage(
            session_id="test-123",
            user_name="John",
            dog_name="Rex",
            dog_breed="Rottweiler",
            symptom="resource guarding behavior",
            conversation_summary="Dog shows aggression around food"
        )
        
        assert package.validate()
        assert len(package.validation_errors) == 0
    
    def test_package_validation_failure(self):
        """Test package validation with missing data"""
        package = HandoffPackage(
            session_id="test-123",
            user_name="Jane",
            dog_name="",  # Missing
            dog_breed="Terrier",
            symptom="",  # Missing
            conversation_summary="Short conversation"
        )
        
        assert not package.validate()
        assert len(package.validation_errors) > 0
        assert any("dog name" in error.lower() for error in package.validation_errors)
        assert any("symptom" in error.lower() for error in package.validation_errors)
    
    def test_package_serialization(self):
        """Test package dictionary conversion"""
        package = HandoffPackage(
            session_id="test-123",
            user_name="Alice",
            dog_name="Luna",
            dog_breed="Border Collie",
            symptom="excessive barking at night",
            conversation_summary="Luna barks when hearing noises",
            metadata={"turns": 4, "duration": 120}
        )
        
        package.validate()
        package_dict = package.to_dict()
        
        assert package_dict["dog_name"] == "Luna"
        assert package_dict["dog_breed"] == "Border Collie"
        assert package_dict["metadata"]["turns"] == 4
        assert package_dict["validated"] is True


# Integration test
class TestArchitectureIntegration:
    """Test integration between components"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_conversation_flow(self):
        """Test a complete conversation flow using new components"""
        # This would be a more complex integration test
        # For now, just test that components can be instantiated together
        
        with patch('src.services.gpt_service.GPTService') as mock_gpt:
            with patch('src.services.weaviate_service.WeaviateService') as mock_weaviate:
                # Mock the services
                mock_gpt_instance = AsyncMock()
                mock_weaviate_instance = AsyncMock()
                mock_gpt.return_value = mock_gpt_instance
                mock_weaviate.return_value = mock_weaviate_instance
                
                # Create enhanced agent
                agent = EnhancedAgenticDogAgent(
                    gpt_service=mock_gpt_instance,
                    weaviate_service=mock_weaviate_instance
                )
                
                # Test that agent can be created without errors
                assert agent is not None
                assert agent.information_extractor is not None
                assert agent.conversation_planner is not None
                assert agent.handoff_manager is not None


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])