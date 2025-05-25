# src/v2/agents/demo_companion_agent.py
"""
Demo script for V2 CompanionAgent showing feedback collection flow.

This demonstrates how the flow engine will interact with the CompanionAgent
to collect user feedback through a structured 5-question sequence.

Run with: python -m src.v2.agents.demo_companion_agent
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.v2.agents.companion_agent import CompanionAgent
from src.v2.agents.base_agent import AgentContext, MessageType
from src.v2.core.prompt_manager import PromptManager
from src.v2.services.redis_service import RedisService


class CompanionAgentDemo:
    """Demo class showing CompanionAgent feedback collection scenarios"""
    
    def __init__(self):
        """Initialize demo with real or mocked services"""
        print("🤝 CompanionAgent Demo - Feedback Collection Flow")
        print("=" * 60)
        
        # For demo, we'll use mocked services to avoid API calls
        self.use_real_services = False
        
        if self.use_real_services:
            # Real services (requires Redis connection)
            self.prompt_manager = PromptManager()
            self.redis_service = RedisService()
        else:
            # Mocked services for demo
            self.prompt_manager = self._create_mock_prompt_manager()
            self.redis_service = self._create_mock_redis_service()
        
        # Create agent with services
        self.companion_agent = CompanionAgent(
            prompt_manager=self.prompt_manager,
            redis_service=self.redis_service
        )
    
    def _create_mock_prompt_manager(self):
        """Create mock prompt manager with demo responses"""
        class MockPromptManager:
            def get_prompt(self, prompt_type, **kwargs):
                prompts = {
                    'companion_feedback_intro': "Ich würde mich freuen, wenn du mir noch ein kurzes Feedback gibst.",
                    'companion_feedback_q1': "Hast Du das Gefühl, dass Dir die Beratung bei Deinem Anliegen weitergeholfen hat?",
                    'companion_feedback_q2': "Wie fandest Du die Sichtweise des Hundes – was hat Dir daran gefallen oder vielleicht irritiert?",
                    'companion_feedback_q3': "Was denkst Du über die vorgeschlagene Übung – passt sie zu Deiner Situation?",
                    'companion_feedback_q4': "Auf einer Skala von 0-10: Wie wahrscheinlich ist es, dass Du Wuffchat weiterempfiehlst?",
                    'companion_feedback_q5': "Optional: Deine E-Mail oder Telefonnummer für eventuelle Rückfragen. Diese wird ausschließlich für Rückfragen zu deinem Feedback verwendet und nach 3 Monaten automatisch gelöscht.",
                    'companion_feedback_ack': "Danke für deine Antwort.",
                    'companion_feedback_complete': "Danke für Dein Feedback! 🐾",
                    'companion_feedback_complete_nosave': "Danke für dein Feedback! Es konnte leider nicht gespeichert werden, aber deine Antworten sind trotzdem wertvoll.",
                    'companion_proceed_confirmation': "Möchtest du mit dem Feedback fortfahren?",
                    'companion_skip_confirmation': "Möchtest du diese Frage überspringen?",
                    'companion_invalid_feedback_error': "Bitte gib eine gültige Antwort. Du kannst auch 'überspringen' sagen.",
                    'companion_save_error': "Es gab ein Problem beim Speichern des Feedbacks. Bitte versuche es erneut.",
                    'companion_general_error': "Es tut mir leid, es gab ein Problem. Bitte versuche es erneut."
                }
                
                # Convert prompt_type to string key
                key = str(prompt_type).lower().replace('prompttype.', '').replace('_', '_')
                return prompts.get(key, f"Mock prompt for {prompt_type}")
        
        return MockPromptManager()
    
    def _create_mock_redis_service(self):
        """Create mock Redis service with demo responses"""
        class MockRedisService:
            async def health_check(self):
                return {"healthy": True}
            
            async def set(self, key, value, expire=None):
                return True
            
            async def get(self, key):
                return None
        
        return MockRedisService()
    
    async def run_all_demos(self):
        """Run all demo scenarios"""
        print(f"\n🔧 Agent Configuration:")
        print(f"   Name: {self.companion_agent.name}")
        print(f"   Role: {self.companion_agent.role}")
        print(f"   Supported Message Types: {[t.value for t in self.companion_agent.get_supported_message_types()]}")
        print(f"   Feedback Questions: {self.companion_agent.get_feedback_question_count()}")
        
        # Run individual demos
        await self.demo_feedback_introduction()
        await self.demo_feedback_questions()
        await self.demo_response_modes()
        await self.demo_confirmations()
        await self.demo_error_handling()
        await self.demo_complete_feedback_flow()
        await self.demo_feedback_sequence_utility()
        await self.demo_health_check()
        
        print(f"\n✅ Demo completed! All feedback scenarios demonstrated.")
    
    async def demo_feedback_introduction(self):
        """Demo feedback introduction message"""
        print(f"\n👋 DEMO: Feedback Introduction")
        print("-" * 40)
        
        context = AgentContext(
            session_id="demo-session",
            message_type=MessageType.GREETING
        )
        
        messages = await self.companion_agent.respond(context)
        
        for message in messages:
            print(f"🤝: {message.text}")
    
    async def demo_feedback_questions(self):
        """Demo all 5 feedback questions"""
        print(f"\n❓ DEMO: Feedback Questions (1-5)")
        print("-" * 40)
        
        for question_num in range(1, 6):
            print(f"\nFrage {question_num}:")
            
            context = AgentContext(
                session_id="demo-session",
                message_type=MessageType.QUESTION,
                metadata={'question_number': question_num}
            )
            
            messages = await self.companion_agent.respond(context)
            
            for message in messages:
                print(f"   🤝: {message.text}")
    
    async def demo_response_modes(self):
        """Demo different response modes"""
        print(f"\n💬 DEMO: Response Modes")
        print("-" * 40)
        
        # 1. Acknowledgment Response
        print(f"\n1. Acknowledgment Response:")
        context = AgentContext(
            session_id="demo-session",
            message_type=MessageType.RESPONSE,
            metadata={'response_mode': 'acknowledgment'}
        )
        
        messages = await self.companion_agent.respond(context)
        for msg in messages:
            print(f"   🤝: {msg.text}")
        
        # 2. Completion Response (Success)
        print(f"\n2. Completion Response (Feedback Saved):")
        context.metadata = {
            'response_mode': 'completion',
            'save_success': True
        }
        
        messages = await self.companion_agent.respond(context)
        for msg in messages:
            print(f"   🤝: {msg.text}")
        
        # 3. Completion Response (Save Failed)
        print(f"\n3. Completion Response (Save Failed):")
        context.metadata = {
            'response_mode': 'completion',
            'save_success': False
        }
        
        messages = await self.companion_agent.respond(context)
        for msg in messages:
            print(f"   🤝: {msg.text}")
        
        # 4. Progress Response (currently empty)
        print(f"\n4. Progress Response:")
        context.metadata = {'response_mode': 'progress'}
        
        messages = await self.companion_agent.respond(context)
        if messages:
            for msg in messages:
                print(f"   🤝: {msg.text}")
        else:
            print(f"   (No progress messages - feature could be enhanced)")
    
    async def demo_confirmations(self):
        """Demo confirmation messages"""
        print(f"\n✅ DEMO: Confirmation Messages")
        print("-" * 40)
        
        confirmation_types = [
            ('proceed', "Proceed Confirmation"),
            ('skip', "Skip Confirmation")
        ]
        
        for confirmation_type, description in confirmation_types:
            print(f"\n{description}:")
            
            context = AgentContext(
                session_id="demo-session",
                message_type=MessageType.CONFIRMATION,
                metadata={'confirmation_type': confirmation_type}
            )
            
            messages = await self.companion_agent.respond(context)
            for msg in messages:
                print(f"   🤝: {msg.text}")
    
    async def demo_error_handling(self):
        """Demo error message handling"""
        print(f"\n❌ DEMO: Error Handling")
        print("-" * 40)
        
        error_types = [
            ('invalid_feedback', "Invalid Feedback Error"),
            ('save_failed', "Save Failed Error"),
            ('general', "General Error")
        ]
        
        for error_type, description in error_types:
            print(f"\n{description}:")
            
            context = AgentContext(
                session_id="demo-session",
                message_type=MessageType.ERROR,
                metadata={'error_type': error_type}
            )
            
            messages = await self.companion_agent.respond(context)
            for msg in messages:
                print(f"   🤝: {msg.text}")
    
    async def demo_complete_feedback_flow(self):
        """Demo complete feedback collection flow"""
        print(f"\n🔄 DEMO: Complete Feedback Flow Simulation")
        print("-" * 40)
        
        session_id = "complete-flow-demo"
        
        # Simulate user responses
        user_responses = [
            "Ja, sehr hilfreich!",
            "Die Hundeperspektive war sehr interessant und neu für mich.",
            "Die Übung passt perfekt zu meiner Situation mit Luna.",
            "9 - würde es definitiv weiterempfehlen!",
            "max.mustermann@email.de"
        ]
        
        print(f"Simuliere kompletten Feedback-Flow mit Benutzer-Antworten:")
        for i, response in enumerate(user_responses, 1):
            print(f"   Benutzer-Antwort {i}: '{response}'")
        
        print(f"\n--- Feedback Flow Start ---")
        
        # 1. Introduction
        intro_context = AgentContext(
            session_id=session_id,
            message_type=MessageType.GREETING
        )
        
        intro_messages = await self.companion_agent.respond(intro_context)
        print(f"\n📢 Einführung:")
        for msg in intro_messages:
            print(f"   🤝: {msg.text}")
        
        # 2. Go through all questions with simulated responses
        for question_num, user_answer in enumerate(user_responses, 1):
            # Ask question
            question_context = AgentContext(
                session_id=session_id,
                message_type=MessageType.QUESTION,
                metadata={'question_number': question_num}
            )
            
            question_messages = await self.companion_agent.respond(question_context)
            print(f"\n❓ Frage {question_num}:")
            for msg in question_messages:
                print(f"   🤝: {msg.text}")
            
            # Simulate user response
            print(f"   👤: {user_answer}")
            
            # Acknowledgment (except for last question)
            if question_num < 5:
                ack_context = AgentContext(
                    session_id=session_id,
                    message_type=MessageType.RESPONSE,
                    metadata={'response_mode': 'acknowledgment'}
                )
                
                ack_messages = await self.companion_agent.respond(ack_context)
                for msg in ack_messages:
                    print(f"   🤝: {msg.text}")
        
        # 3. Final completion
        completion_context = AgentContext(
            session_id=session_id,
            message_type=MessageType.RESPONSE,
            metadata={
                'response_mode': 'completion',
                'save_success': True
            }
        )
        
        completion_messages = await self.companion_agent.respond(completion_context)
        print(f"\n🏁 Abschluss:")
        for msg in completion_messages:
            print(f"   🤝: {msg.text}")
        
        print(f"\n--- Feedback Flow Ende ---")
    
    async def demo_feedback_sequence_utility(self):
        """Demo the feedback sequence utility method"""
        print(f"\n🛠️  DEMO: Feedback Sequence Utility")
        print("-" * 40)
        
        session_id = "utility-demo"
        contexts = await self.companion_agent.create_feedback_sequence(session_id)
        
        print(f"Generated {len(contexts)} contexts for complete feedback sequence:")
        
        for i, context in enumerate(contexts, 1):
            step_info = context.metadata.get('sequence_step', 'unknown')
            print(f"\n{i}. {step_info.title()}:")
            print(f"   Message Type: {context.message_type.value}")
            print(f"   Session ID: {context.session_id}")
            print(f"   Metadata: {context.metadata}")
            
            # Show what this context would generate
            try:
                messages = await self.companion_agent.respond(context)
                if messages:
                    print(f"   Generated Message: '{messages[0].text[:60]}...'")
            except Exception as e:
                print(f"   (Would generate message - skipped due to: {str(e)[:40]}...)")
    
    async def demo_health_check(self):
        """Demo health check functionality"""
        print(f"\n🏥 DEMO: Health Check")
        print("-" * 40)
        
        health = await self.companion_agent.health_check()
        
        print(f"Agent Health Status:")
        print(f"   Agent: {health['agent']}")
        print(f"   Overall Healthy: {health['healthy']}")
        print(f"   Services:")
        for service, status in health['services'].items():
            print(f"      {service}: {status}")
    
    def demo_validation_examples(self):
        """Demo context validation examples"""
        print(f"\n⚠️  DEMO: Context Validation")
        print("-" * 40)
        
        # Test cases for validation
        test_cases = [
            {
                'name': 'Valid Question Context',
                'context': AgentContext(
                    session_id="demo",
                    message_type=MessageType.QUESTION,
                    metadata={'question_number': 3}
                ),
                'should_pass': True
            },
            {
                'name': 'Invalid Question Number',
                'context': AgentContext(
                    session_id="demo",
                    message_type=MessageType.QUESTION,
                    metadata={'question_number': 7}
                ),
                'should_pass': False
            },
            {
                'name': 'Missing Question Number',
                'context': AgentContext(
                    session_id="demo",
                    message_type=MessageType.QUESTION,
                    metadata={}
                ),
                'should_pass': False
            },
            {
                'name': 'Valid Response Context',
                'context': AgentContext(
                    session_id="demo",
                    message_type=MessageType.RESPONSE,
                    metadata={'response_mode': 'completion'}
                ),
                'should_pass': True
            },
            {
                'name': 'Missing Response Mode',
                'context': AgentContext(
                    session_id="demo",
                    message_type=MessageType.RESPONSE,
                    metadata={}
                ),
                'should_pass': False
            }
        ]
        
        for test_case in test_cases:
            print(f"\nTesting: {test_case['name']}")
            try:
                self.companion_agent.validate_context(test_case['context'])
                if test_case['should_pass']:
                    print(f"   ✅ Validation passed as expected")
                else:
                    print(f"   ❌ Expected validation to fail, but it passed")
            except Exception as e:
                if not test_case['should_pass']:
                    print(f"   ✅ Validation correctly failed: {str(e)}")
                else:
                    print(f"   ❌ Unexpected validation failure: {str(e)}")
    
    def demo_question_utilities(self):
        """Demo question-related utility methods"""
        print(f"\n🔢 DEMO: Question Utilities")
        print("-" * 40)
        
        agent = self.companion_agent
        
        print(f"Total Feedback Questions: {agent.get_feedback_question_count()}")
        
        print(f"\nQuestion Number Validation:")
        test_numbers = [-1, 0, 1, 3, 5, 6, 10, "3", None]
        for num in test_numbers:
            is_valid = agent.validate_question_number(num)
            status = "✅ Valid" if is_valid else "❌ Invalid"
            print(f"   {num}: {status}")


async def main():
    """Run the complete demo"""
    demo = CompanionAgentDemo()
    
    try:
        await demo.run_all_demos()
        demo.demo_validation_examples()
        demo.demo_question_utilities()
        
    except KeyboardInterrupt:
        print(f"\n\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Starting CompanionAgent Demo...")
    asyncio.run(main()) 