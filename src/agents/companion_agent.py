# src/v2/agents/companion_agent.py
"""
V2 Companion Agent - Clean message formatting for feedback collection.

This agent handles ONLY message formatting for the feedback collection process.
All business logic (saving feedback, GDPR compliance, etc.) is handled by services.
"""

from typing import List, Dict, Optional, Any
from src.agents.base_agent import BaseAgent, AgentContext, MessageType, V2AgentMessage
from src.core.prompt_manager import PromptType
from src.core.exceptions import V2AgentError, V2ValidationError


class CompanionAgent(BaseAgent):
    """
    Agent that formats feedback collection messages.
    
    Responsibilities:
    - Format feedback questions in sequence
    - Generate feedback completion messages
    - Handle feedback-related instructions
    - Format thank you messages
    
    Business logic like feedback storage, GDPR compliance, etc. 
    is handled by the flow engine and services.
    """
    
    def __init__(self, **kwargs):
        """Initialize CompanionAgent with feedback-specific configuration."""
        super().__init__(
            name="Begleiter",
            role="companion",
            **kwargs
        )
        
        # Companion-specific message configuration
        self._default_temperature = 0.3  # More consistent for feedback questions
        
        # Feedback question sequence (will be loaded from PromptManager)
        self._feedback_question_count = 5
        
    def get_supported_message_types(self) -> List[MessageType]:
        """Return message types this agent supports."""
        return [
            MessageType.GREETING,
            MessageType.QUESTION,
            MessageType.RESPONSE,
            MessageType.CONFIRMATION,
            MessageType.ERROR
        ]
    
    async def respond(self, context: AgentContext) -> List[V2AgentMessage]:
        """
        Generate companion messages based on context.
        
        Args:
            context: Agent context with user input and metadata
            
        Returns:
            List of formatted companion messages
            
        Raises:
            V2AgentError: If message generation fails
            V2ValidationError: If context is invalid
        """
        # Validate context - but catch validation errors and handle gracefully
        try:
            self.validate_context(context)
        except V2ValidationError as e:
            # Return error message instead of raising exception
            return [self.create_error_message(str(e))]
        
        try:
            # Route to appropriate message handler based on message type
            if context.message_type == MessageType.GREETING:
                return await self._handle_greeting(context)
            elif context.message_type == MessageType.QUESTION:
                return await self._handle_question(context)
            elif context.message_type == MessageType.RESPONSE:
                return await self._handle_response(context)
            elif context.message_type == MessageType.CONFIRMATION:
                return await self._handle_confirmation(context)
            elif context.message_type == MessageType.ERROR:
                return await self._handle_error(context)
            else:
                raise V2AgentError(f"Unsupported message type: {context.message_type}")
                
        except Exception as e:
            # Fallback to error message if anything goes wrong
            return [self.create_error_message(str(e))]
    
    async def _handle_greeting(self, context: AgentContext) -> List[V2AgentMessage]:
        """
        Generate feedback introduction message.
        
        Args:
            context: Agent context
            
        Returns:
            List with feedback introduction message
        """
        intro_text = self.prompt_manager.get_prompt(PromptType.COMPANION_FEEDBACK_INTRO)
        return [self.create_message(intro_text, MessageType.GREETING)]
    
    async def _handle_question(self, context: AgentContext) -> List[V2AgentMessage]:
        """
        Generate feedback questions based on question number.
        
        Args:
            context: Agent context with question_number in metadata
            
        Returns:
            List with feedback question message
        """
        question_number = context.metadata.get('question_number', 1)
        
        # Validate question number
        if not (1 <= question_number <= self._feedback_question_count):
            raise V2AgentError(f"Invalid question number: {question_number}")
        
        # Get the appropriate feedback question from PromptManager
        question_text = self._get_feedback_question(question_number)
        
        return [self.create_message(question_text, MessageType.QUESTION)]
    
    async def _handle_response(self, context: AgentContext) -> List[V2AgentMessage]:
        """
        Generate response messages for feedback flow.
        
        The type of response depends on context metadata:
        - 'acknowledgment': Acknowledge received feedback
        - 'completion': Final thank you message
        - 'progress': Progress indicator between questions
        
        Args:
            context: Agent context with response data
            
        Returns:
            List of response messages
        """
        response_mode = context.metadata.get('response_mode', 'acknowledgment')
        
        if response_mode == 'acknowledgment':
            return await self._generate_acknowledgment(context)
        elif response_mode == 'completion':
            return await self._generate_completion(context)
        elif response_mode == 'progress':
            return await self._generate_progress(context)
        else:
            raise V2AgentError(f"Unknown response mode: {response_mode}")
    
    async def _handle_confirmation(self, context: AgentContext) -> List[V2AgentMessage]:
        """
        Generate confirmation messages for feedback process.
        
        Args:
            context: Agent context
            
        Returns:
            List with confirmation message
        """
        confirmation_type = context.metadata.get('confirmation_type', 'proceed')
        
        if confirmation_type == 'proceed':
            text = self.prompt_manager.get_prompt(PromptType.COMPANION_PROCEED_CONFIRMATION)
        elif confirmation_type == 'skip':
            text = self.prompt_manager.get_prompt(PromptType.COMPANION_SKIP_CONFIRMATION)
        else:
            text = "Möchtest du fortfahren?"
        
        return [self.create_message(text, MessageType.CONFIRMATION)]
    
    async def _handle_error(self, context: AgentContext) -> List[V2AgentMessage]:
        """
        Generate error messages for feedback process.
        
        Args:
            context: Agent context
            
        Returns:
            List with error message
        """
        error_type = context.metadata.get('error_type', 'general')
        
        if error_type == 'invalid_feedback':
            text = self.prompt_manager.get_prompt(PromptType.COMPANION_INVALID_FEEDBACK_ERROR)
        elif error_type == 'save_failed':
            text = self.prompt_manager.get_prompt(PromptType.COMPANION_SAVE_ERROR)
        else:
            text = "Es gab ein Problem mit dem Feedback. Bitte versuche es erneut."
        
        return [self.create_message(text, MessageType.ERROR)]
    
    def _get_feedback_question(self, question_number: int) -> str:
        """
        Get feedback question by number from PromptManager.
        
        Args:
            question_number: Question number (1-5)
            
        Returns:
            Formatted feedback question text
            
        Raises:
            V2AgentError: If question not found
        """
        try:
            # Map question numbers to prompt types
            question_map = {
                1: PromptType.COMPANION_FEEDBACK_Q1,
                2: PromptType.COMPANION_FEEDBACK_Q2,
                3: PromptType.COMPANION_FEEDBACK_Q3,
                4: PromptType.COMPANION_FEEDBACK_Q4,
                5: PromptType.COMPANION_FEEDBACK_Q5,
            }
            
            prompt_type = question_map.get(question_number)
            if not prompt_type:
                raise V2AgentError(f"No prompt found for question number {question_number}")
            
            return self.prompt_manager.get_prompt(prompt_type)
            
        except Exception as e:
            raise V2AgentError(f"Failed to get feedback question {question_number}: {str(e)}") from e
    
    async def _generate_acknowledgment(self, context: AgentContext) -> List[V2AgentMessage]:
        """
        Generate acknowledgment message for received feedback.
        
        Args:
            context: Agent context
            
        Returns:
            List with acknowledgment message
        """
        # Simple acknowledgment for continuing feedback flow
        ack_text = self.prompt_manager.get_prompt(PromptType.COMPANION_FEEDBACK_ACK)
        return [self.create_message(ack_text, MessageType.RESPONSE)]
    
    async def _generate_completion(self, context: AgentContext) -> List[V2AgentMessage]:
        """
        Generate completion message after all feedback collected.
        
        Args:
            context: Agent context
            
        Returns:
            List with completion/thank you message
        """
        # Check if feedback was successfully saved
        save_success = context.metadata.get('save_success', True)
        
        if save_success:
            completion_text = self.prompt_manager.get_prompt(PromptType.COMPANION_FEEDBACK_COMPLETE)
        else:
            completion_text = self.prompt_manager.get_prompt(PromptType.COMPANION_FEEDBACK_COMPLETE_NOSAVE)
        
        return [self.create_message(completion_text, MessageType.RESPONSE)]
    
    async def _generate_progress(self, context: AgentContext) -> List[V2AgentMessage]:
        """
        Generate progress indicator message between questions.
        
        Args:
            context: Agent context with progress info
            
        Returns:
            List with progress message (optional - can be empty)
        """
        # For now, we don't show progress indicators
        # This could be enhanced to show "Frage 2 von 5" etc.
        return []
    
    def get_feedback_question_count(self) -> int:
        """
        Get the total number of feedback questions.
        
        Returns:
            Number of feedback questions
        """
        return self._feedback_question_count
    
    def validate_question_number(self, question_number: int) -> bool:
        """
        Validate if a question number is valid.
        
        Args:
            question_number: Question number to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Handle non-integer types
        if not isinstance(question_number, int):
            return False
            
        return 1 <= question_number <= self._feedback_question_count
    
    def _validate_context_impl(self, context: AgentContext) -> None:
        """
        Validate companion-specific context requirements.
        
        Args:
            context: Context to validate
            
        Raises:
            V2ValidationError: If context is invalid for companion agent
        """
        # For question messages, we need a question number
        if context.message_type == MessageType.QUESTION:
            question_number = context.metadata.get('question_number')
            if question_number is None:
                raise V2ValidationError("Question context requires 'question_number' in metadata")
            
            if not self.validate_question_number(question_number):
                raise V2ValidationError(f"Invalid question number: {question_number}")
        
        # For response messages, we need a response mode
        if context.message_type == MessageType.RESPONSE:
            response_mode = context.metadata.get('response_mode')
            if not response_mode:
                raise V2ValidationError("Response context requires 'response_mode' in metadata")
    
    def create_error_message(self, error_msg: str) -> V2AgentMessage:
        """
        Override to create companion-specific error messages.
        
        Args:
            error_msg: Technical error message
            
        Returns:
            Companion-friendly error message
        """
        # Get companion-specific error message from prompts
        try:
            friendly_msg = self.prompt_manager.get_prompt(PromptType.COMPANION_GENERAL_ERROR)
        except:
            # Ultimate fallback
            friendly_msg = "Es tut mir leid, es gab ein Problem. Bitte versuche es erneut."
        
        return self.create_message(friendly_msg, MessageType.ERROR)
    
    async def create_feedback_sequence(self, session_id: str) -> List[AgentContext]:
        """
        Helper method to create context sequence for complete feedback flow.
        
        This is a utility method that the flow engine can use to get all
        contexts needed for the complete feedback sequence.
        
        Args:
            session_id: Session ID for the feedback flow
            
        Returns:
            List of AgentContext objects for the complete feedback sequence
        """
        contexts = []
        
        # Add intro context
        contexts.append(AgentContext(
            session_id=session_id,
            message_type=MessageType.GREETING,
            metadata={'sequence_step': 'intro'}
        ))
        
        # Add question contexts
        for i in range(1, self._feedback_question_count + 1):
            contexts.append(AgentContext(
                session_id=session_id,
                message_type=MessageType.QUESTION,
                metadata={
                    'question_number': i,
                    'sequence_step': f'question_{i}'
                }
            ))
        
        # Add completion context
        contexts.append(AgentContext(
            session_id=session_id,
            message_type=MessageType.RESPONSE,
            metadata={
                'response_mode': 'completion',
                'sequence_step': 'completion'
            }
        ))
        
        return contexts