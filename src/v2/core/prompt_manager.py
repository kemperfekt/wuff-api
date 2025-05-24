# src/v2/core/prompt_manager.py
"""
Centralized prompt management system for WuffChat V2.

This replaces scattered prompts across multiple files with a single,
manageable system that supports:
- Organized prompt storage
- Variable substitution
- Prompt versioning
- A/B testing capability
- Easy fine-tuning
"""
from typing import Dict, Any, Optional, List
from enum import Enum
from pathlib import Path
import json
import logging
from string import Template
from dataclasses import dataclass
from src.v2.core.exceptions import PromptError

logger = logging.getLogger(__name__)


class PromptCategory(str, Enum):
    """Categories for organizing prompts"""
    DOG = "dog"
    COMPANION = "companion" 
    QUERY = "query"
    VALIDATION = "validation"
    ERROR = "error"
    COMMON = "common"


@dataclass
class Prompt:
    """Represents a single prompt template"""
    key: str
    template: str
    category: PromptCategory
    description: str = ""
    variables: List[str] = None
    version: str = "1.0"
    
    def __post_init__(self):
        if self.variables is None:
            # Extract variables from template
            self.variables = self._extract_variables()
    
    def _extract_variables(self) -> List[str]:
        """Extract variable names from template"""
        # Find all {variable} patterns
        import re
        pattern = r'\{(\w+)\}'
        return list(set(re.findall(pattern, self.template)))
    
    def format(self, **kwargs) -> str:
        """
        Format the prompt with provided variables.
        
        Args:
            **kwargs: Variable values
            
        Returns:
            Formatted prompt string
            
        Raises:
            PromptError: If required variables are missing
        """
        # Check for missing variables
        missing = set(self.variables) - set(kwargs.keys())
        if missing:
            raise PromptError(
                prompt_key=self.key,
                message=f"Missing required variables: {missing}",
                details={"missing_variables": list(missing)}
            )
        
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise PromptError(
                prompt_key=self.key,
                message=f"Error formatting prompt: {e}",
                details={"error": str(e)}
            )


class PromptManager:
    """
    Centralized prompt management system.
    
    This manager:
    - Loads prompts from organized files
    - Provides easy access by key
    - Handles variable substitution
    - Supports prompt versioning
    - Enables A/B testing
    """
    
    def __init__(self):
        self.prompts: Dict[str, Prompt] = {}
        self.variants: Dict[str, List[Prompt]] = {}  # For A/B testing
        self._loaded = False
    
    def load_prompts(self, prompts_dir: Optional[Path] = None):
        """
        Load all prompts from the prompts directory.
        
        Args:
            prompts_dir: Path to prompts directory (defaults to v2/prompts)
        """
        if self._loaded:
            logger.debug("Prompts already loaded")
            return
        
        if prompts_dir is None:
            prompts_dir = Path(__file__).parent.parent / "prompts"
        
        logger.info(f"Loading prompts from {prompts_dir}")
        
        # For now, we'll define prompts in code
        # Later, these can be loaded from JSON/YAML files
        self._define_prompts()
        
        self._loaded = True
        logger.info(f"Loaded {len(self.prompts)} prompts")
    
    def _define_prompts(self):
        """Define all prompts (temporary - will be moved to files)"""
        
        # Dog agent prompts
        self.add_prompt(Prompt(
            key="dog.greeting",
            template="Hallo! Schön, dass Du da bist. Ich erkläre Dir Hundeverhalten aus der Hundeperspektive. Bitte beschreibe ein Verhalten oder eine Situation!",
            category=PromptCategory.DOG,
            description="Initial greeting from dog agent"
        ))
        
        self.add_prompt(Prompt(
            key="dog.perspective",
            template="""Ich bin ein Hund und habe dieses Verhalten gezeigt:
'{symptom}'

Hier ist eine Beschreibung aus ähnlichen Situationen:
{match}

Du bist ein Hund. Beschreibe ruhig und klar, wie du dieses Verhalten aus deiner Sicht erlebt hast. 
Sprich nicht über Menschen oder Trainingsmethoden. Nenne keine Instinkte beim Namen. Keine Fantasie. Keine Fachbegriffe.""",
            category=PromptCategory.DOG,
            description="Dog perspective on behavior"
        ))
        
        self.add_prompt(Prompt(
            key="dog.ask_for_more",
            template="Magst Du mehr erfahren, warum ich mich so verhalte?",
            category=PromptCategory.DOG,
            description="Ask if user wants more information"
        ))
        
        self.add_prompt(Prompt(
            key="dog.ask_for_context", 
            template="Gut, dann brauche ich ein bisschen mehr Informationen. Bitte beschreibe, wie es zu der Situation kam, wer dabei war und was sonst noch wichtig sein könnte.",
            category=PromptCategory.DOG,
            description="Ask for additional context"
        ))
        
        self.add_prompt(Prompt(
            key="dog.need_more_info",
            template="Kannst Du das Verhalten bitte etwas ausführlicher beschreiben?",
            category=PromptCategory.DOG,
            description="Request more detailed description"
        ))
        
        self.add_prompt(Prompt(
            key="dog.instinct_diagnosis",
            template="""Ich bin ein Hund und habe folgendes Verhalten gezeigt:
{symptom}

Mein Inneres erinnert sich an vier verschiedene Möglichkeiten, wie ich mich in so einer Situation fühlen könnte:

Jagd: {jagd}
Rudel: {rudel}
Territorial: {territorial}
Sexual: {sexual}

Du bist ich – ein Hund. Erkläre dem Menschen, welcher dieser Impulse dich am besten beschreibt und warum. 
Vermeide Fachbegriffe, bleib bei deinem Gefühl. Keine Instinktnamen nennen. Sprich nicht über Menschen oder Training.""",
            category=PromptCategory.DOG,
            description="Instinct-based diagnosis"
        ))
        
        # Companion agent prompts
        self.add_prompt(Prompt(
            key="companion.feedback_intro",
            template="Ich würde mich freuen, wenn du mir noch ein kurzes Feedback gibst.",
            category=PromptCategory.COMPANION,
            description="Feedback introduction"
        ))
        
        self.add_prompt(Prompt(
            key="companion.feedback_q1",
            template="Hast Du das Gefühl, dass Dir die Beratung bei Deinem Anliegen weitergeholfen hat?",
            category=PromptCategory.COMPANION
        ))
        
        self.add_prompt(Prompt(
            key="companion.feedback_q2",
            template="Wie fandest Du die Sichtweise des Hundes – was hat Dir daran gefallen oder vielleicht irritiert?",
            category=PromptCategory.COMPANION
        ))
        
        self.add_prompt(Prompt(
            key="companion.feedback_q3",
            template="Was denkst Du über die vorgeschlagene Übung – passt sie zu Deiner Situation?",
            category=PromptCategory.COMPANION
        ))
        
        self.add_prompt(Prompt(
            key="companion.feedback_q4",
            template="Auf einer Skala von 0-10: Wie wahrscheinlich ist es, dass Du Wuffchat weiterempfiehlst?",
            category=PromptCategory.COMPANION
        ))
        
        self.add_prompt(Prompt(
            key="companion.feedback_q5",
            template="Optional: Deine E-Mail oder Telefonnummer für eventuelle Rückfragen. Diese wird ausschließlich für Rückfragen zu deinem Feedback verwendet und nach 3 Monaten automatisch gelöscht.",
            category=PromptCategory.COMPANION
        ))
        
        # Query prompts
        self.add_prompt(Prompt(
            key="query.symptom_search",
            template="Beschreibe das folgende Hundeverhalten: {symptom}",
            category=PromptCategory.QUERY
        ))
        
        self.add_prompt(Prompt(
            key="query.instinct_search",
            template="Beschreibe den folgenden Hundeinstinkt: {instinct}",
            category=PromptCategory.QUERY
        ))
        
        self.add_prompt(Prompt(
            key="query.exercise_search",
            template="""Finde eine passende Übung für einen Hund mit aktivem {instinct}-Instinkt, 
der folgendes Verhalten zeigt: {symptom}""",
            category=PromptCategory.QUERY
        ))
        
        # Validation prompts
        self.add_prompt(Prompt(
            key="validation.is_dog_related",
            template="""Antworte mit 'ja' oder 'nein'. 
Hat die folgende Eingabe mit Hundeverhalten oder Hundetraining zu tun?

{text}""",
            category=PromptCategory.VALIDATION
        ))
        
        # Error prompts
        self.add_prompt(Prompt(
            key="error.technical_issue",
            template="Entschuldige, es ist ein technisches Problem aufgetreten. Lass uns neu starten.",
            category=PromptCategory.ERROR
        ))
        
        self.add_prompt(Prompt(
            key="error.not_understood",
            template="Hmm, das habe ich nicht verstanden. Kannst du es anders formulieren?",
            category=PromptCategory.ERROR
        ))
    
    def add_prompt(self, prompt: Prompt):
        """Add a prompt to the manager"""
        if prompt.key in self.prompts:
            logger.warning(f"Overwriting existing prompt: {prompt.key}")
        
        self.prompts[prompt.key] = prompt
        
        # Also add to variants for potential A/B testing
        base_key = prompt.key.rsplit(".", 1)[0]
        if base_key not in self.variants:
            self.variants[base_key] = []
        self.variants[base_key].append(prompt)
    
    def get(self, key: str, **kwargs) -> str:
        """
        Get a formatted prompt by key.
        
        Args:
            key: Prompt key (e.g., "dog.greeting")
            **kwargs: Variables for formatting
            
        Returns:
            Formatted prompt string
            
        Raises:
            PromptError: If prompt not found or formatting fails
        """
        if not self._loaded:
            self.load_prompts()
        
        if key not in self.prompts:
            raise PromptError(
                prompt_key=key,
                message=f"Prompt not found: {key}",
                details={"available_keys": list(self.prompts.keys())}
            )
        
        prompt = self.prompts[key]
        
        # If no variables needed, return template as-is
        if not prompt.variables and not kwargs:
            return prompt.template
        
        return prompt.format(**kwargs)
    
    def get_variant(self, key: str, variant: int = 0, **kwargs) -> str:
        """
        Get a specific variant of a prompt (for A/B testing).
        
        Args:
            key: Base prompt key
            variant: Variant index
            **kwargs: Variables for formatting
            
        Returns:
            Formatted prompt string
        """
        if key not in self.variants or variant >= len(self.variants[key]):
            # Fall back to regular get
            return self.get(key, **kwargs)
        
        prompt = self.variants[key][variant]
        return prompt.format(**kwargs)
    
    def list_prompts(self, category: Optional[PromptCategory] = None) -> List[str]:
        """
        List all available prompt keys.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of prompt keys
        """
        if not self._loaded:
            self.load_prompts()
        
        if category:
            return [
                key for key, prompt in self.prompts.items()
                if prompt.category == category
            ]
        
        return list(self.prompts.keys())
    
    def get_prompt_info(self, key: str) -> Dict[str, Any]:
        """
        Get information about a prompt.
        
        Args:
            key: Prompt key
            
        Returns:
            Dict with prompt information
        """
        if key not in self.prompts:
            raise PromptError(
                prompt_key=key,
                message=f"Prompt not found: {key}"
            )
        
        prompt = self.prompts[key]
        return {
            "key": prompt.key,
            "category": prompt.category.value,
            "description": prompt.description,
            "variables": prompt.variables,
            "version": prompt.version,
            "template_preview": prompt.template[:100] + "..." if len(prompt.template) > 100 else prompt.template
        }


# Global instance for easy access
_prompt_manager = None


def get_prompt_manager() -> PromptManager:
    """Get the global PromptManager instance"""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
        _prompt_manager.load_prompts()
    return _prompt_manager