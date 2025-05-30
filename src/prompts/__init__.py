# src/v2/prompts/__init__.py
"""V2 Prompts package - centralized prompt management"""

# Import all prompt modules for PromptManager
from . import dog_prompts
from . import companion_prompts
from . import generation_prompts
from . import query_prompts
from . import validation_prompts
from . import common_prompts

__all__ = [
    'dog_prompts',
    'companion_prompts', 
    'generation_prompts',
    'query_prompts',
    'validation_prompts',
    'common_prompts'
]