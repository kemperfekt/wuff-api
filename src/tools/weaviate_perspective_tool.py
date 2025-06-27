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
            # Debug logging to catch potential name confusion
            self.logger.info(f"Generating perspective for dog_name='{dog_name}', dog_breed='{dog_breed}', symptom='{symptom}', user_name='{user_name}'")
            
            # Validation to prevent agent name confusion
            if dog_name and dog_name.lower() == 'balu':
                self.logger.warning(f"WARNING: dog_name is 'Balu' (agent name) - this might be incorrect data!")
                self.logger.warning(f"Context: user_name='{user_name}', symptom='{symptom}'")
            
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
        """Retrieve breed-specific insights via Rassen -> gruppen_code -> Instinktveranlagung"""
        try:
            # Step 1: Search for the specific breed in "Rassen" collection
            breed_results = await self.weaviate.search(
                collection="Rassen", 
                query=breed,
                limit=1,
                return_metadata=True
            )
            
            if not breed_results or len(breed_results) == 0:
                self.logger.info(f"No breed found in Rassen collection for: {breed}")
                return None
            
            breed_result = breed_results[0]
            distance = breed_result.get('metadata', {}).get('distance', 1.0)
            if distance >= 0.8:  # Poor match
                self.logger.info(f"Breed match too weak (distance: {distance}) for: {breed}")
                return None
            
            # Step 2: Get the gruppen_code from the breed result properties
            # Weaviate returns data in the 'properties' field
            breed_properties = breed_result.get('properties', breed_result)
            self.logger.info(f"Breed result structure: {list(breed_result.keys())}")
            self.logger.info(f"Breed properties: {list(breed_properties.keys()) if isinstance(breed_properties, dict) else 'Not a dict'}")
            
            gruppen_code = breed_properties.get('gruppen_code', '')
            if not gruppen_code:
                self.logger.info(f"No gruppen_code found for breed: {breed}. Available properties: {list(breed_properties.keys()) if isinstance(breed_properties, dict) else breed_properties}")
                return None
            
            self.logger.info(f"Found breed {breed} with gruppen_code: {gruppen_code}")
            
            # Step 3: Find the exact gruppen_code match in "Instinktveranlagung" collection
            try:
                # First try semantic search with the gruppen_code
                instinct_results = await self.weaviate.search(
                    collection="Instinktveranlagung", 
                    query=str(gruppen_code),  # Convert to string for search
                    limit=10,  # Get more results to find exact match
                    return_metadata=True
                )
                
                # Look for exact gruppen_code match in results
                exact_match = None
                for result in instinct_results:
                    # Access properties correctly
                    result_properties = result.get('properties', result)
                    result_code = result_properties.get('gruppen_code', '')
                    self.logger.info(f"Checking result with gruppen_code: {result_code} against target: {gruppen_code}")
                    if str(result_code) == str(gruppen_code):
                        exact_match = result_properties  # Return the properties, not the wrapper
                        self.logger.info(f"Found exact match for gruppen_code: {gruppen_code}")
                        break
                
                if exact_match:
                    return exact_match
                else:
                    self.logger.info(f"No exact match found for gruppen_code: {gruppen_code}")
                    
                    # Fallback: Try searching with a more specific query format
                    # Some Weaviate setups might need different query approaches
                    fallback_results = await self.weaviate.search(
                        collection="Instinktveranlagung",
                        query=f"gruppen_code:{gruppen_code}",
                        limit=1,
                        return_metadata=True
                    )
                    
                    if fallback_results and len(fallback_results) > 0:
                        result = fallback_results[0]
                        result_properties = result.get('properties', result)
                        found_code = result_properties.get('gruppen_code', '')
                        if str(found_code) == str(gruppen_code):
                            self.logger.info(f"Found match via fallback search for gruppen_code: {gruppen_code}")
                            return result_properties
                    
                    self.logger.info(f"No Instinktveranlagung found for gruppen_code: {gruppen_code}")
                    return None
                    
            except Exception as search_error:
                self.logger.warning(f"Error searching Instinktveranlagung for gruppen_code {gruppen_code}: {search_error}")
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
        """Generate Balu's perspective with optional breed comment"""
        
        # 1. Generate breed comment if we have breed context and it's not "Mischling"
        breed_comment = ""
        self.logger.info(f"Breed context check: breed='{dog_breed}', has_context={bool(breed_context)}")
        if breed_context:
            self.logger.info(f"Breed context keys: {list(breed_context.keys())}")
        
        if breed_context and dog_breed.lower() not in ["mischling", "mix", "mischlingsrüde", "mischlingshündin"]:
            breed_comment = await self._generate_breed_comment(dog_breed, breed_context)
            self.logger.info(f"Generated breed comment: '{breed_comment}'")
        
        # 2. Build the main perspective prompt
        prompt = self._build_perspective_prompt(
            symptom=symptom,
            dog_name=dog_name,
            dog_breed=dog_breed,
            user_name=user_name,
            symptom_data=symptom_data,
            breed_context=breed_context
        )
        
        try:
            # 3. Generate the main perspective
            response = await self.gpt.complete(
                prompt=prompt,
                model="gpt-4o-mini",
                max_tokens=300,
                temperature=0.7
            )
            
            perspective = response.strip()
            
            # 4. Combine breed comment with perspective
            if breed_comment:
                return f"{breed_comment}\n\n{perspective}"
            else:
                return perspective
            
        except Exception as e:
            raise ToolError(
                tool_name=self.name,
                message=f"GPT generation failed: {str(e)}",
                details={"prompt_length": len(prompt)}
            )
    
    async def _generate_breed_comment(self, dog_breed: str, breed_context: Dict[str, Any]) -> str:
        """Extract and summarize breed comment from Weaviate Hundeperspektive field"""
        
        # Get the Hundeperspektive field from Instinktveranlagung data
        hundeperspektive = breed_context.get('hundeperspektive', '')
        
        self.logger.info(f"Hundeperspektive for {dog_breed}: '{hundeperspektive[:100]}...' (available fields: {list(breed_context.keys())})")
        
        if not hundeperspektive:
            # No breed perspective available
            self.logger.warning(f"No Hundeperspektive found for breed: {dog_breed}")
            return ""
        
        # Summarize to 1-2 sentences that describe the nature of this breed group
        summary_prompt = f"""Du bist Balu. Fasse die Hundeperspektive für die Rasse {dog_breed} in 1-2 Sätzen zusammen.

Original Hundeperspektive: {hundeperspektive}

Deine Aufgabe: Erstelle eine kurze Zusammenfassung, die die Natur und Eigenschaften dieser Rasse beschreibt.

Stil:
- Beginne mit "*aufmerksam*" oder "*interessiert*"
- 1-2 Sätze über die wichtigsten Eigenschaften der Rasse
- Positiv und informativ formuliert
- Verwende "diese Rasse" oder "{dog_breed}"

Beispiel: "*interessiert* Diese Rasse ist bekannt für ihre ausgeprägte Wachsamkeit und ihren starken Schutzinstinkt."

Deine Zusammenfassung:"""

        try:
            summary = await self.gpt.complete(
                prompt=summary_prompt,
                model="gpt-4o-mini",
                max_tokens=80,  # Keep it short - 1-2 sentences
                temperature=0.7
            )
            
            return summary.strip()
            
        except Exception as e:
            # Fallback: Use first 2 sentences of original if GPT fails
            self.logger.warning(f"Breed comment summarization failed: {e}")
            sentences = hundeperspektive.split('.')
            if len(sentences) >= 2:
                fallback = '. '.join(sentences[:2]).strip() + '.'
                return f"*aufmerksam* {fallback}"
            else:
                return f"*aufmerksam* {hundeperspektive.strip()}"
    
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
- Maximal EINE emotionale Beschreibung: *nachdenklich*, *verständnisvoll*, oder *aufmerksam*
- Erkläre warmherzig und ohne Vorwürfe
- Zeige, dass {dog_name}s Verhalten aus Hundesicht völlig logisch ist
- Verwende "wir Hunde" um Verbindung zu schaffen
- Bleibe bei maximal 2-3 Sätzen
- Sprich ZU dem Hundebesitzer ÜBER {dog_name} (nicht zu {dog_name} direkt)
- Verwende "du" für den Hundebesitzer und erwähne {dog_name} in der dritten Person

Beispiel-Ton: "*verständnisvoll* Ach, das kenne ich... Für uns Hunde ist das..." oder "Das kann ich gut verstehen... Wenn {dog_name} das macht..."

Deine Perspektive zu {dog_name}s Verhalten:"""

        return prompt
    
    def get_description(self) -> str:
        """Get tool description for LLM planning"""
        return """WeaviatePerspectiveTool: Generates authentic dog perspective on behavioral concerns. 
        Requires: symptom, dog_name, dog_breed. Optional: user_name.
        Uses Weaviate for context and GPT for perspective generation."""