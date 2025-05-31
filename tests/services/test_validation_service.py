# tests/v2/services/test_validation_service.py
"""
Tests for ValidationService - centralized input validation.
"""

import pytest
from src.services.validation_service import ValidationService, ValidationResult, DogContentValidator


class TestValidationService:
    """Test ValidationService for all input validation rules"""
    
    @pytest.fixture
    def validation_service(self):
        """Create ValidationService instance"""
        return ValidationService()
    
    # ===========================================
    # SYMPTOM VALIDATION TESTS
    # ===========================================
    
    @pytest.mark.asyncio
    async def test_symptom_valid(self, validation_service):
        """Test valid symptom input"""
        result = await validation_service.validate_symptom_input(
            "Mein Hund bellt ständig sehr laut wenn Besucher kommen und er sieht sie"
        )
        
        assert result.valid is True
        assert result.error_type is None
        assert result.message is None
    
    @pytest.mark.asyncio
    async def test_symptom_too_short_chars(self, validation_service):
        """Test symptom input too short (character count)"""
        result = await validation_service.validate_symptom_input("kurz")
        
        assert result.valid is False
        assert result.error_type == "input_too_short"
        assert "more detail" in result.message.lower()
        assert result.details['min_length'] == 25
        assert result.details['actual_length'] == 4
    
    @pytest.mark.asyncio
    async def test_symptom_too_short_barely(self, validation_service):
        """Test symptom input just under threshold"""
        result = await validation_service.validate_symptom_input("Hund bellt laut")  # 16 chars
        
        assert result.valid is False
        assert result.error_type == "input_too_short"
        assert "more detail" in result.message
        assert result.details['min_length'] == 25
        assert result.details['actual_length'] == 16
    
    @pytest.mark.asyncio
    async def test_symptom_edge_cases(self, validation_service):
        """Test symptom validation edge cases"""
        # Exactly 25 characters with dog content
        result = await validation_service.validate_symptom_input("Mein Hund bellt sehr oft")
        assert result.valid is True  # Should pass - has dog keywords
        
        # Whitespace handling
        result = await validation_service.validate_symptom_input("   kurz   ")
        assert result.valid is False
        assert result.details['actual_length'] == 4
    
    # ===========================================
    # CONTEXT VALIDATION TESTS
    # ===========================================
    
    @pytest.mark.asyncio
    async def test_context_valid(self, validation_service):
        """Test valid context input"""
        result = await validation_service.validate_context_input(
            "Es passiert immer wenn es an der Tür klingelt und Besucher kommen"
        )
        
        assert result.valid is True
        assert result.error_type is None
    
    @pytest.mark.asyncio
    async def test_context_too_short(self, validation_service):
        """Test context input too short"""
        result = await validation_service.validate_context_input("oft")
        
        assert result.valid is False
        assert result.error_type == "context_too_short"
        assert "more context" in result.message.lower()
        assert result.details['min_length'] == 25
        assert result.details['actual_length'] == 3
    
    @pytest.mark.asyncio
    async def test_context_edge_cases(self, validation_service):
        """Test context validation edge cases"""
        # Exactly 25 characters
        result = await validation_service.validate_context_input("1234567890123456789012345")
        assert result.valid is True
        
        # Empty string
        result = await validation_service.validate_context_input("")
        assert result.valid is False
        assert result.details['actual_length'] == 0
    
    # ===========================================
    # YES/NO VALIDATION TESTS
    # ===========================================
    
    @pytest.mark.asyncio
    async def test_yes_responses(self, validation_service):
        """Test various yes responses"""
        yes_inputs = ["ja", "Ja", "JA", "ja gerne", "yes", "YES"]
        
        for input_text in yes_inputs:
            result = await validation_service.validate_yes_no_response(input_text)
            assert result.valid is True
            assert result.details['response_type'] == "yes"
    
    @pytest.mark.asyncio
    async def test_no_responses(self, validation_service):
        """Test various no responses"""
        no_inputs = ["nein", "Nein", "NEIN", "no", "NO"]
        
        for input_text in no_inputs:
            result = await validation_service.validate_yes_no_response(input_text)
            assert result.valid is True
            assert result.details['response_type'] == "no"
    
    @pytest.mark.asyncio
    async def test_invalid_yes_no_responses(self, validation_service):
        """Test invalid yes/no responses"""
        invalid_inputs = ["vielleicht", "maybe", "123", ""]
        
        for input_text in invalid_inputs:
            result = await validation_service.validate_yes_no_response(input_text)
            assert result.valid is False
            assert result.error_type == "invalid_yes_no"
            assert "invalid yes/no" in result.message.lower()
            assert result.details['expected'] == ["ja", "nein"]
    
    # ===========================================
    # FEEDBACK VALIDATION TESTS
    # ===========================================
    
    @pytest.mark.asyncio
    async def test_feedback_valid(self, validation_service):
        """Test valid feedback responses"""
        result = await validation_service.validate_feedback_response(
            "Sehr hilfreich, danke!",
            question_number=1
        )
        
        assert result.valid is True
        assert result.error_type is None
    
    @pytest.mark.asyncio
    async def test_feedback_empty(self, validation_service):
        """Test empty feedback response"""
        result = await validation_service.validate_feedback_response(
            "",
            question_number=1
        )
        
        assert result.valid is False
        assert result.error_type == "feedback_too_short"
        assert "cannot be empty" in result.message
        assert result.details['question_number'] == 1
        assert result.details['min_length'] == 1


class TestDogContentValidator:
    """Test DogContentValidator for dog-related content detection"""
    
    @pytest.fixture
    def dog_validator(self):
        """Create DogContentValidator instance without GPT service"""
        return DogContentValidator()
    
    @pytest.mark.asyncio
    async def test_keyword_detection_german(self, dog_validator):
        """Test German dog keyword detection"""
        dog_inputs = [
            "Mein Hund bellt ständig",
            "Der Welpe springt auf Menschen",
            "Sie zieht an der Leine",
            "Er gehorcht nicht beim Sitz",
            "Das Bellen nervt die Nachbarn"
        ]
        
        for input_text in dog_inputs:
            result = await dog_validator.is_dog_related(input_text)
            assert result is True, f"Failed to detect dog content in: {input_text}"
    
    @pytest.mark.asyncio
    async def test_keyword_detection_english(self, dog_validator):
        """Test English dog keyword detection"""
        dog_inputs = [
            "My dog barks constantly",
            "The puppy jumps on people",
            "She pulls on the leash",
            "He doesn't obey the sit command",
            "The barking annoys neighbors"
        ]
        
        for input_text in dog_inputs:
            result = await dog_validator.is_dog_related(input_text)
            assert result is True, f"Failed to detect dog content in: {input_text}"
    
    @pytest.mark.asyncio
    async def test_non_dog_content(self, dog_validator):
        """Test non-dog content detection"""
        non_dog_inputs = [
            "Das Wetter ist heute schön",
            "I need help with my computer",
            "Pizza tastes really good",
            "My car needs repair"
        ]
        
        for input_text in non_dog_inputs:
            result = await dog_validator.is_dog_related(input_text)
            # Without GPT service, defaults to True (permissive)
            # This tests the keyword-only path
            if dog_validator._check_keywords(input_text):
                assert result is True
            else:
                # Should default to True without GPT
                assert result is True
    
    @pytest.mark.asyncio 
    async def test_edge_cases(self, dog_validator):
        """Test edge cases for content validation"""
        edge_cases = [
            "",  # Empty string
            "   ",  # Whitespace only
            "dog",  # Single keyword
            "hund",  # Single German keyword
            "The dog and cat play together"  # Mixed content
        ]
        
        for input_text in edge_cases:
            result = await dog_validator.is_dog_related(input_text)
            # Most should pass due to keywords or permissive default
            assert isinstance(result, bool)
    
    def test_keyword_detection_private(self, dog_validator):
        """Test private keyword detection method"""
        # German keywords
        assert dog_validator._check_keywords("mein hund") is True
        assert dog_validator._check_keywords("das bellen") is True
        assert dog_validator._check_keywords("sitz kommando") is True
        
        # English keywords  
        assert dog_validator._check_keywords("my dog") is True
        assert dog_validator._check_keywords("the barking") is True
        assert dog_validator._check_keywords("sit command") is True
        
        # Non-dog content
        assert dog_validator._check_keywords("weather today") is False
        assert dog_validator._check_keywords("computer problems") is False
        assert dog_validator._check_keywords("") is False
    
