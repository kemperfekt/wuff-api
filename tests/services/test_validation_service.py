# tests/v2/services/test_validation_service.py
"""
Tests for ValidationService - centralized input validation.
"""

import pytest
from src.services.validation_service import ValidationService, ValidationResult


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
            "Mein Hund bellt ständig wenn Besucher kommen"
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
        assert "too short" in result.message.lower()
        assert result.details['min_length'] == 10
        assert result.details['actual_length'] == 4
    
    @pytest.mark.asyncio
    async def test_symptom_too_short_words(self, validation_service):
        """Test symptom input too short (word count)"""
        result = await validation_service.validate_symptom_input("Hund bellt")
        
        assert result.valid is False
        assert result.error_type == "input_too_short"
        assert "more detail" in result.message
        assert result.details['word_count'] == 2
    
    @pytest.mark.asyncio
    async def test_symptom_edge_cases(self, validation_service):
        """Test symptom validation edge cases"""
        # Exactly 10 characters
        result = await validation_service.validate_symptom_input("1234567890")
        assert result.valid is False  # Still needs more words
        
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
            "Es passiert immer wenn es an der Tür klingelt"
        )
        
        assert result.valid is True
        assert result.error_type is None
    
    @pytest.mark.asyncio
    async def test_context_too_short(self, validation_service):
        """Test context input too short"""
        result = await validation_service.validate_context_input("oft")
        
        assert result.valid is False
        assert result.error_type == "context_too_short"
        assert "too short" in result.message.lower()
        assert result.details['min_length'] == 5
        assert result.details['actual_length'] == 3
    
    @pytest.mark.asyncio
    async def test_context_edge_cases(self, validation_service):
        """Test context validation edge cases"""
        # Exactly 5 characters
        result = await validation_service.validate_context_input("12345")
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
    
    @pytest.mark.asyncio
    async def test_feedback_email_validation(self, validation_service):
        """Test email validation for feedback question 5"""
        # Valid emails
        valid_emails = ["test@example.com", "user.name@domain.co.uk"]
        for email in valid_emails:
            result = await validation_service.validate_feedback_response(
                email,
                question_number=5
            )
            assert result.valid is True
        
        # Invalid emails
        invalid_emails = ["not-an-email", "missing-at.com", "@no-user.com", "no-dot@example"]
        for email in invalid_emails:
            result = await validation_service.validate_feedback_response(
                email,
                question_number=5
            )
            assert result.valid is False
            assert result.error_type == "invalid_email"
            assert "valid email" in result.message