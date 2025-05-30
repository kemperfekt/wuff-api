# src/v2/services/validation_service.py
"""
Input Validation Service for WuffChat V2.

Centralizes all business rule validation to maintain clean separation of concerns.
Flow Engine handles state transitions, Handlers coordinate business logic,
and this service validates inputs.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of input validation"""
    valid: bool
    error_type: Optional[str] = None
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class ValidationService:
    """
    Centralized validation service for all user inputs.
    
    This service handles all business rule validation, keeping validation
    logic separate from flow control and message formatting.
    """
    
    def __init__(self):
        self.logger = logger
        
    async def validate_symptom_input(self, user_input: str) -> ValidationResult:
        """
        Validate symptom description input.
        
        Args:
            user_input: User's symptom description
            
        Returns:
            ValidationResult with validation outcome
        """
        user_input = user_input.strip()
        
        # Check minimum length
        if len(user_input) < 10:
            return ValidationResult(
                valid=False,
                error_type="input_too_short",
                message=f"Symptom description too short: {len(user_input)} characters (minimum: 10)",
                details={"min_length": 10, "actual_length": len(user_input), "error_type": "input_too_short"}
            )
        
        # Check if input seems to be dog-related (basic check)
        if len(user_input.split()) < 3:
            return ValidationResult(
                valid=False,
                error_type="input_too_short", 
                message="Symptom description should contain more detail",
                details={"word_count": len(user_input.split()), "error_type": "input_too_short"}
            )
        
        return ValidationResult(valid=True)
    
    async def validate_context_input(self, user_input: str) -> ValidationResult:
        """
        Validate context description input.
        
        Args:
            user_input: User's context description
            
        Returns:
            ValidationResult with validation outcome
        """
        user_input = user_input.strip()
        
        # Check minimum length for context
        if len(user_input) < 5:
            return ValidationResult(
                valid=False,
                error_type="context_too_short",
                message=f"Context description too short: {len(user_input)} characters (minimum: 5)",
                details={"min_length": 5, "actual_length": len(user_input), "error_type": "context_too_short"}
            )
        
        return ValidationResult(valid=True)
    
    async def validate_yes_no_response(self, user_input: str) -> ValidationResult:
        """
        Validate yes/no response.
        
        Args:
            user_input: User's response
            
        Returns:
            ValidationResult with validation outcome and classification
        """
        normalized_input = user_input.lower().strip()
        
        # Check for yes responses
        if "ja" in normalized_input or "yes" in normalized_input:
            return ValidationResult(
                valid=True,
                details={"response_type": "yes"}
            )
        
        # Check for no responses  
        if "nein" in normalized_input or "no" in normalized_input:
            return ValidationResult(
                valid=True,
                details={"response_type": "no"}
            )
        
        # Invalid yes/no response
        return ValidationResult(
            valid=False,
            error_type="invalid_yes_no",
            message=f"Invalid yes/no response: '{user_input}'",
            details={"expected": ["ja", "nein"], "received": user_input, "error_type": "invalid_yes_no"}
        )
    
    async def validate_feedback_response(self, user_input: str, question_number: int) -> ValidationResult:
        """
        Validate feedback response.
        
        Args:
            user_input: User's feedback response
            question_number: Which feedback question (1-5)
            
        Returns:
            ValidationResult with validation outcome
        """
        user_input = user_input.strip()
        
        # Basic length check
        if len(user_input) < 1:
            return ValidationResult(
                valid=False,
                error_type="feedback_too_short",
                message="Feedback response cannot be empty",
                details={"question_number": question_number}
            )
        
        # Special validation for email (question 5)
        if question_number == 5:
            # Basic email validation: check for @ and . in proper positions
            at_index = user_input.find("@")
            if at_index == -1 or at_index == 0:
                return ValidationResult(
                    valid=False,
                    error_type="invalid_email",
                    message="Please provide a valid email address",
                    details={"question_number": question_number}
                )
            
            # Check for dot after @ symbol
            domain_part = user_input[at_index + 1:]
            if "." not in domain_part or domain_part.startswith(".") or domain_part.endswith("."):
                return ValidationResult(
                    valid=False,
                    error_type="invalid_email",
                    message="Please provide a valid email address",
                    details={"question_number": question_number}
                )
        
        return ValidationResult(valid=True)