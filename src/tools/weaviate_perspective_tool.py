# src/tools/weaviate_perspective_tool.py

from typing import Optional, Dict, Any
import logging
from src.tools.base_tool import BaseTool, ToolError
from src.services.weaviate_service import WeaviateService
from src.services.gpt_service import GPTService

logger = logging.getLogger(__name__)


class WeaviatePerspectiveTool(BaseTool):
    """
    Tool for generating authentic dog perspective based on collected information.
    
    Uses Weaviate to retrieve relevant symptom and breed data, then generates
    Balu's perspective using GPT with that context.
    """
    
    def __init__(self, weaviate_service: WeaviateService, gpt_service: GPTService):
        super().__init__("weaviate_perspective")
        self.weaviate = weaviate_service
        self.gpt = gpt_service
    
    async def _execute(self, 
                      symptom: str, 
                      dog_name: str, 
                      dog_breed: str,
                      user_name: Optional[str] = None) -> str:
        """
        Generate Balu's perspective on the collected symptom and context.
        
        Args:
            symptom: The behavioral concern described by the user
            dog_name: Name of the user's dog
            dog_breed: Breed of the user's dog
            user_name: Optional name of the user
        
        Returns:
            Balu's perspective as a string
        """
        try:
            # 1. Get symptom information from Weaviate
            symptom_data = await self._get_symptom_context(symptom)
            
            # 2. Get breed-specific insights if available
            breed_context = await self._get_breed_context(dog_breed)
            
            # 3. Generate Balu's perspective using GPT
            perspective = await self._generate_perspective(
                symptom=symptom,
                dog_name=dog_name,
                dog_breed=dog_breed,
                user_name=user_name,
                symptom_data=symptom_data,
                breed_context=breed_context
            )
            
            return perspective
            
        except Exception as e:
            raise ToolError(
                tool_name=self.name,
                message=f"Failed to generate dog perspective: {str(e)}",
                details={
                    "symptom": symptom,
                    "dog_name": dog_name,
                    "dog_breed": dog_breed
                }
            )
    
    async def _get_symptom_context(self, symptom: str) -> Optional[Dict[str, Any]]:
        """Retrieve symptom information from Weaviate"""
        try:
            # Search in Symptome collection
            results = await self.weaviate.search(
                collection="Symptome",
                query=symptom,
                limit=1,
                return_metadata=True  # Include distance for quality assessment
            )
            
            if results and len(results) > 0:
                # Check if the match is good enough (distance < 0.8 means good match)
                result = results[0]
                distance = result.get('metadata', {}).get('distance', 1.0)
                if distance < 0.8:  # Good match threshold
                    return result
                else:
                    self.logger.info(f"Symptom match too weak (distance: {distance}) for: {symptom}")
            
            self.logger.info(f"No good symptom data found for: {symptom}")
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to retrieve symptom context: {e}")
            return None
    
    async def _get_breed_context(self, breed: str) -> Optional[Dict[str, Any]]:
        """Retrieve breed-specific insights from Weaviate"""
        try:
            # Search in Rassen collection
            results = await self.weaviate.search(
                collection="Rassen", 
                query=breed,
                limit=1,
                return_metadata=True  # Include distance for quality assessment
            )
            
            if results and len(results) > 0:
                # Check if the match is good enough (distance < 0.8 means good match)
                result = results[0]
                distance = result.get('metadata', {}).get('distance', 1.0)
                if distance < 0.8:  # Good match threshold
                    return result
                else:
                    self.logger.info(f"Breed match too weak (distance: {distance}) for: {breed}")
                
            self.logger.info(f"No good breed data found for: {breed}")
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to retrieve breed context: {e}")
            return None
    
    async def _generate_perspective(self,
                                  symptom: str,
                                  dog_name: str, 
                                  dog_breed: str,
                                  user_name: Optional[str],
                                  symptom_data: Optional[Dict[str, Any]],
                                  breed_context: Optional[Dict[str, Any]]) -> str:
        """Generate Balu's perspective using GPT"""
        
        # Build the prompt with available context
        prompt = self._build_perspective_prompt(
            symptom=symptom,
            dog_name=dog_name,
            dog_breed=dog_breed,
            user_name=user_name,
            symptom_data=symptom_data,
            breed_context=breed_context
        )
        
        try:
            # Use GPT-4o-mini for cost efficiency
            response = await self.gpt.complete(
                prompt=prompt,
                model="gpt-4o-mini",
                max_tokens=300,
                temperature=0.7
            )
            
            return response.strip()
            
        except Exception as e:
            raise ToolError(
                tool_name=self.name,
                message=f"GPT generation failed: {str(e)}",
                details={"prompt_length": len(prompt)}
            )
    
    def _build_perspective_prompt(self,
                                symptom: str,
                                dog_name: str,
                                dog_breed: str, 
                                user_name: Optional[str],
                                symptom_data: Optional[Dict[str, Any]],
                                breed_context: Optional[Dict[str, Any]]) -> str:
        """Build the prompt for generating Balu's perspective"""
        
        # Start with Balu's identity
        prompt = f"""Du bist Balu, ein ruhiger und weiser Labrador mit einer besonderen Gabe: Du verstehst sowohl Hunde als auch Menschen.

Du sprichst {user_name + ' ' if user_name else ''}über {dog_name}, einen {dog_breed}, und das Verhalten: {symptom}

Deine Aufgabe: Erkläre aus authentischer Hundesicht, warum {dog_name} dieses Verhalten zeigt.

"""

        # Add symptom context if available
        if symptom_data:
            diagnosis = symptom_data.get('diagnosis', '')
            dog_perspective = symptom_data.get('dog_perspective', '')
            
            if diagnosis:
                prompt += f"Fachliche Einordnung: {diagnosis}\n"
            if dog_perspective:
                prompt += f"Hunde-Sicht: {dog_perspective}\n"
            
            prompt += "\n"

        # Add breed context if available  
        if breed_context:
            instinkte = breed_context.get('instinkte', {})
            if instinkte:
                instinct_text = ", ".join([f"{k}: {v}" for k, v in instinkte.items() if v])
                prompt += f"Rassen-Instinkte von {dog_breed}: {instinct_text}\n\n"

        # Add Balu's perspective instructions
        prompt += f"""Antworte als Balu:
- Verwende Präsenz-Marker wie *nachdenklich* oder *verständnisvoll-blick*
- Erkläre warmherzig und ohne Vorwürfe
- Zeige, dass {dog_name}s Verhalten aus Hundesicht völlig logisch ist
- Verwende "wir Hunde" um Verbindung zu schaffen
- Bleibe bei maximal 2-3 Sätzen
- Nutze {dog_name}s Namen persönlich

Beispiel-Ton: "*verständnisvoll* Ach, das kenne ich... Für uns Hunde ist das..."

Deine Perspektive zu {dog_name}s Verhalten:"""

        return prompt
    
    def get_description(self) -> str:
        """Get tool description for LLM planning"""
        return """WeaviatePerspectiveTool: Generates authentic dog perspective on behavioral concerns. 
        Requires: symptom, dog_name, dog_breed. Optional: user_name.
        Uses Weaviate for context and GPT for perspective generation."""