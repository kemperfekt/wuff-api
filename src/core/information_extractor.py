# src/core/information_extractor.py

"""
Information Extractor - LLM-based extraction of user information from natural conversation.

This module provides intelligent extraction of dog information from user messages,
replacing the simple string matching with a more robust NLP approach.
"""

import json
import logging
from typing import Dict, Any, Optional
from src.services.gpt_service import GPTService
from src.models.agentic_models import ConversationContext
from src.core.exceptions import V2ServiceError

logger = logging.getLogger(__name__)


class InformationExtractor:
    """
    Extracts structured information from user input using LLM.
    
    Handles extraction of:
    - Dog name
    - Dog breed
    - Behavioral concerns/symptoms
    - User name (optional)
    
    Provides confidence scores for each extracted piece of information.
    """
    
    def __init__(self, gpt_service: GPTService):
        self.gpt = gpt_service
        self.logger = logging.getLogger(f"{__name__}.InformationExtractor")
        
        # Common breed variations for validation
        self.breed_variations = {
            "golden retriever": ["golden", "goldie", "golden retriever"],
            "labrador": ["lab", "labrador", "labrador retriever"],
            "german shepherd": ["schäferhund", "deutscher schäferhund", "dsh"],
            "french bulldog": ["frenchie", "französische bulldogge", "bully"],
            "poodle": ["pudel", "caniche"],
            "dachshund": ["dackel", "teckel", "wiener dog"],
            "beagle": ["beagle"],
            "husky": ["husky", "siberian husky"],
            "border collie": ["border collie", "collie"],
            "mixed breed": ["mischling", "mix", "mischlingshund"]
        }
    
    async def extract_from_input(
        self, 
        user_input: str, 
        context: ConversationContext
    ) -> Dict[str, Any]:
        """
        Extract information from user input using GPT with structured output.
        
        Args:
            user_input: The user's message
            context: Current conversation context with existing information
            
        Returns:
            Dict containing extracted information and confidence scores
        """
        try:
            # Build extraction prompt with context
            prompt = self._build_extraction_prompt(user_input, context)
            
            # Use GPT with JSON response format
            response = await self.gpt.complete(
                prompt=prompt,
                response_format={"type": "json_object"},
                model="gpt-4o-mini",
                max_tokens=200,
                temperature=0.3  # Lower temperature for more consistent extraction
            )
            
            # Parse JSON response
            extracted = json.loads(response)
            
            # Validate and normalize extracted data
            validated = self._validate_extraction(extracted)
            
            # Track token usage
            context.track_llm_call(tokens_used=200)  # Approximate
            
            self.logger.info(f"Extracted information: {validated}")
            return validated
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse GPT response as JSON: {e}")
            return self._empty_extraction()
        except Exception as e:
            self.logger.error(f"Extraction failed: {e}", exc_info=True)
            return self._empty_extraction()
    
    def _build_extraction_prompt(self, user_input: str, context: ConversationContext) -> str:
        """Build the extraction prompt with conversation context"""
        
        info = context.information_status
        
        # Get recent conversation history for context
        recent_turns = []
        if context.message_history:
            for msg in context.message_history[-4:]:  # Last 4 messages
                role = "Balu" if msg["role"] == "assistant" else "User"
                recent_turns.append(f"{role}: {msg['content']}")
        
        conversation_context = "\n".join(recent_turns) if recent_turns else "Start of conversation"
        
        prompt = f"""You are an information extraction system for a dog behavior consultation service.

Extract the following information from the user's message:

Previous context:
- Known dog name: {info.dog_name or 'unknown'}
- Known breed: {info.dog_breed or 'unknown'}  
- Known concern: {info.main_concern or 'none'}
- User name: {info.user_name or 'unknown'}

Recent conversation:
{conversation_context}

Current user input: "{user_input}"

Extract any NEW or UPDATED information:
1. Dog name (the name of the user's dog)
2. Dog breed (specific breed or mix)
3. Behavioral concern/symptom (what the dog is doing that concerns the user)
4. User name (if they introduce themselves)

Rules:
- Only extract information that is explicitly stated
- For breeds, normalize to standard breed names (e.g., "Lab" → "Labrador")
- For concerns, extract the full behavioral description
- Assign confidence 0.0-1.0 based on clarity
- If information was previously known and user confirms/clarifies it, update with higher confidence

Return as JSON:
{{
    "dog_name": "name or null",
    "dog_breed": "breed or null", 
    "main_concern": "behavioral description or null",
    "user_name": "name or null",
    "confidence": {{
        "dog_name": 0.0-1.0,
        "dog_breed": 0.0-1.0,
        "main_concern": 0.0-1.0,
        "user_name": 0.0-1.0
    }},
    "reasoning": "brief explanation of what was extracted and why"
}}"""
        
        return prompt
    
    def _validate_extraction(self, extracted: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize extracted information"""
        
        validated = {
            "dog_name": None,
            "dog_breed": None,
            "main_concern": None,
            "user_name": None,
            "confidence": {
                "dog_name": 0.0,
                "dog_breed": 0.0,
                "main_concern": 0.0,
                "user_name": 0.0
            },
            "reasoning": extracted.get("reasoning", "")
        }
        
        # Validate dog name
        if extracted.get("dog_name") and extracted["dog_name"] != "null":
            name = extracted["dog_name"].strip()
            if len(name) > 1 and len(name) < 30 and name.replace(" ", "").isalpha():
                validated["dog_name"] = name.capitalize()
                validated["confidence"]["dog_name"] = extracted.get("confidence", {}).get("dog_name", 0.8)
        
        # Validate and normalize breed
        if extracted.get("dog_breed") and extracted["dog_breed"] != "null":
            breed = self._normalize_breed(extracted["dog_breed"])
            if breed:
                validated["dog_breed"] = breed
                validated["confidence"]["dog_breed"] = extracted.get("confidence", {}).get("dog_breed", 0.8)
        
        # Validate concern (must be substantive)
        if extracted.get("main_concern") and extracted["main_concern"] != "null":
            concern = extracted["main_concern"].strip()
            if len(concern) > 10:  # Minimum length for a real concern
                validated["main_concern"] = concern
                validated["confidence"]["main_concern"] = extracted.get("confidence", {}).get("main_concern", 0.8)
        
        # Validate user name
        if extracted.get("user_name") and extracted["user_name"] != "null":
            name = extracted["user_name"].strip()
            if len(name) > 1 and len(name) < 50:
                validated["user_name"] = name
                validated["confidence"]["user_name"] = extracted.get("confidence", {}).get("user_name", 0.8)
        
        return validated
    
    def _normalize_breed(self, breed_input: str) -> Optional[str]:
        """Normalize breed names to standard forms"""
        
        breed_lower = breed_input.lower().strip()
        
        # Check against known breed variations
        for standard_breed, variations in self.breed_variations.items():
            if any(var in breed_lower for var in variations):
                return standard_breed.title()
        
        # If not found in variations, check if it's a reasonable breed name
        if len(breed_input) > 2 and breed_input.replace(" ", "").replace("-", "").isalpha():
            return breed_input.title()
        
        return None
    
    def _empty_extraction(self) -> Dict[str, Any]:
        """Return empty extraction result"""
        return {
            "dog_name": None,
            "dog_breed": None,
            "main_concern": None,
            "user_name": None,
            "confidence": {
                "dog_name": 0.0,
                "dog_breed": 0.0,
                "main_concern": 0.0,
                "user_name": 0.0
            },
            "reasoning": "Extraction failed"
        }
    
    async def extract_from_conversation(
        self,
        full_conversation: str
    ) -> Dict[str, Any]:
        """
        Extract information from a full conversation transcript.
        
        Useful for re-processing or summarizing a conversation.
        
        Args:
            full_conversation: Complete conversation text
            
        Returns:
            Extracted information with confidence scores
        """
        prompt = f"""Extract dog consultation information from this conversation:

{full_conversation}

Extract:
- Dog name
- Dog breed
- Main behavioral concern
- User name (if mentioned)

Return as JSON with the same format as before, including confidence scores."""
        
        try:
            response = await self.gpt.complete(
                prompt=prompt,
                response_format={"type": "json_object"},
                model="gpt-4o-mini",
                max_tokens=200,
                temperature=0.3
            )
            
            extracted = json.loads(response)
            return self._validate_extraction(extracted)
            
        except Exception as e:
            self.logger.error(f"Conversation extraction failed: {e}")
            return self._empty_extraction()