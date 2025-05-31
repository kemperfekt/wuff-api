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
from src.core.exceptions import PromptError

logger = logging.getLogger(__name__)


class PromptCategory(str, Enum):
    """Categories for organizing prompts"""
    DOG = "dog"
    COMPANION = "companion" 
    QUERY = "query"
    VALIDATION = "validation"
    ERROR = "error"
    COMMON = "common"

class PromptType(str, Enum):
    """Enum for all prompt types - maps to prompt keys"""
    
    # Dog Agent Prompts
    DOG_GREETING = "dog.greeting"
    DOG_GREETING_FOLLOWUP = "dog.greeting.followup"
    DOG_PERSPECTIVE = "generation.dog_perspective"
    DOG_INSTINCT_DIAGNOSIS = "generation.instinct_diagnosis"
    DOG_ASK_FOR_MORE = "dog.ask.for.more"
    DOG_DIAGNOSIS_INTRO = "dog.diagnosis.intro"
    DOG_DIAGNOSIS = "dog.diagnosis"
    DOG_CONFIRMATION_QUESTION = "dog.confirmation.question"
    DOG_CONTEXT_QUESTION = "dog.context.question"
    DOG_EXERCISE_QUESTION = "dog.exercise.question"
    #DOG_RESTART_QUESTION = "dog.restart.question"
    DOG_CONTINUE_OR_RESTART = "dog.continue.or.restart"
    DOG_NO_MATCH_ERROR = "dog.no.match.error"
    DOG_SILLY_INPUT_REJECTION = "dog.silly.input.rejection"
    DOG_INVALID_INPUT_ERROR = "dog.invalid.input.error"
    DOG_TECHNICAL_ERROR = "dog.technical.error"
    DOG_DESCRIBE_MORE = "dog.need.more.detail"
    DOG_BE_SPECIFIC = "dog.be.specific"
    DOG_ANOTHER_BEHAVIOR_QUESTION = "dog.another.behavior.question"
    DOG_FALLBACK_EXERCISE = "dog.fallback.exercise"
    
    # Companion Agent Prompts
    COMPANION_FEEDBACK_INTRO = "companion.feedback.intro"
    COMPANION_FEEDBACK_Q1 = "companion.feedback.q1"
    COMPANION_FEEDBACK_Q2 = "companion.feedback.q2"
    COMPANION_FEEDBACK_Q3 = "companion.feedback.q3"
    COMPANION_FEEDBACK_Q4 = "companion.feedback.q4"
    COMPANION_FEEDBACK_Q5 = "companion.feedback.q5"
    COMPANION_FEEDBACK_ACK = "companion.feedback.ack"
    COMPANION_FEEDBACK_COMPLETE = "companion.feedback.complete"
    COMPANION_FEEDBACK_COMPLETE_NOSAVE = "companion.feedback.complete.nosave"
    COMPANION_PROCEED_CONFIRMATION = "companion.proceed.confirmation"
    COMPANION_SKIP_CONFIRMATION = "companion.skip.confirmation"
    COMPANION_INVALID_FEEDBACK_ERROR = "companion.invalid.feedback.error"
    COMPANION_SAVE_ERROR = "companion.save.error"
    COMPANION_GENERAL_ERROR = "companion.general.error"
    
    # Validation error prompts
    INPUT_TOO_SHORT = "validation.input.too.short"
    NO_BEHAVIOR_MATCH = "validation.no.behavior.match"
    INVALID_YES_NO = "validation.invalid.yes.no"
    
    # Other prompts
    VALIDATION = "validation.input"
    COMBINED_INSTINCT = "query.combined_instinct"
    INSTINCT_ANALYSIS = "query.instinct_analysis"

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
                prompt_type=self.key,
                message=f"Missing required variables: {missing}",
                details={"missing_variables": list(missing)}
            )
        
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise PromptError(
                prompt_type=self.key,
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
    
    def get_prompt(self, prompt_type, **kwargs) -> str:
        """
        Compatibility method for PromptType enum usage.
        
        Args:
            prompt_type: PromptType enum value or string key
            **kwargs: Variables for formatting
            
        Returns:
            Formatted prompt string
        """
        # Convert PromptType enum to string key
        key = prompt_type.value if hasattr(prompt_type, 'value') else str(prompt_type)
        return self.get(key, **kwargs)
        
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
        """Load all prompts from the prompt files"""
        # Import all prompt modules
        from src.prompts import (
            dog_prompts,
            generation_prompts,
            query_prompts,
            companion_prompts,
            validation_prompts,
            common_prompts
        )
        
        # Helper to register prompts from module attributes
        def register_from_module(module, category: PromptCategory, key_prefix: str):
            """Register all string constants from a module as prompts"""
            for name in dir(module):
                value = getattr(module, name)
                # Only process string constants (uppercase names)
                if isinstance(value, str) and name.isupper() and not name.startswith('_'):
                    # Convert CONSTANT_NAME to constant.name format
                    key_parts = name.lower().split('_')
                    key = f"{key_prefix}.{'.'.join(key_parts)}"
                    
                    self.add_prompt(Prompt(
                        key=key,
                        template=value,
                        category=category,
                        description=f"Auto-imported from {module.__name__}.{name}"
                    ))
        
        # Register all prompts from each module
        register_from_module(dog_prompts, PromptCategory.DOG, "dog")
        register_from_module(companion_prompts, PromptCategory.COMPANION, "companion")
        register_from_module(validation_prompts, PromptCategory.VALIDATION, "validation")
        register_from_module(common_prompts, PromptCategory.COMMON, "common")
        
        # Special handling for templates that need specific keys
        
        # Generation prompts (these keep their template suffix)
        self.add_prompt(Prompt(
            key="generation.dog_perspective",
            template=generation_prompts.DOG_PERSPECTIVE_TEMPLATE,
            category=PromptCategory.DOG,
            variables=["symptom", "match"]
        ))
        
        self.add_prompt(Prompt(
            key="generation.instinct_diagnosis",
            template=generation_prompts.INSTINCT_DIAGNOSIS_TEMPLATE,
            category=PromptCategory.DOG,
            variables=["symptom", "context", "jagd", "rudel", "territorial", "sexual"]
        ))
        
        self.add_prompt(Prompt(
            key="generation.exercise",
            template=generation_prompts.EXERCISE_TEMPLATE,
            category=PromptCategory.DOG,
            variables=["symptom", "match"]
        ))
        
        # Query prompts
        self.add_prompt(Prompt(
            key="query.symptom",
            template=query_prompts.SYMPTOM_QUERY_TEMPLATE,
            category=PromptCategory.QUERY,
            variables=["symptom"]
        ))
        
        self.add_prompt(Prompt(
            key="query.instinct",
            template=query_prompts.INSTINCT_QUERY_TEMPLATE,
            category=PromptCategory.QUERY,
            variables=["instinct"]
        ))
        
        self.add_prompt(Prompt(
            key="query.exercise",
            template=query_prompts.EXERCISE_QUERY_TEMPLATE,
            category=PromptCategory.QUERY,
            variables=["instinct", "symptom"]
        ))
        
        self.add_prompt(Prompt(
            key="query.dog_perspective",
            template=query_prompts.DOG_PERSPECTIVE_QUERY_TEMPLATE,
            category=PromptCategory.QUERY,
            variables=["symptom"]
        ))
        
        self.add_prompt(Prompt(
            key="query.instinct_analysis",
            template=query_prompts.INSTINCT_ANALYSIS_QUERY_TEMPLATE,
            category=PromptCategory.QUERY,
            variables=["symptom", "context"]
        ))
        
        self.add_prompt(Prompt(
            key="query.combined_instinct",
            template=query_prompts.COMBINED_INSTINCT_QUERY_TEMPLATE,
            category=PromptCategory.QUERY,
            variables=["symptom", "context"]
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
                prompt_type=key,
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
                prompt_type=self.key,
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