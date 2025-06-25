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
from src.services.weaviate_service import WeaviateService
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
    
    def __init__(self, gpt_service: GPTService, weaviate_service: Optional[WeaviateService] = None):
        self.gpt = gpt_service
        self.weaviate = weaviate_service or WeaviateService()
        self.logger = logging.getLogger(f"{__name__}.InformationExtractor")
        
        # Pure LLM+Weaviate approach - no hardcoded patterns
        self.logger.info("InformationExtractor initialized with LLM-based extraction")
    
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
            validated = await self._validate_extraction(extracted)
            
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

IMPORTANT: Extract only information about the USER'S DOG, not about "Balu" (the assistant).
- "Balu" is the AI assistant's name - ignore any information about Balu
- Only extract information when the user is talking about THEIR OWN dog
- The dog's name should be different from "Balu" unless explicitly stated by the user

Extract any NEW or UPDATED information:
1. Dog name (the name of the user's dog - NOT Balu)
2. Dog breed (specific breed or mix of the user's dog)
3. Behavioral concern/symptom (what the user's dog is doing that concerns them)
4. User name (if the user introduces themselves)

Rules:
- Only extract information that is explicitly stated
- For breeds, extract EXACTLY what the user says, don't translate or interpret (e.g., "Dogge" → "Dogge", not "Great Dane")
- For concerns, extract the full behavioral description
- Assign confidence 0.0-1.0 based on clarity
- If information was previously known and user confirms/clarifies it, update with higher confidence

IMPORTANT: For dog breeds, preserve the original language and terms used by the user. Do not translate German breed names to English.

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
    
    async def _validate_extraction(self, extracted: Dict[str, Any]) -> Dict[str, Any]:
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
        
        # Validate and normalize breed using Weaviate
        if extracted.get("dog_breed") and extracted["dog_breed"] != "null":
            breed = await self._normalize_breed(extracted["dog_breed"])
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
    
    async def _normalize_breed(self, breed_input: str) -> Optional[str]:
        """Normalize breed names using Weaviate breed database and LLM validation"""
        
        if not breed_input or len(breed_input.strip()) < 2:
            return None
            
        try:
            # Search Weaviate for matching breed
            results = await self.weaviate.search(
                collection="Rassen",
                query=breed_input,
                limit=5,  # Get more matches for better evaluation
                properties=["rassename", "alternative_namen"],
                return_metadata=True
            )
            
            # Check for high-confidence direct matches first
            if results:
                best_match = results[0]
                best_similarity = 1 - best_match.get('metadata', {}).get('distance', 1.0)
                best_breed = best_match.get('properties', {}).get('rassename', '')
                
                # Direct match with high similarity
                if best_similarity >= 0.6:
                    self.logger.info(f"High-confidence breed match: '{breed_input}' -> '{best_breed}' (similarity: {best_similarity:.2f})")
                    return best_breed
            
            # Use LLM to validate and select best breed match
            breed_validation_prompt = f"""
You are a dog breed expert working with a German dog breed database.

User input: "{breed_input}"

Database search results (ranked by similarity):
{self._format_breed_matches(results) if results else "No close matches found"}

IMPORTANT RULES:
1. If the user input closely matches a breed name from the database (similarity > 0.4), use the EXACT breed name from the database
2. Common German breed shortcuts:
   - "Dogge" → look for "Deutsche Dogge" in results
   - "Pinscher" → could be "Zwergpinscher", "Deutscher Pinscher", etc. - check results
   - "Dackel" → "Dackel" (Dachshund)
3. Only return "Mischling" if the user explicitly mentions mix/cross/hybrid/kreuzung
4. Prefer ANY database match over general knowledge - even partial matches
5. Use the EXACT breed name from the database, not translations

Return JSON:
{{
    "breed_name": "exact breed name from database, 'Mischling' for explicit mixes, or null if unclear",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation of your choice"
}}"""

            response = await self.gpt.complete(
                prompt=breed_validation_prompt,
                response_format={"type": "json_object"},
                model="gpt-4o-mini",
                max_tokens=150,
                temperature=0.1  # Lower temperature for more consistent results
            )
            
            validation_result = json.loads(response)
            
            # Return validated breed if confidence is reasonable
            if validation_result.get("confidence", 0) >= 0.3:  # Lower threshold for better recognition
                validated_breed = validation_result.get("breed_name")
                if validated_breed and validated_breed != "null":
                    return validated_breed
            
            # Fallback: if we have good Weaviate matches, use the best one
            if results and len(results) > 0:
                best_match = results[0]
                best_similarity = 1 - best_match.get('metadata', {}).get('distance', 1.0)
                
                # For common shortcuts, check specific patterns
                breed_lower = breed_input.lower().strip()
                if breed_lower == "pinscher":
                    # Look for any pinscher breed in results
                    for result in results:
                        breed_name = result.get('properties', {}).get('rassename', '').lower()
                        if "pinscher" in breed_name:
                            self.logger.info(f"Matched '{breed_input}' to '{result['properties']['rassename']}' based on pattern")
                            return result['properties']['rassename']
                
                # Use best match if similarity is good enough
                if best_similarity >= 0.35:  # More forgiving threshold
                    best_breed = best_match.get('properties', {}).get('rassename', '')
                    self.logger.info(f"Fallback to best Weaviate match: '{breed_input}' -> '{best_breed}' (similarity: {best_similarity:.2f})")
                    return best_breed
            
            # Final fallback to cleaned input
            return breed_input.strip().title()
            
        except Exception as e:
            self.logger.warning(f"Breed normalization failed: {e}")
            # Fallback to cleaned input
            return breed_input.strip().title()
    
    def _format_breed_matches(self, results) -> str:
        """Format Weaviate results for LLM evaluation"""
        if not results:
            return "No matches found"
        
        formatted = []
        for i, result in enumerate(results[:3]):
            props = result.get('properties', {})
            distance = result.get('metadata', {}).get('distance', 1.0)
            rassename = props.get('rassename', 'Unknown')
            alt_names = props.get('alternative_namen', '')
            
            match_info = f"{i+1}. {rassename}"
            if alt_names:
                match_info += f" (also: {alt_names})"
            match_info += f" [similarity: {1-distance:.2f}]"
            formatted.append(match_info)
        
        return "\n".join(formatted)
    
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