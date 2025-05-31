# src/v2/services/validation_service.py
"""
Input Validation Service for WuffChat V2.

Centralizes all business rule validation to maintain clean separation of concerns.
Flow Engine handles state transitions, Handlers coordinate business logic,
and this service validates inputs.
"""

from typing import Optional, Dict, Any, Set, TYPE_CHECKING
from dataclasses import dataclass
import logging
import re

if TYPE_CHECKING:
    from src.services.gpt_service import GPTService

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of input validation"""
    valid: bool
    error_type: Optional[str] = None
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class DogContentValidator:
    """
    Validates if user input is related to dog behavior/training.
    
    Uses a hybrid approach:
    1. Fast keyword matching for common dog terms
    2. GPT validation as fallback for edge cases
    """
    
    # Dog-related keywords for fast validation
    DOG_KEYWORDS: Dict[str, Set[str]] = {
        'de': {
            'hund', 'hunde', 'welpe', 'welpen', 'rüde', 'hündin', 'vierbeiner',
            'bellen', 'bellt', 'gebell', 'beißen', 'beißt', 'knurren', 'knurrt',
            'winseln', 'winselt', 'jaulen', 'jault', 'heulen', 'heult',
            'schwanz', 'rute', 'pfote', 'pfoten', 'schnauze', 'nase',
            'schnüffeln', 'schnüffelt', 'lecken', 'leckt', 'sabbern', 'sabbert',
            'springen', 'springt', 'hüpfen', 'hüpft', 'rennen', 'rennt', 'laufen', 'läuft',
            'ziehen', 'zieht', 'zerren', 'zerrt', 'ziehen', 'zieht',
            'gehorchen', 'gehorcht', 'folgen', 'folgt', 'hören', 'hört',
            'sitz', 'platz', 'bleib', 'fuß', 'hier', 'komm', 'aus', 'nein',
            'apportieren', 'apportiert', 'bringen', 'bringt', 'holen', 'holt',
            'jagen', 'jagt', 'hetzen', 'hetzt', 'verfolgen', 'verfolgt',
            'fressen', 'frisst', 'essen', 'isst', 'futter', 'leckerli', 'leckerchen',
            'gassi', 'spaziergang', 'spazieren', 'leine', 'halsband', 'geschirr',
            'spielen', 'spielt', 'toben', 'tobt', 'ball', 'spielzeug', 'stock',
            'hundeschule', 'training', 'erziehung', 'kommando', 'tricks'
        },
        'en': {
            'dog', 'dogs', 'puppy', 'puppies', 'canine', 'pup', 'pooch',
            'bark', 'barking', 'barks', 'bite', 'biting', 'bites', 'growl', 'growling',
            'whine', 'whining', 'howl', 'howling', 'yelp', 'yelping',
            'tail', 'paw', 'paws', 'snout', 'muzzle', 'nose',
            'sniff', 'sniffing', 'lick', 'licking', 'drool', 'drooling',
            'jump', 'jumping', 'jumps', 'run', 'running', 'runs',
            'pull', 'pulling', 'pulls', 'tug', 'tugging',
            'obey', 'obeys', 'follow', 'follows', 'listen', 'listens',
            'sit', 'stay', 'down', 'heel', 'come', 'fetch', 'drop',
            'retrieve', 'retrieves', 'bring', 'brings', 'get',
            'chase', 'chasing', 'hunt', 'hunting', 'track', 'tracking',
            'eat', 'eating', 'eats', 'food', 'treat', 'treats', 'kibble',
            'walk', 'walking', 'walks', 'leash', 'collar', 'harness',
            'play', 'playing', 'plays', 'ball', 'toy', 'stick',
            'training', 'train', 'command', 'commands', 'trick', 'tricks'
        }
    }
    
    def __init__(self, gpt_service: Optional["GPTService"] = None):
        self.gpt_service = gpt_service
        self.logger = logging.getLogger(f"{__name__}.DogContentValidator")
    
    async def is_dog_related(self, user_input: str) -> bool:
        """
        Check if input is related to dog behavior using hybrid approach.
        
        Args:
            user_input: User's input to validate
            
        Returns:
            True if input appears to be dog-related, False otherwise
        """
        # Step 1: Fast keyword check
        if self._check_keywords(user_input):
            self.logger.debug("Dog content detected via keywords")
            return True
        
        # Step 2: GPT fallback for edge cases
        if self.gpt_service:
            try:
                is_dog_related = await self._check_with_gpt(user_input)
                self.logger.debug(f"Dog content GPT check result: {is_dog_related}")
                return is_dog_related
            except Exception as e:
                self.logger.warning(f"GPT dog content check failed: {e}")
                # Default to allowing input if GPT fails
                return True
        
        # No GPT service available, be permissive
        self.logger.debug("No GPT service available, defaulting to allowing input")
        return True
    
    def _check_keywords(self, user_input: str) -> bool:
        """
        Fast keyword-based dog content detection using word boundaries.
        
        Args:
            user_input: Input text to check
            
        Returns:
            True if dog-related keywords found, False otherwise
        """
        text_lower = user_input.lower()
        
        # Check German keywords with word boundaries
        for keyword in self.DOG_KEYWORDS['de']:
            # Use word boundaries to avoid partial matches (e.g., "eat" in "weather")
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text_lower):
                return True
        
        # Check English keywords with word boundaries
        for keyword in self.DOG_KEYWORDS['en']:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    async def _check_with_gpt(self, user_input: str) -> bool:
        """
        Use GPT to validate dog-related content.
        
        Args:
            user_input: Input text to validate
            
        Returns:
            True if GPT determines input is dog-related, False otherwise
        """
        if not self.gpt_service:
            return True
        
        validation_prompt = f"Ist das Hundeverhalten? Antworte nur 'ja' oder 'nein':\n{user_input}"
        
        response = await self.gpt_service.complete(
            prompt=validation_prompt,
            temperature=0.3,  # More permissive than 0.0
            max_tokens=3      # Only need "ja" or "nein"
        )
        
        # Check if response contains "ja" (dog-related)
        return "ja" in response.lower().strip()


class ValidationService:
    """
    Centralized validation service for all user inputs.
    
    This service handles all business rule validation, keeping validation
    logic separate from flow control and message formatting.
    
    Validation strategy:
    1. Length validation first (performance)
    2. Content validation second (accuracy)
    3. Graceful degradation on service failures
    """
    
    # Validation thresholds
    MIN_SYMPTOM_LENGTH = 25      # Substantial input required
    MIN_CONTEXT_LENGTH = 25      # Context needs detail too
    MIN_FEEDBACK_LENGTH = 1      # Feedback can be brief
    
    def __init__(self, gpt_service: Optional["GPTService"] = None):
        self.logger = logger
        self.dog_content_validator = DogContentValidator(gpt_service)
        
    async def validate_symptom_input(self, user_input: str) -> ValidationResult:
        """
        Validate symptom description input.
        
        Validation order (performance-optimized):
        1. Length check first (fast, eliminates short inputs)
        2. Content validation second (only for qualified inputs)
        
        Args:
            user_input: User's symptom description
            
        Returns:
            ValidationResult with validation outcome
        """
        user_input = user_input.strip()
        
        # Step 1: Length validation FIRST (performance optimization)
        if len(user_input) < self.MIN_SYMPTOM_LENGTH:
            return ValidationResult(
                valid=False,
                error_type="input_too_short",
                message="Please describe the behavior in more detail (at least 25 characters)",
                details={
                    "min_length": self.MIN_SYMPTOM_LENGTH,
                    "actual_length": len(user_input),
                    "error_type": "input_too_short"
                }
            )
        
        # Step 2: Content validation ONLY for qualified inputs (cost optimization)
        try:
            is_dog_related = await self.dog_content_validator.is_dog_related(user_input)
            if not is_dog_related:
                return ValidationResult(
                    valid=False,
                    error_type="not_dog_related",
                    message="Please describe a dog behavior or situation with your dog",
                    details={
                        "error_type": "not_dog_related",
                        "input_preview": user_input[:50]
                    }
                )
        except Exception as e:
            # Graceful degradation: continue if content validation fails
            self.logger.warning(f"Dog content validation failed, continuing: {e}")
        
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
        
        # Check minimum length for context - needs substantial detail
        if len(user_input) < self.MIN_CONTEXT_LENGTH:
            return ValidationResult(
                valid=False,
                error_type="context_too_short",
                message=f"Please provide more context details (at least {self.MIN_CONTEXT_LENGTH} characters)",
                details={
                    "min_length": self.MIN_CONTEXT_LENGTH,
                    "actual_length": len(user_input),
                    "error_type": "context_too_short"
                }
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
        if len(user_input) < self.MIN_FEEDBACK_LENGTH:
            return ValidationResult(
                valid=False,
                error_type="feedback_too_short",
                message="Feedback response cannot be empty",
                details={
                    "question_number": question_number,
                    "min_length": self.MIN_FEEDBACK_LENGTH
                }
            )
        
        # Question 5 is optional contact info (email OR phone) - no validation needed
        # Users can enter email, phone, or even skip with "keine" etc.
        return ValidationResult(valid=True)
    
