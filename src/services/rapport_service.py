# src/services/rapport_service.py
"""
MVP RapportEnhancer - Simple rapport building enhancement service.

This service provides minimal but effective rapport building enhancements
that can be applied to any agent response. Starts simple and extensible.
"""

from typing import Optional, Dict, List
# Simple standalone service - no inheritance needed for MVP
class BaseService:
    def __init__(self):
        pass
import random
import logging

logger = logging.getLogger(__name__)


class RapportService(BaseService):
    """
    Legacy RapportService for compatibility - provides dog info extraction.
    Contains the new RapportEnhancer functionality as well.
    """
    
    def __init__(self):
        super().__init__()
        # RapportEnhancer will be initialized after class definition
    
    async def extract_dog_info(self, user_input: str, session) -> dict:
        """Extract dog information from user input."""
        import re
        
        dog_info = {}
        
        # Simple regex patterns for dog name extraction
        name_patterns = [
            r"mein hund ([\w\-]+)",
            r"heißt ([\w\-]+)",
            r"([\w\-]+) macht",
            r"([\w\-]+) bellt",
            r"([\w\-]+) springt"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, user_input.lower())
            if match:
                potential_name = match.group(1).capitalize()
                if len(potential_name) > 2 and potential_name not in ["Mein", "Der", "Die", "Das"]:
                    dog_info["dog_name"] = potential_name
                    break
        
        return dog_info
    
    def update_session_with_dog_info(self, session, dog_info: dict):
        """Update session with extracted dog information."""
        if "dog_name" in dog_info:
            session.user_dog_name = dog_info["dog_name"]
            session.dog_info_collected = True


class RapportEnhancer(BaseService):
    """
    Minimal Viable Rapport enhancement service.
    
    Provides simple but effective presence markers and emotional awareness
    without complex state management or heavy processing.
    """
    
    def __init__(self):
        """Initialize RapportEnhancer with presence marker library."""
        super().__init__()
        
        # Presence marker library organized by emotional context
        self.presence_markers = {
            "calm": [
                "*ruhig-atme*", "*aufmerksam-schau*", "*beobachte-gelassen*",
                "*gemütlich-hinleg*", "*entspannt-sitz*", "*sanft-blick*"
            ],
            "concerned": [
                "*aufmerksam-werd*", "*näher-rück*", "*verstehend-nick*",
                "*mitfühlend-stups*", "*tröstend-näher*", "*sorgsam-blick*"
            ],
            "engaged": [
                "*interessiert*", "*neugierig-schnüffel*", "*aufhorche*",
                "*lebhaft-wedelnd*", "*gespannt-warten*", "*wissbegierig*"
            ],
            "thoughtful": [
                "*nachdenklich*", "*kopf-neig*", "*sinnierend*",
                "*überlege-kurz*", "*bedächtig*", "*weise-blick*"
            ]
        }
        
        # Simple emotion keywords for detection
        self.emotion_keywords = {
            "stressed": ["verzweifelt", "hilfe!", "total", "ständig", "immer", "katastrophe"],
            "frustrated": ["nervt", "ärgert", "probleme", "schwierig", "nicht"],
            "positive": ["toll", "super", "gut", "schön", "freut", "gefällt"],
            "questioning": ["warum", "wieso", "wie", "verstehe nicht", "weiß nicht", "macht mein hund"]
        }
    
    def enhance_response(self, 
                        response: str, 
                        user_input: Optional[str] = None,
                        emotional_context: Optional[str] = None) -> str:
        """
        Enhance a response with rapport-building elements.
        
        Args:
            response: Original agent response
            user_input: User's input (for emotion detection)
            emotional_context: Pre-detected emotional context
            
        Returns:
            Enhanced response with presence markers
        """
        try:
            # Handle None response
            if response is None:
                return None
                
            # Skip if response is empty or too short
            if not response or len(response.strip()) < 10:
                return response
            
            # Detect emotional context if not provided
            if not emotional_context and user_input:
                emotional_context = self._detect_simple_emotion(user_input)
            
            # Default to calm if no emotion detected
            if not emotional_context:
                emotional_context = "calm"
            
            # Add presence marker based on emotional context
            enhanced = self._add_presence_marker(response, emotional_context)
            
            logger.debug(f"[RapportEnhancer] Enhanced response with {emotional_context} marker")
            return enhanced
            
        except Exception as e:
            logger.error(f"[RapportEnhancer] Enhancement failed: {e}")
            # Return original response if enhancement fails
            return response
    
    def _detect_simple_emotion(self, user_input: str) -> str:
        """
        Simple keyword-based emotion detection.
        
        Args:
            user_input: User's text input
            
        Returns:
            Detected emotion category
        """
        if not user_input:
            return "calm"
        
        user_lower = user_input.lower()
        
        # Check questioning first (most specific patterns)
        for keyword in self.emotion_keywords["questioning"]:
            if keyword in user_lower:
                return "thoughtful"
                
        # Then check other emotions
        for emotion, keywords in self.emotion_keywords.items():
            if emotion == "questioning":
                continue  # Already checked
            if any(keyword in user_lower for keyword in keywords):
                # Map detected emotions to presence marker categories
                if emotion == "stressed":
                    return "concerned"
                elif emotion == "frustrated":
                    return "concerned"
                elif emotion == "positive":
                    return "engaged"
        
        # Default to calm for neutral input
        return "calm"
    
    def _add_presence_marker(self, response: str, emotional_context: str) -> str:
        """
        Add appropriate presence marker to response.
        
        Args:
            response: Original response text
            emotional_context: Emotional context for marker selection
            
        Returns:
            Response with presence marker added
        """
        # Get markers for the emotional context
        markers = self.presence_markers.get(emotional_context, self.presence_markers["calm"])
        
        # Select random marker
        marker = random.choice(markers)
        
        # Add marker at the beginning with a space
        return f"{marker} {response}"
    
    def get_available_emotions(self) -> List[str]:
        """
        Get list of available emotional contexts.
        
        Returns:
            List of emotion categories supported
        """
        return list(self.presence_markers.keys())
    
    def validate_emotion(self, emotion: str) -> bool:
        """
        Validate if an emotion category is supported.
        
        Args:
            emotion: Emotion category to validate
            
        Returns:
            True if emotion is supported
        """
        return emotion in self.presence_markers
    
    async def health_check(self) -> Dict[str, str]:
        """
        Service health check.
        
        Returns:
            Health status information
        """
        try:
            # Test basic functionality
            test_response = self.enhance_response("Test response", "Hallo")
            
            return {
                "status": "healthy",
                "service": "RapportEnhancer",
                "markers_loaded": str(len(self.presence_markers)),
                "test_enhancement": "✅" if "*" in test_response else "❌"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "service": "RapportEnhancer",
                "error": str(e)
            }


# Global instances for easy import
rapport_enhancer = RapportEnhancer()

# Initialize RapportService after RapportEnhancer exists
class _RapportServiceWithEnhancer(RapportService):
    def __init__(self):
        super().__init__()
        self.enhancer = rapport_enhancer

rapport_service = _RapportServiceWithEnhancer()  # For backward compatibility