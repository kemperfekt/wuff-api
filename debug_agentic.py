#!/usr/bin/env python3
"""
Debug script to test agentic conversation system goal progression.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.agentic_conversation_manager import AgenticConversationManager
from src.core.simple_prompt_builder import SimplePromptBuilder
from src.models.agentic_models import ConversationContext, EmotionalState
from src.services.gpt_service import GPTService
from src.tools.tool_registry import ToolRegistry
from src.tools.session_tool import SessionManagerTool

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def debug_conversation_flow():
    """Debug the conversation flow step by step."""
    
    # Initialize minimal components
    gpt_service = GPTService()
    tool_registry = ToolRegistry()
    tool_registry.register_tool(SessionManagerTool())
    prompt_builder = SimplePromptBuilder()
    
    manager = AgenticConversationManager(
        gpt_service=gpt_service,
        tool_registry=tool_registry,
        prompt_builder=prompt_builder
    )
    
    # Create initial conversation context
    context = ConversationContext()
    print(f"Initial context: dog_name={context.dog_name}, main_concern={context.main_concern}")
    print(f"Initial goals: {manager._get_active_goals(context)}")
    print()
    
    # Test sequence of inputs
    test_inputs = [
        "Mein Hund zieht an der Leine",
        "Mein Hund heißt Max und er ist ein Golden Retriever", 
        "Er zieht besonders stark im Park wenn andere Hunde da sind"
    ]
    
    for i, user_input in enumerate(test_inputs, 1):
        print(f"=== Turn {i}: {user_input} ===")
        
        # Get active goals before processing
        active_goals = manager._get_active_goals(context)
        print(f"Active goals: {active_goals}")
        
        try:
            # Create action plan
            action_plan = await manager._create_action_plan(user_input, context)
            print(f"Action plan created:")
            print(f"  Goal: {action_plan.conversation_goal}")
            print(f"  Extracted info: {action_plan.extracted_info}")
            print(f"  Tool calls: {len(action_plan.tool_calls)}")
            
            # Check what information was extracted
            if action_plan.extracted_info.has_any_info():
                print(f"  Found info:")
                if action_plan.extracted_info.dog_name:
                    print(f"    Dog name: {action_plan.extracted_info.dog_name}")
                if action_plan.extracted_info.dog_breed:
                    print(f"    Dog breed: {action_plan.extracted_info.dog_breed}")
                if action_plan.extracted_info.main_concern:
                    print(f"    Main concern: {action_plan.extracted_info.main_concern}")
            
            # Simulate full response (without tool execution for simplicity)
            response = await manager._synthesize_response(action_plan, [], context)
            print(f"Response: {response.message[:100]}...")
            print(f"Goals progressed: {response.goals_progressed}")
            
            # Update context
            manager._update_context(context, action_plan, response)
            print(f"Updated context: dog_name={context.dog_name}, main_concern={context.main_concern}")
            print(f"Goals achieved: {context.goals_achieved}")
            print()
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            print()

if __name__ == "__main__":
    asyncio.run(debug_conversation_flow())