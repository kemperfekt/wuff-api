# src/models/unified_state.py

"""
Unified State Models - Single source of truth for conversation state.

This module provides a unified state model that bridges the agentic and static flows,
ensuring seamless data transfer and state management throughout the conversation.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any, List
from datetime import datetime
from enum import Enum

from src.models.agentic_models import ConversationPhase
from src.core.conversation_memory import ConversationMemory


class ConversationMode(str, Enum):
    """Mode of conversation flow"""
    AGENTIC = "agentic"  # Natural conversation for information collection
    STATIC = "static"    # Structured diagnostic flow
    HYBRID = "hybrid"    # Transitioning between modes


@dataclass
class UnifiedConversationState:
    """
    Single source of truth for conversation state across agentic and static flows.
    
    This unifies:
    - Information collection (agentic)
    - Conversation memory
    - Flow state management
    - Handoff preparation
    """
    
    # Identity
    session_id: str
    
    # Collected information with confidence tracking
    user_name: Optional[str] = None
    dog_name: Optional[str] = None
    dog_breed: Optional[str] = None
    main_concern: Optional[str] = None
    
    # Confidence scores for each piece of information
    confidence: Dict[str, float] = field(default_factory=lambda: {
        "user_name": 0.0,
        "dog_name": 0.0,
        "dog_breed": 0.0,
        "main_concern": 0.0
    })
    
    # Conversation memory
    memory: ConversationMemory = field(default_factory=ConversationMemory)
    
    # Flow state
    current_phase: ConversationPhase = ConversationPhase.COLLECTING
    conversation_mode: ConversationMode = ConversationMode.AGENTIC
    perspective_generated: bool = False
    handoff_ready: bool = False
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    llm_calls_count: int = 0
    total_tokens_used: int = 0
    
    # Additional context from perspective generation
    dog_perspective: Optional[str] = None
    instinct_analysis: Optional[Dict[str, Any]] = None
    
    def update_from_extraction(self, extracted_info: Dict[str, Any]) -> None:
        """
        Update state from extraction results.
        
        Args:
            extracted_info: Results from InformationExtractor
        """
        confidence_scores = extracted_info.get("confidence", {})
        
        # Update each field if extracted with sufficient confidence
        fields = ["user_name", "dog_name", "dog_breed", "main_concern"]
        
        for field in fields:
            value = extracted_info.get(field)
            confidence = confidence_scores.get(field, 0.0)
            
            if value and confidence > 0.0:
                # Update if new or better confidence
                current_confidence = self.confidence.get(field, 0.0)
                
                if confidence > current_confidence or getattr(self, field) is None:
                    setattr(self, field, value)
                    self.confidence[field] = confidence
        
        self.last_updated = datetime.now()
    
    def is_ready_for_perspective(self) -> bool:
        """Check if we have enough information for perspective generation"""
        required_fields = ["dog_name", "dog_breed", "main_concern"]
        
        for field in required_fields:
            value = getattr(self, field)
            confidence = self.confidence.get(field, 0.0)
            
            if not value or confidence < 0.7:
                return False
        
        return True
    
    def is_ready_for_handoff(self) -> bool:
        """Check if ready to hand off to static flow"""
        return (
            self.is_ready_for_perspective() and
            self.perspective_generated and
            self.handoff_ready
        )
    
    def get_missing_fields(self) -> List[str]:
        """Get list of missing or low-confidence fields"""
        required = ["dog_name", "dog_breed", "main_concern"]
        missing = []
        
        for field in required:
            value = getattr(self, field)
            confidence = self.confidence.get(field, 0.0)
            
            if not value or confidence < 0.7:
                missing.append(field)
        
        return missing
    
    def get_completion_percentage(self) -> float:
        """Get percentage of required information collected"""
        required = ["dog_name", "dog_breed", "main_concern"]
        collected = 0
        
        for field in required:
            if getattr(self, field) and self.confidence.get(field, 0.0) >= 0.7:
                collected += 1
        
        return (collected / len(required)) * 100
    
    def track_llm_usage(self, tokens: int = 0) -> None:
        """Track LLM usage for cost monitoring"""
        self.llm_calls_count += 1
        self.total_tokens_used += tokens
        self.last_updated = datetime.now()
    
    def get_cost_estimate(self) -> float:
        """Estimate cost in euros based on token usage"""
        # GPT-4o-mini pricing approximation
        # Input: ~$0.00015 per 1K tokens, Output: ~$0.0006 per 1K tokens
        # Using average for estimation
        cost_per_1k_tokens = 0.0004  # Average of input/output
        return (self.total_tokens_used / 1000) * cost_per_1k_tokens
    
    def to_handoff_dict(self) -> Dict[str, Any]:
        """
        Create dictionary for handoff to static flow.
        
        Returns:
            Dict with all necessary information for static flow
        """
        return {
            "session_id": self.session_id,
            "user_name": self.user_name,
            "dog_name": self.dog_name,
            "dog_breed": self.dog_breed,
            "symptom": self.main_concern,
            "dog_perspective": self.dog_perspective,
            "instinct_analysis": self.instinct_analysis,
            "confidence_scores": self.confidence.copy(),
            "conversation_summary": self.memory.get_context_summary(),
            "metadata": {
                "turns": self.memory.turn_counter,
                "duration_seconds": self.memory.get_conversation_duration(),
                "llm_calls": self.llm_calls_count,
                "tokens_used": self.total_tokens_used,
                "cost_estimate_euros": self.get_cost_estimate()
            }
        }
    
    def __str__(self) -> str:
        """String representation for logging"""
        return (
            f"UnifiedState({self.session_id[:8]}... "
            f"phase={self.current_phase.value}, "
            f"completion={self.get_completion_percentage():.0f}%, "
            f"dog={self.dog_name or 'unknown'}, "
            f"breed={self.dog_breed or 'unknown'})"
        )


@dataclass
class HandoffPackage:
    """
    Package of information for handoff between agentic and static flows.
    
    This ensures all necessary data is properly transferred during transitions.
    """
    
    # Core information
    session_id: str
    user_name: Optional[str]
    dog_name: str
    dog_breed: str
    symptom: str
    
    # Enhanced context
    conversation_summary: str
    dog_perspective: Optional[str] = None
    instinct_analysis: Optional[Dict[str, Any]] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Validation
    validated: bool = False
    validation_errors: List[str] = field(default_factory=list)
    
    def validate(self) -> bool:
        """
        Validate the handoff package has all required information.
        
        Returns:
            True if valid, False otherwise
        """
        self.validation_errors.clear()
        
        # Required fields
        if not self.dog_name:
            self.validation_errors.append("Missing dog name")
        if not self.dog_breed:
            self.validation_errors.append("Missing dog breed")
        if not self.symptom or len(self.symptom) < 10:
            self.validation_errors.append("Missing or insufficient symptom description")
        
        self.validated = len(self.validation_errors) == 0
        return self.validated
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "session_id": self.session_id,
            "user_name": self.user_name,
            "dog_name": self.dog_name,
            "dog_breed": self.dog_breed,
            "symptom": self.symptom,
            "conversation_summary": self.conversation_summary,
            "dog_perspective": self.dog_perspective,
            "instinct_analysis": self.instinct_analysis,
            "metadata": self.metadata,
            "validated": self.validated,
            "validation_errors": self.validation_errors
        }