# tests/v2/agents/demo_agents.py
"""
Interactive demo for V2 Agents.

Run this file to see how the agents work in practice:
    python -m tests.v2.agents.demo_agents
"""

import asyncio
import sys
from typing import List
from unittest.mock import AsyncMock

from src.v2.agents.dog_agent import DogAgent
from src.v2.agents.companion_agent import CompanionAgent
from src.v2.agents.base_agent import AgentContext, MessageType, V2AgentMessage
from src.v2.core.prompt_manager import PromptManager
from src.v2.services.gpt_service import GPTService


class AgentDemo:
    """Interactive demonstration of V2 agents"""
    
    def __init__(self):
        # Initialize real PromptManager
        self.prompt_manager = PromptManager()
        self.prompt_manager.load_prompts()
        
        # Mock GPT service for demo
        self.mock_gpt = AsyncMock(spec=GPTService)
        self.setup_mock_responses()
        
        # Initialize agents
        self.dog_agent = DogAgent(
            prompt_manager=self.prompt_manager,
            gpt_service=self.mock_gpt
        )
        
        self.companion_agent = CompanionAgent(
            prompt_manager=self.prompt_manager
        )
        
        self.session_id = "demo-session"
    
    def setup_mock_responses(self):
        """Setup realistic mock responses for demo"""
        self.gpt_responses = [
            "Als Hund belle ich, weil ich mein Zuhause beschützen will! Wenn jemand Fremdes kommt, ist es meine Aufgabe, dich zu warnen.",
            "Mein Territorialinstinkt ist hier sehr stark. Ich fühle mich verantwortlich für unser gemeinsames Revier.",
            "Bei mir ist der Schutzinstinkt aktiv - ich will sicherstellen, dass keine Gefahr droht!"
        ]
        self.response_index = 0
        
        def mock_complete(*args, **kwargs):
            response = self.gpt_responses[self.response_index % len(self.gpt_responses)]
            self.response_index += 1
            return response
        
        self.mock_gpt.complete.side_effect = mock_complete
    
    def print_message(self, message: V2AgentMessage, prefix: str = ""):
        """Pretty print a message"""
        emoji = "🐕" if message.sender == "dog" else "🤝"
        print(f"{prefix}{emoji} {message.sender.upper()}: {message.text}")
        if message.metadata:
            print(f"{prefix}   (Type: {message.message_type}, Metadata: {message.metadata})")
        print()
    
    async def demo_dog_agent(self):
        """Demonstrate DogAgent capabilities"""
        print("=" * 60)
        print("🐕 DOG AGENT DEMO")
        print("=" * 60)
        print()
        
        # 1. Greeting
        print("1. GREETING")
        print("-" * 40)
        
        context = AgentContext(
            session_id=self.session_id,
            message_type=MessageType.GREETING
        )
        
        messages = await self.dog_agent.respond(context)
        for msg in messages:
            self.print_message(msg, "   ")
        
        # 2. Dog Perspective
        print("2. DOG PERSPECTIVE RESPONSE")
        print("-" * 40)
        print("   👤 User: Mein Hund bellt immer wenn es an der Tür klingelt")
        print()
        
        context = AgentContext(
            session_id=self.session_id,
            user_input="Mein Hund bellt immer wenn es an der Tür klingelt",
            message_type=MessageType.RESPONSE,
            metadata={
                'response_mode': 'perspective_only',
                'match_data': 'Hund bellt bei Türklingel als Warnung'
            }
        )
        
        messages = await self.dog_agent.respond(context)
        for msg in messages:
            self.print_message(msg, "   ")
        
        # 3. Diagnosis
        print("3. INSTINCT DIAGNOSIS")
        print("-" * 40)
        print("   👤 User provides context: Besonders bei Fremden")
        print()
        
        context = AgentContext(
            session_id=self.session_id,
            message_type=MessageType.RESPONSE,
            metadata={
                'response_mode': 'diagnosis',
                'analysis_data': {
                    'primary_instinct': 'territorial',
                    'primary_description': 'Der Hund zeigt territoriales Verhalten zum Schutz des Reviers'
                }
            }
        )
        
        messages = await self.dog_agent.respond(context)
        for msg in messages:
            self.print_message(msg, "   ")
        
        # 4. Exercise
        print("4. EXERCISE RECOMMENDATION")
        print("-" * 40)
        
        context = AgentContext(
            session_id=self.session_id,
            message_type=MessageType.RESPONSE,
            metadata={
                'response_mode': 'exercise',
                'exercise_data': 'Übe mit deinem Hund das "Ruhig"-Kommando. Wenn es klingelt, lass ihn einmal bellen, dann sage "Ruhig" und belohne ihn, wenn er aufhört.'
            }
        )
        
        messages = await self.dog_agent.respond(context)
        for msg in messages:
            self.print_message(msg, "   ")
        
        # 5. Questions
        print("5. VARIOUS QUESTIONS")
        print("-" * 40)
        
        question_types = ['confirmation', 'context', 'exercise', 'restart']
        
        for q_type in question_types:
            context = AgentContext(
                session_id=self.session_id,
                message_type=MessageType.QUESTION,
                metadata={'question_type': q_type}
            )
            
            messages = await self.dog_agent.respond(context)
            print(f"   Question Type: {q_type}")
            for msg in messages:
                self.print_message(msg, "   ")
    
    async def demo_companion_agent(self):
        """Demonstrate CompanionAgent capabilities"""
        print("\n" + "=" * 60)
        print("🤝 COMPANION AGENT DEMO")
        print("=" * 60)
        print()
        
        # 1. Feedback Introduction
        print("1. FEEDBACK INTRODUCTION")
        print("-" * 40)
        
        context = AgentContext(
            session_id=self.session_id,
            message_type=MessageType.GREETING
        )
        
        messages = await self.companion_agent.respond(context)
        for msg in messages:
            self.print_message(msg, "   ")
        
        # 2. Feedback Questions
        print("2. FEEDBACK QUESTIONS (1-5)")
        print("-" * 40)
        
        for i in range(1, 6):
            context = AgentContext(
                session_id=self.session_id,
                message_type=MessageType.QUESTION,
                metadata={'question_number': i}
            )
            
            messages = await self.companion_agent.respond(context)
            print(f"   Question {i}:")
            for msg in messages:
                self.print_message(msg, "   ")
            
            # Simulate user answer
            print(f"   👤 User: Beispielantwort {i}")
            
            # Acknowledgment
            ack_context = AgentContext(
                session_id=self.session_id,
                user_input=f"Beispielantwort {i}",
                message_type=MessageType.RESPONSE,
                metadata={'response_mode': 'acknowledgment'}
            )
            
            ack_messages = await self.companion_agent.respond(ack_context)
            for msg in ack_messages:
                self.print_message(msg, "   ")
        
        # 3. Completion
        print("3. FEEDBACK COMPLETION")
        print("-" * 40)
        
        context = AgentContext(
            session_id=self.session_id,
            message_type=MessageType.RESPONSE,
            metadata={
                'response_mode': 'completion',
                'save_success': True
            }
        )
        
        messages = await self.companion_agent.respond(context)
        for msg in messages:
            self.print_message(msg, "   ")
    
    async def demo_error_handling(self):
        """Demonstrate error handling"""
        print("\n" + "=" * 60)
        print("⚠️  ERROR HANDLING DEMO")
        print("=" * 60)
        print()
        
        # 1. Invalid context
        print("1. INVALID CONTEXT")
        print("-" * 40)
        
        messages = await self.dog_agent.respond("not a valid context")
        for msg in messages:
            self.print_message(msg, "   ")
        
        # 2. Missing metadata
        print("2. MISSING REQUIRED METADATA")
        print("-" * 40)
        
        context = AgentContext(
            session_id=self.session_id,
            message_type=MessageType.RESPONSE
            # Missing response_mode
        )
        
        messages = await self.dog_agent.respond(context)
        for msg in messages:
            self.print_message(msg, "   ")
        
        # 3. Service failure
        print("3. SERVICE FAILURE")
        print("-" * 40)
        
        # Make GPT fail
        original_side_effect = self.mock_gpt.complete.side_effect
        self.mock_gpt.complete.side_effect = Exception("Service unavailable")
        
        context = AgentContext(
            session_id=self.session_id,
            message_type=MessageType.RESPONSE,
            metadata={
                'response_mode': 'perspective_only',
                'match_data': 'test'
            }
        )
        
        messages = await self.dog_agent.respond(context)
        for msg in messages:
            self.print_message(msg, "   ")
        
        # Restore mock
        self.mock_gpt.complete.side_effect = original_side_effect
    
    async def run(self):
        """Run all demos"""
        print("\n🎭 V2 AGENTS DEMONSTRATION")
        print("=" * 60)
        print("This demo shows the capabilities of the V2 agent system")
        print("=" * 60)
        
        await self.demo_dog_agent()
        await self.demo_companion_agent()
        await self.demo_error_handling()
        
        print("\n✅ DEMO COMPLETED!")
        print("=" * 60)
        print("\nKey Features Demonstrated:")
        print("- Clean message formatting")
        print("- Proper error handling")
        print("- Flexible response modes")
        print("- Centralized prompt management")
        print("- Type-safe message structures")


async def main():
    """Main entry point"""
    demo = AgentDemo()
    await demo.run()


if __name__ == "__main__":
    print("Starting V2 Agents Demo...")
    asyncio.run(main())