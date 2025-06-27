# src/models/agentic_models.py

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class ConversationPhase(str, Enum):
    """Phases of the agentic conversation"""
    COLLECTING = "collecting"  # Still gathering information
    PERSPECTIVE = "perspective"  # Generating dog perspective
    HANDOFF = "handoff"  # Ready to hand off to static flow
    INSTINCT_ANALYSIS = "instinct_analysis"  # Analyzing root instinct
    EXERCISE_OFFER = "exercise_offer"  # Offering training plan
    COMPLETED = "completed"  # Flow completed


class InformationStatus(BaseModel):
    """Track what information we have collected from the user"""
    user_name: Optional[str] = None
    dog_name: Optional[str] = None
    dog_breed: Optional[str] = None
    main_concern: Optional[str] = None
    perspective_given: bool = False
    ready_for_handoff: bool = False
    
    def get_missing_information(self) -> List[str]:
        """Return list of missing required information"""
        missing = []
        
        # Required information (user_name is optional)
        if not self.dog_name:
            missing.append("dog_name")
        if not self.dog_breed:
            missing.append("dog_breed")
        if not self.main_concern:
            missing.append("main_concern")
            
        return missing
    
    def all_required_collected(self) -> bool:
        """Check if all required information is collected"""
        return len(self.get_missing_information()) == 0
    
    def get_current_phase(self) -> ConversationPhase:
        """Determine current conversation phase"""
        if not self.all_required_collected():
            return ConversationPhase.COLLECTING
        elif not self.perspective_given:
            return ConversationPhase.PERSPECTIVE
        elif not self.ready_for_handoff:
            return ConversationPhase.HANDOFF
        else:
            return ConversationPhase.COMPLETED


class ActionPlan(BaseModel):
    """Structured output for LLM conversation planning"""
    next_question: str
    information_needed: str  # "dog_name", "dog_breed", "main_concern", "handoff_decision"
    confidence: float = Field(ge=0.0, le=1.0)  # 0.0-1.0 confidence in the plan
    should_handoff: bool = False
    reasoning: Optional[str] = None  # Why this action was chosen (for debugging)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "next_question": "Wie heißt denn dein Hund?",
                "information_needed": "dog_name",
                "confidence": 0.9,
                "should_handoff": False,
                "reasoning": "User hasn't provided dog name yet, this is essential for personalization"
            }
        }
    }


class ConversationContext(BaseModel):
    """Context for agentic conversation planning"""
    message_history: List[Dict[str, str]] = Field(default_factory=list)
    information_status: InformationStatus = Field(default_factory=InformationStatus)
    exchange_count: int = 0
    current_phase: ConversationPhase = ConversationPhase.COLLECTING
    
    # Tracking for cost optimization
    llm_calls_made: int = 0
    total_tokens_used: int = 0
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation history"""
        self.message_history.append({"role": role, "content": content})
        if role == "user":
            self.exchange_count += 1
    
    def update_phase(self):
        """Update the current phase based on information status"""
        self.current_phase = self.information_status.get_current_phase()
    
    def track_llm_call(self, tokens_used: int = 0):
        """Track LLM usage for cost monitoring"""
        self.llm_calls_made += 1
        self.total_tokens_used += tokens_used


class ToolResult(BaseModel):
    """Result from a tool execution"""
    tool_name: str
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "tool_name": "weaviate_perspective",
                "success": True,
                "result": "Als Balu verstehe ich, dass Max nicht böse ist...",
                "error": None,
                "execution_time_ms": 234.5
            }
        }
    }


class AgenticResponse(BaseModel):
    """Response from the agentic dog agent"""
    message: str
    phase: ConversationPhase
    information_collected: InformationStatus
    should_transition: bool = False  # Should transition to static flow
    next_flow_step: Optional[str] = None  # Next step in static flow
    tool_results: List[ToolResult] = Field(default_factory=list)
    cost_info: Optional[Dict[str, Any]] = None  # Cost tracking information
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "*aufmerksam-blick* Wie heißt denn dein Hund?",
                "phase": "collecting",
                "information_collected": {
                    "user_name": None,
                    "dog_name": None,
                    "dog_breed": None,
                    "main_concern": None,
                    "perspective_given": False,
                    "ready_for_handoff": False
                },
                "should_transition": False,
                "next_flow_step": None,
                "tool_results": [],
                "cost_info": {"tokens_used": 45, "estimated_cost_euros": 0.001}
            }
        }
    }