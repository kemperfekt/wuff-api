# src/v2/agents/dog_agent.py
"""
V2 Dog Agent - Clean message formatting focused on dog perspective responses.

This agent handles ONLY message formatting for dog-perspective responses.
All business logic (RAG analysis, symptom checking, etc.) is handled by services.
"""

from typing import List, Dict, Optional, Any
from src.agents.base_agent import BaseAgent, AgentContext, MessageType, V2AgentMessage
from src.core.exceptions import V2AgentError, V2ValidationError
from src.core.prompt_manager import PromptType, PromptCategory
from src.prompts.generation_prompts import DOG_AGENT_SYSTEM


class DogAgent(BaseAgent):
    """
    Agent that formats responses from a dog's perspective.
    
    Responsibilities:
    - Format greeting messages
    - Generate dog perspective responses using prompts
    - Format diagnostic messages
    - Format exercise recommendations
    - Handle error messages in dog voice
    
    Business logic like RAG analysis, symptom validation, etc. 
    is handled by the flow engine and services.
    """
    
    def __init__(self, **kwargs):
        """Initialize DogAgent with dog-specific configuration."""
        super().__init__(
            name="Hund",
            role="dog",
            **kwargs
        )
        
        # Dog-specific message configuration
        self._default_temperature = 0.8  # More personality for dog responses
        self._system_prompt = DOG_AGENT_SYSTEM
        
    def get_supported_message_types(self) -> List[MessageType]:
        """Return message types this agent supports."""
        return [
            MessageType.GREETING,
            MessageType.RESPONSE,
            MessageType.QUESTION,
            MessageType.ERROR,
            MessageType.INSTRUCTION
        ]
    
    async def respond(self, context: AgentContext) -> List[V2AgentMessage]:
        """
        Generate dog perspective messages based on context.
        
        Args:
            context: Agent context with user input and metadata
            
        Returns:
            List of formatted dog messages
            
        Raises:
            V2AgentError: If message generation fails
            V2ValidationError: If context is invalid
        """
        # Validate context - but handle validation errors gracefully
        try:
            self.validate_context(context)
        except V2ValidationError as e:
            # Return user-friendly error message instead of raising
            return [self.create_message(
                "Es tut mir leid, ich verstehe gerade nicht ganz. Kannst du es nochmal versuchen?",
                MessageType.ERROR
            )]
        
        try:
            # Route to appropriate message handler based on message type
            if context.message_type == MessageType.GREETING:
                return await self._handle_greeting(context)
            elif context.message_type == MessageType.RESPONSE:
                return await self._handle_response(context)
            elif context.message_type == MessageType.QUESTION:
                return await self._handle_question(context)
            elif context.message_type == MessageType.ERROR:
                return await self._handle_error(context)
            elif context.message_type == MessageType.INSTRUCTION:
                return await self._handle_instruction(context)
            else:
                raise V2AgentError(f"Unsupported message type: {context.message_type}")
                
        except Exception as e:
            # Fallback to error message if anything goes wrong
            return [self.create_error_message(str(e))]
    
    async def _handle_greeting(self, context: AgentContext) -> List[V2AgentMessage]:
        """
        Generate greeting messages from dog perspective.
        
        Args:
            context: Agent context
            
        Returns:
            List of greeting messages
        """
        try:
            # Debug: List available prompts
            
            # Try to get greeting prompts with fallbacks
            try:
                greeting_text = self.prompt_manager.get_prompt(PromptType.DOG_GREETING)
            except Exception as e:
                # Fallback greeting
                greeting_text = "Wuff! Schön, dass Du da bist. Bitte nenne mir ein Verhalten und ich schildere dir, wie ich es erlebe."
            
            try:
                follow_up_text = self.prompt_manager.get_prompt(PromptType.DOG_GREETING_FOLLOWUP)
            except Exception as e:
                # Fallback follow-up
                follow_up_text = "Beschreib mir bitte, was du beobachtet hast."
            
            return [
                self.create_message(greeting_text, MessageType.GREETING),
                self.create_message(follow_up_text, MessageType.QUESTION)
            ]
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            # Return fallback messages instead of raising
            return [
                self.create_message(
                    "Wuff! Schön, dass Du da bist. Bitte nenne mir ein Verhalten und ich schildere dir, wie ich es erlebe.",
                    MessageType.GREETING
                ),
                self.create_message(
                    "Was ist los? Beschreib mir bitte, was du beobachtet hast.",
                    MessageType.QUESTION
                )
            ]
    
    async def _handle_response(self, context: AgentContext) -> List[V2AgentMessage]:
        """
        Generate response messages from dog perspective.
        
        The type of response depends on context metadata:
        - 'perspective_only': Just dog perspective
        - 'diagnosis': Instinct-based diagnosis  
        - 'exercise': Exercise recommendation
        - 'full_response': Complete response flow
        
        Args:
            context: Agent context with response data
            
        Returns:
            List of response messages
        """
        response_mode = context.metadata.get('response_mode', 'perspective_only')
        
        if response_mode == 'perspective_only':
            return await self._generate_dog_perspective(context)
        elif response_mode == 'diagnosis':
            return await self._generate_diagnosis(context)
        elif response_mode == 'exercise':
            return await self._generate_exercise_response(context)
        elif response_mode == 'full_response':
            return await self._generate_full_response(context)
        else:
            raise V2AgentError(f"Unknown response mode: {response_mode}")
    
    async def _handle_question(self, context: AgentContext) -> List[V2AgentMessage]:
        """
        Generate question messages from dog perspective.
        
        Args:
            context: Agent context
            
        Returns:
            List of question messages
        """
        question_type = context.metadata.get('question_type', 'confirmation')
        
        
        if question_type == 'confirmation':
            text = self.prompt_manager.get_prompt(PromptType.DOG_CONFIRMATION_QUESTION)
        elif question_type == 'context':
            text = self.prompt_manager.get_prompt(PromptType.DOG_CONTEXT_QUESTION)
        elif question_type == 'exercise':
            text = self.prompt_manager.get_prompt(PromptType.DOG_EXERCISE_QUESTION)
        elif question_type == 'restart':
            text = self.prompt_manager.get_prompt(PromptType.DOG_CONTINUE_OR_RESTART)
        elif question_type == 'ask_for_more':
            text = self.prompt_manager.get_prompt(PromptType.DOG_ASK_FOR_MORE)
        else:
            # Fallback to generic question
            text = "Was möchtest du wissen?"
        
        return [self.create_message(text, MessageType.QUESTION)]
    
    async def _handle_error(self, context: AgentContext) -> List[V2AgentMessage]:
        """
        Generate error messages from dog perspective.
        
        Args:
            context: Agent context
            
        Returns:
            List of error messages
        """
        error_type = context.metadata.get('error_type', 'general')
        
        if error_type == 'no_match':
            text = self.prompt_manager.get_prompt(PromptType.DOG_NO_MATCH_ERROR)
        elif error_type == 'no_behavior_match':
            text = self.prompt_manager.get_prompt(PromptType.NO_BEHAVIOR_MATCH)
        elif error_type == 'not_dog_related':
            text = self.prompt_manager.get_prompt(PromptType.DOG_SILLY_INPUT_REJECTION)
        elif error_type == 'input_too_short':
            text = self.prompt_manager.get_prompt(PromptType.INPUT_TOO_SHORT)
        elif error_type == 'context_too_short':
            text = "Ich brauche noch ein bisschen mehr Info… Wo war das genau, was war da los?"
        elif error_type == 'invalid_yes_no':
            text = self.prompt_manager.get_prompt(PromptType.INVALID_YES_NO)
        elif error_type == 'invalid_input':
            text = self.prompt_manager.get_prompt(PromptType.DOG_INVALID_INPUT_ERROR)
        elif error_type == 'technical':
            text = self.prompt_manager.get_prompt(PromptType.DOG_TECHNICAL_ERROR)
        else:
            text = "Es tut mir leid, ich verstehe gerade nicht ganz. Kannst du es nochmal versuchen?"
        
        return [self.create_message(text, MessageType.ERROR)]
    
    async def _handle_instruction(self, context: AgentContext) -> List[V2AgentMessage]:
        """
        Generate instruction messages from dog perspective.
        
        Args:
            context: Agent context
            
        Returns:
            List of instruction messages
        """
        instruction_type = context.metadata.get('instruction_type', 'general')
        
        if instruction_type == 'describe_more':
            text = self.prompt_manager.get_prompt(PromptType.DOG_DESCRIBE_MORE)
        elif instruction_type == 'be_specific':
            text = self.prompt_manager.get_prompt(PromptType.DOG_BE_SPECIFIC)
        else:
            text = "Kannst du mir mehr erzählen?"
        
        return [self.create_message(text, MessageType.INSTRUCTION)]
    
    async def _generate_dog_perspective(self, context: AgentContext) -> List[V2AgentMessage]:
        """
        Generate dog perspective response using analysis data.
        
        Args:
            context: Context containing analysis results in metadata
            
        Returns:
            List with dog perspective message
        """
        # Extract analysis data from context
        symptom = context.user_input
        analysis_data = context.metadata.get('analysis_data', {})
        match_data = context.metadata.get('match_data', '')
        
        # Use PromptManager to get dog perspective prompt and generate response
        if match_data:
            # Use match-based perspective if we have exact match
            dog_perspective = await self.generate_text_with_prompt(
                PromptType.DOG_PERSPECTIVE,
                symptom=symptom,
                match=match_data,
                temperature=self._default_temperature
            )
        else:
            # Use analysis-based perspective
            primary_instinct = analysis_data.get('primary_instinct', 'unbekannt')
            primary_description = analysis_data.get('primary_description', '')
            all_instincts = analysis_data.get('all_instincts', {})
            
            dog_perspective = await self.generate_text_with_prompt(
                PromptType.DOG_INSTINCT_PERSPECTIVE,
                symptom=symptom,
                primary_instinct=primary_instinct,
                primary_description=primary_description,
                jagd=all_instincts.get('jagd', ''),
                rudel=all_instincts.get('rudel', ''),
                territorial=all_instincts.get('territorial', ''),
                sexual=all_instincts.get('sexual', ''),
                temperature=self._default_temperature
            )
        
        return [self.create_message(dog_perspective, MessageType.RESPONSE)]
    
    async def _generate_diagnosis(self, context: AgentContext) -> List[V2AgentMessage]:
        """
        Generate diagnosis message from dog perspective.
        
        Args:
            context: Context containing analysis results
            
        Returns:
            List with diagnosis message
        """
       
       
        analysis_data = context.metadata.get('analysis_data', {})
        primary_instinct = analysis_data.get('primary_instinct', 'unbekannter Instinkt')
        primary_description = analysis_data.get('primary_description', 'Keine Beschreibung verfügbar')
        

        try:
            # Get all instinct descriptions from analysis data
            all_instincts = analysis_data.get('all_instincts', {})
            symptom = context.metadata.get('symptom', 'unbekanntes Verhalten')
            user_context = context.metadata.get('context', '')
            
            # Use the proper instinct diagnosis template with all RAG data
            diagnosis_text = await self.generate_text_with_prompt(
                PromptType.DOG_INSTINCT_DIAGNOSIS,
                symptom=symptom,
                context=user_context,
                jagd=all_instincts.get('jagd', 'Keine Jagdinstinkt-Information gefunden'),
                rudel=all_instincts.get('rudel', 'Keine Rudelinstinkt-Information gefunden'),
                territorial=all_instincts.get('territorial', 'Keine Territorialinstinkt-Information gefunden'),
                sexual=all_instincts.get('sexual', 'Keine Sexualinstinkt-Information gefunden'),
                temperature=self._default_temperature
            )

            
            return [self.create_message(diagnosis_text, MessageType.RESPONSE)]
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            # Return error message
            return [self.create_message(self.prompt_manager.get_prompt(PromptType.DOG_TECHNICAL_ERROR), MessageType.ERROR)]


    async def _generate_exercise_response(self, context: AgentContext) -> List[V2AgentMessage]:
        """
        Generate exercise recommendation response.
        
        Args:
            context: Context containing exercise data
            
        Returns:
            List with exercise message
        """
        exercise_data = context.metadata.get('exercise_data', '')
        
        if exercise_data:
            # Format the exercise recommendation
            return [self.create_message(exercise_data, MessageType.RESPONSE)]
        else:
            # Generate fallback exercise - don't require exercise_data
            fallback_exercise = self.prompt_manager.get_prompt(PromptType.DOG_FALLBACK_EXERCISE)
            return [self.create_message(fallback_exercise, MessageType.RESPONSE)]
    
    async def _generate_full_response(self, context: AgentContext) -> List[V2AgentMessage]:
        """
        Generate complete response flow (perspective + exercise offer).
        
        Args:
            context: Context with all necessary data
            
        Returns:
            List with multiple messages for full flow
        """
        messages = []
        
        # Generate dog perspective
        perspective_messages = await self._generate_dog_perspective(context)
        messages.extend(perspective_messages)
        
        # Add exercise offer if exercise data available
        if context.metadata.get('exercise_data'):
            exercise_messages = await self._generate_exercise_response(context)
            messages.extend(exercise_messages)
            
            # Add follow-up question
            followup_text = self.prompt_manager.get_prompt(PromptType.DOG_ANOTHER_BEHAVIOR_QUESTION)
            messages.append(self.create_message(followup_text, MessageType.QUESTION))
        
        return messages
    
    def _validate_context_impl(self, context: AgentContext) -> None:
        """
        Validate dog-specific context requirements.
        
        Args:
            context: Context to validate
            
        Raises:
            V2ValidationError: If context is invalid for dog agent
        """
        # For response messages, we usually need some data - but be more lenient
        if context.message_type == MessageType.RESPONSE:
            response_mode = context.metadata.get('response_mode')
            if not response_mode:
                raise V2ValidationError("Response context requires 'response_mode' in metadata")
            
            # Only validate required data for modes that actually need it
            if response_mode == 'diagnosis' and not context.metadata.get('analysis_data'):
                raise V2ValidationError(f"Response mode '{response_mode}' requires 'analysis_data' in metadata")
            
            # For exercise mode, don't require exercise_data - we have fallback
            # if response_mode == 'exercise' and not context.metadata.get('exercise_data'):
            #     raise V2ValidationError("Exercise response mode requires 'exercise_data' in metadata")
    
    def create_error_message(self, error_msg: str) -> V2AgentMessage:
        """
        Override to create dog-specific error messages.
        
        Args:
            error_msg: Technical error message
            
        Returns:
            Dog-friendly error message
        """
        # Get dog-specific error message from prompts
        try:
            friendly_msg = self.prompt_manager.get_prompt(PromptType.DOG_TECHNICAL_ERROR)
        except:
            # Ultimate fallback
            friendly_msg = "Wuff! Entschuldige, ich bin gerade etwas verwirrt. Kannst du es nochmal versuchen?"
        
        return self.create_message(friendly_msg, MessageType.ERROR)