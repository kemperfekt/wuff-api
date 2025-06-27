# src/core/conversation_memory.py

"""
Conversation Memory - Maintains context and extracted information across conversation turns.

This module provides a memory system that tracks conversation history, extracted facts,
and confidence scores to enable more natural, context-aware conversations.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConversationTurn:
    """Represents a single turn in the conversation"""
    user_input: str
    agent_response: str
    extracted_info: Dict[str, Any]
    timestamp: datetime
    turn_number: int


@dataclass  
class ExtractedFact:
    """Represents an extracted piece of information with metadata"""
    value: Any
    confidence: float
    source_turn: int
    timestamp: datetime
    extraction_method: str = "llm"  # llm, rule, user_provided


class ConversationMemory:
    """
    Maintains conversation context and extracted information.
    
    Features:
    - Tracks all conversation turns
    - Maintains extracted facts with confidence scores
    - Provides context summaries for LLM prompts
    - Supports fact updates and confidence adjustments
    """
    
    def __init__(self):
        self.turns: List[ConversationTurn] = []
        self.extracted_facts: Dict[str, ExtractedFact] = {}
        self.turn_counter: int = 0
        self.start_time: datetime = datetime.now()
        self.logger = logging.getLogger(f"{__name__}.ConversationMemory")
    
    def add_turn(
        self, 
        user_input: str, 
        agent_response: str, 
        extracted_info: Dict[str, Any]
    ) -> None:
        """
        Add a conversation turn with extracted information.
        
        Args:
            user_input: What the user said
            agent_response: What the agent responded
            extracted_info: Information extracted from this turn
        """
        self.turn_counter += 1
        
        turn = ConversationTurn(
            user_input=user_input,
            agent_response=agent_response,
            extracted_info=extracted_info,
            timestamp=datetime.now(),
            turn_number=self.turn_counter
        )
        
        self.turns.append(turn)
        self._update_facts(extracted_info, self.turn_counter)
        
        self.logger.debug(f"Added turn {self.turn_counter}: extracted {len(extracted_info)} facts")
    
    def _update_facts(self, extracted_info: Dict[str, Any], turn_number: int) -> None:
        """Update extracted facts with new information"""
        
        # Expected structure from InformationExtractor
        confidence_scores = extracted_info.get("confidence", {})
        
        fact_keys = ["dog_name", "dog_breed", "main_concern", "user_name"]
        
        for key in fact_keys:
            value = extracted_info.get(key)
            confidence = confidence_scores.get(key, 0.0)
            
            if value and confidence > 0.0:
                # Check if we should update existing fact
                if key in self.extracted_facts:
                    existing_fact = self.extracted_facts[key]
                    
                    # Update if new confidence is higher or significantly different value
                    if confidence > existing_fact.confidence or value != existing_fact.value:
                        self.logger.info(
                            f"Updating {key}: '{existing_fact.value}' -> '{value}' "
                            f"(confidence: {existing_fact.confidence:.2f} -> {confidence:.2f})"
                        )
                        
                        self.extracted_facts[key] = ExtractedFact(
                            value=value,
                            confidence=confidence,
                            source_turn=turn_number,
                            timestamp=datetime.now()
                        )
                else:
                    # New fact
                    self.logger.info(f"New fact {key}: '{value}' (confidence: {confidence:.2f})")
                    
                    self.extracted_facts[key] = ExtractedFact(
                        value=value,
                        confidence=confidence,
                        source_turn=turn_number,
                        timestamp=datetime.now()
                    )
    
    def get_fact(self, key: str) -> Optional[Any]:
        """Get a fact value if it exists with sufficient confidence"""
        fact = self.extracted_facts.get(key)
        if fact and fact.confidence >= 0.7:  # Minimum confidence threshold
            return fact.value
        return None
    
    def get_facts_dict(self) -> Dict[str, Any]:
        """Get all high-confidence facts as a simple dictionary"""
        return {
            key: fact.value
            for key, fact in self.extracted_facts.items()
            if fact.confidence >= 0.7
        }
    
    def get_missing_information(self, required_fields: Optional[List[str]] = None) -> List[str]:
        """
        Get list of missing required information.
        
        Args:
            required_fields: List of required fields (defaults to standard set)
            
        Returns:
            List of field names that are missing or have low confidence
        """
        if required_fields is None:
            required_fields = ["dog_name", "dog_breed", "main_concern"]
        
        missing = []
        for field in required_fields:
            fact = self.extracted_facts.get(field)
            if not fact or fact.confidence < 0.7:
                missing.append(field)
        
        return missing
    
    def get_context_summary(self, include_turns: int = 3) -> str:
        """
        Generate a context summary for LLM prompts.
        
        Args:
            include_turns: Number of recent turns to include
            
        Returns:
            Formatted context summary
        """
        parts = []
        
        # Add extracted facts
        facts = []
        if "dog_name" in self.extracted_facts:
            facts.append(f"Dog: {self.extracted_facts['dog_name'].value}")
        if "dog_breed" in self.extracted_facts:
            facts.append(f"Breed: {self.extracted_facts['dog_breed'].value}")
        if "main_concern" in self.extracted_facts:
            concern = self.extracted_facts['main_concern'].value
            if len(concern) > 50:
                concern = concern[:50] + "..."
            facts.append(f"Concern: {concern}")
        if "user_name" in self.extracted_facts:
            facts.append(f"User: {self.extracted_facts['user_name'].value}")
        
        if facts:
            parts.append("Known facts: " + " | ".join(facts))
        
        # Add recent conversation
        if self.turns and include_turns > 0:
            recent_turns = self.turns[-include_turns:]
            conversation_parts = []
            
            for turn in recent_turns:
                # Truncate long messages
                user_msg = turn.user_input[:100] + "..." if len(turn.user_input) > 100 else turn.user_input
                agent_msg = turn.agent_response[:100] + "..." if len(turn.agent_response) > 100 else turn.agent_response
                
                conversation_parts.append(f"User: {user_msg}")
                conversation_parts.append(f"Balu: {agent_msg}")
            
            parts.append("Recent conversation:\n" + "\n".join(conversation_parts))
        
        # Add conversation stats
        parts.append(f"Conversation length: {self.turn_counter} turns")
        
        return "\n\n".join(parts)
    
    def get_confidence_report(self) -> Dict[str, float]:
        """Get confidence scores for all extracted facts"""
        return {
            key: fact.confidence
            for key, fact in self.extracted_facts.items()
        }
    
    def needs_clarification(self) -> List[Tuple[str, str]]:
        """
        Identify facts that need clarification due to low confidence.
        
        Returns:
            List of (field_name, reason) tuples
        """
        clarifications = []
        
        for key, fact in self.extracted_facts.items():
            if 0.3 < fact.confidence < 0.7:
                if key == "dog_breed":
                    clarifications.append((key, "Unsure about the exact breed"))
                elif key == "dog_name":
                    clarifications.append((key, "Name might be misunderstood"))
                elif key == "main_concern":
                    clarifications.append((key, "Behavior description needs more detail"))
        
        return clarifications
    
    def get_conversation_duration(self) -> float:
        """Get conversation duration in seconds"""
        if not self.turns:
            return 0.0
        
        return (datetime.now() - self.start_time).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize memory to dictionary for storage/logging"""
        return {
            "turn_count": self.turn_counter,
            "duration_seconds": self.get_conversation_duration(),
            "extracted_facts": {
                key: {
                    "value": fact.value,
                    "confidence": fact.confidence,
                    "source_turn": fact.source_turn
                }
                for key, fact in self.extracted_facts.items()
            },
            "missing_information": self.get_missing_information(),
            "confidence_report": self.get_confidence_report()
        }
    
    def has_minimum_information(self) -> bool:
        """Check if we have the minimum required information for proceeding"""
        required = ["dog_name", "dog_breed", "main_concern"]
        
        for field in required:
            fact = self.extracted_facts.get(field)
            if not fact or fact.confidence < 0.7:
                return False
        
        return True
    
    def get_last_user_input(self) -> Optional[str]:
        """Get the most recent user input"""
        if self.turns:
            return self.turns[-1].user_input
        return None
    
    def get_last_agent_response(self) -> Optional[str]:
        """Get the most recent agent response"""
        if self.turns:
            return self.turns[-1].agent_response
        return None