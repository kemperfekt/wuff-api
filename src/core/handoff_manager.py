# src/core/handoff_manager.py

"""
Handoff Manager - Manages seamless transitions between conversation flows.

This module handles the transfer of collected information from the agentic
conversation flow to the static diagnostic flow, ensuring no data is lost.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.models.unified_state import UnifiedConversationState, HandoffPackage
from src.models.session_state import SessionState
from src.models.flow_models import FlowStep
from src.core.exceptions import V2FlowError

logger = logging.getLogger(__name__)


class HandoffError(Exception):
    """Raised when handoff cannot be completed"""
    pass


class HandoffManager:
    """
    Manages handoff between agentic and static conversation flows.
    
    Responsibilities:
    - Validate collected information
    - Create handoff packages
    - Transfer data to static flow session
    - Handle error cases gracefully
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.HandoffManager")
    
    async def prepare_handoff(
        self, 
        state: UnifiedConversationState
    ) -> HandoffPackage:
        """
        Prepare handoff package from unified state.
        
        Args:
            state: Current unified conversation state
            
        Returns:
            HandoffPackage ready for transfer
            
        Raises:
            HandoffError: If state is not ready for handoff
        """
        # Validate readiness
        if not state.is_ready_for_perspective():
            missing = state.get_missing_fields()
            raise HandoffError(
                f"Cannot handoff: missing required fields: {', '.join(missing)}"
            )
        
        # Create handoff package
        package = HandoffPackage(
            session_id=state.session_id,
            user_name=state.user_name,
            dog_name=state.dog_name,
            dog_breed=state.dog_breed,
            symptom=state.main_concern,
            conversation_summary=state.memory.get_context_summary(),
            dog_perspective=state.dog_perspective,
            instinct_analysis=state.instinct_analysis,
            metadata={
                "turns": state.memory.turn_counter,
                "confidence_scores": state.confidence.copy(),
                "perspective_generated": state.perspective_generated,
                "duration_seconds": state.memory.get_conversation_duration(),
                "llm_calls": state.llm_calls_count,
                "tokens_used": state.total_tokens_used,
                "cost_estimate_euros": state.get_cost_estimate(),
                "handoff_timestamp": datetime.now().isoformat()
            }
        )
        
        # Validate package
        if not package.validate():
            raise HandoffError(
                f"Handoff package validation failed: {', '.join(package.validation_errors)}"
            )
        
        self.logger.info(
            f"Prepared handoff package for session {state.session_id[:8]}... "
            f"(dog: {package.dog_name}, breed: {package.dog_breed})"
        )
        
        return package
    
    def execute_handoff(
        self,
        package: HandoffPackage,
        session: SessionState
    ) -> None:
        """
        Transfer data from handoff package to static flow session.
        
        Args:
            package: Validated handoff package
            session: Target session state for static flow
        """
        if not package.validated:
            package.validate()
            if not package.validated:
                raise HandoffError("Cannot execute handoff with invalid package")
        
        # Transfer core information
        session.user_name = package.user_name
        session.user_dog_name = package.dog_name
        session.user_dog_breed = package.dog_breed
        session.active_symptom = package.symptom
        
        # Mark that dog info has been collected
        session.dog_info_collected = True
        
        # Store perspective if available
        if package.dog_perspective and hasattr(session, 'dog_perspective'):
            session.dog_perspective = package.dog_perspective
        
        # Store metadata for analytics
        if hasattr(session, 'agentic_metadata'):
            session.agentic_metadata = package.metadata
        
        # Set appropriate flow step
        session.current_step = FlowStep.WAIT_FOR_SYMPTOM
        
        self.logger.info(
            f"Executed handoff for session {session.session_id[:8]}... "
            f"Transferred: name={package.dog_name}, breed={package.dog_breed}, "
            f"symptom_length={len(package.symptom)}"
        )
    
    def validate_handoff_readiness(
        self,
        state: UnifiedConversationState
    ) -> Dict[str, Any]:
        """
        Check if state is ready for handoff and provide detailed status.
        
        Args:
            state: Current conversation state
            
        Returns:
            Dict with readiness status and details
        """
        missing_fields = state.get_missing_fields()
        completion_pct = state.get_completion_percentage()
        
        readiness = {
            "ready": state.is_ready_for_handoff(),
            "completion_percentage": completion_pct,
            "missing_fields": missing_fields,
            "has_perspective": state.perspective_generated,
            "confidence_report": state.confidence.copy(),
            "conversation_metrics": {
                "turns": state.memory.turn_counter,
                "duration_seconds": state.memory.get_conversation_duration()
            }
        }
        
        # Add specific issues
        issues = []
        
        if missing_fields:
            issues.append(f"Missing fields: {', '.join(missing_fields)}")
        
        if not state.perspective_generated:
            issues.append("Dog perspective not yet generated")
        
        # Check confidence levels
        low_confidence = [
            f"{field} ({conf:.1f})"
            for field, conf in state.confidence.items()
            if conf > 0 and conf < 0.7
        ]
        if low_confidence:
            issues.append(f"Low confidence: {', '.join(low_confidence)}")
        
        readiness["issues"] = issues
        
        return readiness
    
    def create_transition_messages(
        self,
        package: HandoffPackage
    ) -> List[Dict[str, str]]:
        """
        Create transition messages for smooth handoff.
        
        Args:
            package: Handoff package with information
            
        Returns:
            List of messages to display during transition
        """
        messages = []
        
        # Acknowledgment of collected information
        info_parts = []
        if package.dog_name:
            info_parts.append(f"{package.dog_name}")
        if package.dog_breed:
            info_parts.append(f"({package.dog_breed})")
        
        if info_parts:
            messages.append({
                "sender": "system",
                "text": f"*aufmerksam* Okay, ich habe alles über {' '.join(info_parts)} verstanden.",
                "type": "transition"
            })
        
        # Transition to detailed analysis
        messages.append({
            "sender": "system", 
            "text": "*konzentriert* Lass uns nun genauer schauen, was hinter diesem Verhalten steckt...",
            "type": "transition"
        })
        
        return messages
    
    def rollback_handoff(
        self,
        session: SessionState,
        reason: str
    ) -> None:
        """
        Rollback a failed handoff attempt.
        
        Args:
            session: Session to rollback
            reason: Reason for rollback
        """
        self.logger.warning(f"Rolling back handoff for session {session.session_id[:8]}: {reason}")
        
        # Reset to pre-handoff state
        session.current_step = FlowStep.AGENTIC_COLLECTION
        session.dog_info_collected = False
        
        # Clear transferred data if needed
        if hasattr(session, 'agentic_metadata'):
            delattr(session, 'agentic_metadata')
    
    def get_handoff_summary(
        self,
        package: HandoffPackage
    ) -> str:
        """
        Generate a summary of the handoff for logging/debugging.
        
        Args:
            package: Handoff package
            
        Returns:
            Formatted summary string
        """
        summary_parts = [
            f"Handoff Summary for {package.session_id[:8]}:",
            f"- Dog: {package.dog_name} ({package.dog_breed})",
            f"- Concern: {package.symptom[:50]}..." if len(package.symptom) > 50 else f"- Concern: {package.symptom}",
            f"- User: {package.user_name or 'Unknown'}",
            f"- Conversation: {package.metadata.get('turns', 0)} turns, "
            f"{package.metadata.get('duration_seconds', 0):.1f}s",
            f"- Confidence: " + ", ".join([
                f"{k}={v:.1f}" 
                for k, v in package.metadata.get('confidence_scores', {}).items()
                if v > 0
            ])
        ]
        
        if package.dog_perspective:
            summary_parts.append(f"- Perspective: Generated ({len(package.dog_perspective)} chars)")
        
        return "\n".join(summary_parts)