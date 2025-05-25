# src/v2/agents/demo_dog_agent.py
"""
Demo script for V2 DogAgent showing all message types and response modes.

This demonstrates how the flow engine will interact with the DogAgent
to generate different types of messages based on context.

Run with: python -m src.v2.agents.demo_dog_agent
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.v2.agents.dog_agent import DogAgent
from src.v2.agents.base_agent import AgentContext, MessageType
from src.v2.core.prompt_manager import PromptManager
from src.v2.services.gpt_service import GPTService


class DogAgentDemo:
    """Demo class showing DogAgent usage scenarios"""
    
    def __init__(self):
        """Initialize demo with real or mocked services"""
        print("🐕 DogAgent Demo - Message Types and Response Modes")
        print("=" * 60)
        
        # For demo, we'll use mocked services to avoid API calls
        self.use_real_services = False
        
        if self.use_real_services:
            # Real services (requires API keys)
            self.prompt_manager = PromptManager()
            self.gpt_service = GPTService()
        else:
            # Mocked services for demo
            self.prompt_manager = self._create_mock_prompt_manager()
            self.gpt_service = self._create_mock_gpt_service()
        
        # Create agent with services
        self.dog_agent = DogAgent(
            prompt_manager=self.prompt_manager,
            gpt_service=self.gpt_service
        )
    
    def _create_mock_prompt_manager(self):
        """Create mock prompt manager with demo responses"""
        class MockPromptManager:
            def get_prompt(self, prompt_type, **kwargs):
                prompts = {
                    'dog_greeting': "Wuff! Schön, dass Du da bist. Ich erkläre Dir Hundeverhalten aus meiner Sicht.",
                    'dog_greeting_followup': "Was ist los? Beschreib mir bitte, was du beobachtet hast.",
                    'dog_confirmation_question': "Magst Du mehr erfahren, warum ich mich so verhalte?",
                    'dog_context_question': "Gut, dann brauche ich ein bisschen mehr Informationen. Wo war das genau?",
                    'dog_exercise_question': "Möchtest du eine Lernaufgabe, die dir helfen kann?",
                    'dog_restart_question': "Möchtest du ein weiteres Hundeverhalten verstehen?",
                    'dog_no_match_error': "Hmm, zu diesem Verhalten habe ich leider noch keine Antwort.",
                    'dog_invalid_input_error': "Kannst Du das Verhalten bitte etwas ausführlicher beschreiben?",
                    'dog_technical_error': "Wuff! Entschuldige, ich bin gerade etwas verwirrt. Kannst du es nochmal versuchen?",
                    'dog_describe_more': "Kannst du mir mehr erzählen?",
                    'dog_be_specific': "Kannst Du das bitte genauer beschreiben?",
                    'dog_another_behavior_question': "Gibt es ein weiteres Verhalten, das Du mit mir besprechen möchtest?",
                    'dog_fallback_exercise': "Eine hilfreiche Übung wäre, mit deinem Hund klare Grenzen zu setzen."
                }
                
                # Convert prompt_type to string key
                key = str(prompt_type).lower().replace('prompttype.', '').replace('_', '_')
                return prompts.get(key, f"Mock prompt for {prompt_type}")
        
        return MockPromptManager()
    
    def _create_mock_gpt_service(self):
        """Create mock GPT service with demo responses"""
        class MockGPTService:
            async def complete(self, prompt, **kwargs):
                if "Jagd" in prompt or "jagd" in prompt:
                    return "Als Hund spüre ich einen starken Drang, Dinge zu verfolgen und zu fangen. In dieser Situation will ich etwas jagen!"
                elif "territorial" in prompt or "Territorial" in prompt:
                    return "Als Hund fühle ich mich verantwortlich für mein Gebiet. Ich muss es beschützen - das ist mein Job!"
                elif "Rudel" in prompt or "rudel" in prompt:
                    return "Als Hund denke ich an meine Familie, mein Rudel. Ich will meinen Platz finden und dazugehören."
                elif "Sexual" in prompt or "sexual" in prompt:
                    return "Als Hund folge ich meinen natürlichen Instinkten. Diese Gefühle sind normal für mich."
                else:
                    return "Als Hund erlebe ich verschiedene Gefühle in dieser Situation. Manchmal ist es schwer zu erklären, aber es fühlt sich wichtig an."
            
            async def health_check(self):
                return {"healthy": True}
        
        return MockGPTService()
    
    async def run_all_demos(self):
        """Run all demo scenarios"""
        print(f"\n🔧 Agent Configuration:")
        print(f"   Name: {self.dog_agent.name}")
        print(f"   Role: {self.dog_agent.role}")
        print(f"   Supported Message Types: {[t.value for t in self.dog_agent.get_supported_message_types()]}")
        
        # Run individual demos
        await self.demo_greeting_messages()
        await self.demo_response_modes()
        await self.demo_questions()
        await self.demo_errors()
        await self.demo_instructions()
        await self.demo_health_check()
        
        print(f"\n✅ Demo completed! All message types demonstrated.")
    
    async def demo_greeting_messages(self):
        """Demo greeting message generation"""
        print(f"\n📢 DEMO: Greeting Messages")
        print("-" * 40)
        
        context = AgentContext(
            session_id="demo-session",
            message_type=MessageType.GREETING
        )
        
        messages = await self.dog_agent.respond(context)
        
        for i, message in enumerate(messages, 1):
            print(f"Message {i}: {message.text}")
    
    async def demo_response_modes(self):
        """Demo different response modes"""
        print(f"\n🐕 DEMO: Response Modes")
        print("-" * 40)
        
        # Sample analysis data
        analysis_data = {
            'primary_instinct': 'territorial',
            'primary_description': 'Der Hund zeigt territoriales Verhalten zum Schutz seines Reviers',
            'all_instincts': {
                'jagd': 'Jagdinstinkt - will Dinge verfolgen',
                'rudel': 'Rudelinstinkt - soziales Verhalten',
                'territorial': 'Territorialinstinkt - Gebiet schützen', 
                'sexual': 'Sexualinstinkt - Fortpflanzungsverhalten'
            }
        }
        
        # 1. Perspective Only
        print(f"\n1. Perspective Only Response:")
        context = AgentContext(
            session_id="demo-session",
            user_input="Mein Hund bellt wenn Besucher kommen",
            message_type=MessageType.RESPONSE,
            metadata={
                'response_mode': 'perspective_only',
                'analysis_data': analysis_data
            }
        )
        
        messages = await self.dog_agent.respond(context)
        for msg in messages:
            print(f"   🐕: {msg.text}")
        
        # 2. Diagnosis Response
        print(f"\n2. Diagnosis Response:")
        context.metadata = {
            'response_mode': 'diagnosis',
            'analysis_data': analysis_data
        }
        
        messages = await self.dog_agent.respond(context)
        for msg in messages:
            print(f"   🐕: {msg.text}")
        
        # 3. Exercise Response
        print(f"\n3. Exercise Response:")
        context.metadata = {
            'response_mode': 'exercise',
            'exercise_data': 'Übe mit deinem Hund Impulskontrolle, indem du ihn bei Besuch zuerst ins Platz schickst und erst nach Ruhe belohnst.'
        }
        
        messages = await self.dog_agent.respond(context)
        for msg in messages:
            print(f"   🐕: {msg.text}")
        
        # 4. Full Response
        print(f"\n4. Full Response (Perspective + Exercise + Follow-up):")
        context.metadata = {
            'response_mode': 'full_response',
            'analysis_data': analysis_data,
            'exercise_data': 'Übe Grenzen setzen beim Besuch - erst Ruhe, dann Begrüßung.'
        }
        
        messages = await self.dog_agent.respond(context)
        for i, msg in enumerate(messages, 1):
            print(f"   🐕 ({i}): {msg.text}")
    
    async def demo_questions(self):
        """Demo question message generation"""
        print(f"\n❓ DEMO: Question Messages")
        print("-" * 40)
        
        question_types = [
            ('confirmation', "Confirmation Question"),
            ('context', "Context Question"),
            ('exercise', "Exercise Question"),
            ('restart', "Restart Question")
        ]
        
        for question_type, description in question_types:
            print(f"\n{description}:")
            
            context = AgentContext(
                session_id="demo-session",
                message_type=MessageType.QUESTION,
                metadata={'question_type': question_type}
            )
            
            messages = await self.dog_agent.respond(context)
            for msg in messages:
                print(f"   🐕: {msg.text}")
    
    async def demo_errors(self):
        """Demo error message generation"""
        print(f"\n❌ DEMO: Error Messages")
        print("-" * 40)
        
        error_types = [
            ('no_match', "No Match Found"),
            ('invalid_input', "Invalid Input"),
            ('technical', "Technical Error")
        ]
        
        for error_type, description in error_types:
            print(f"\n{description}:")
            
            context = AgentContext(
                session_id="demo-session",
                message_type=MessageType.ERROR,
                metadata={'error_type': error_type}
            )
            
            messages = await self.dog_agent.respond(context)
            for msg in messages:
                print(f"   🐕: {msg.text}")
    
    async def demo_instructions(self):
        """Demo instruction message generation"""
        print(f"\n📋 DEMO: Instruction Messages")
        print("-" * 40)
        
        instruction_types = [
            ('describe_more', "Ask for More Description"),
            ('be_specific', "Ask to Be More Specific")
        ]
        
        for instruction_type, description in instruction_types:
            print(f"\n{description}:")
            
            context = AgentContext(
                session_id="demo-session",
                message_type=MessageType.INSTRUCTION,
                metadata={'instruction_type': instruction_type}
            )
            
            messages = await self.dog_agent.respond(context)
            for msg in messages:
                print(f"   🐕: {msg.text}")
    
    async def demo_health_check(self):
        """Demo health check functionality"""
        print(f"\n🏥 DEMO: Health Check")
        print("-" * 40)
        
        health = await self.dog_agent.health_check()
        
        print(f"Agent Health Status:")
        print(f"   Agent: {health['agent']}")
        print(f"   Overall Healthy: {health['healthy']}")
        print(f"   Services:")
        for service, status in health['services'].items():
            print(f"      {service}: {status}")
    
    async def demo_validation_errors(self):
        """Demo context validation errors"""
        print(f"\n⚠️  DEMO: Validation Errors")
        print("-" * 40)
        
        # Test cases that should fail validation
        test_cases = [
            {
                'name': 'Missing response_mode',
                'context': AgentContext(
                    session_id="demo",
                    message_type=MessageType.RESPONSE,
                    metadata={}
                )
            },
            {
                'name': 'Missing analysis_data for diagnosis',
                'context': AgentContext(
                    session_id="demo", 
                    message_type=MessageType.RESPONSE,
                    metadata={'response_mode': 'diagnosis'}
                )
            }
        ]
        
        for test_case in test_cases:
            print(f"\nTesting: {test_case['name']}")
            try:
                self.dog_agent.validate_context(test_case['context'])
                print(f"   ❌ Expected validation error, but none occurred")
            except Exception as e:
                print(f"   ✅ Validation correctly failed: {str(e)}")
    
    def demo_context_examples(self):
        """Show examples of different context configurations"""
        print(f"\n📝 DEMO: Context Examples")
        print("-" * 40)
        
        examples = [
            {
                'name': 'Greeting Context',
                'context': AgentContext(
                    session_id="demo-123",
                    message_type=MessageType.GREETING
                )
            },
            {
                'name': 'Dog Perspective Context',
                'context': AgentContext(
                    session_id="demo-123",
                    user_input="Mein Hund springt Besucher an",
                    message_type=MessageType.RESPONSE,
                    metadata={
                        'response_mode': 'perspective_only',
                        'analysis_data': {
                            'primary_instinct': 'rudel',
                            'all_instincts': {'rudel': 'Pack behavior'}
                        }
                    }
                )
            },
            {
                'name': 'Error Context',
                'context': AgentContext(
                    session_id="demo-123",
                    message_type=MessageType.ERROR,
                    metadata={'error_type': 'no_match'}
                )
            }
        ]
        
        for example in examples:
            print(f"\n{example['name']}:")
            context = example['context']
            print(f"   Session ID: {context.session_id}")
            print(f"   Message Type: {context.message_type.value}")
            print(f"   User Input: {context.user_input}")
            print(f"   Metadata: {context.metadata}")


async def main():
    """Run the complete demo"""
    demo = DogAgentDemo()
    
    try:
        await demo.run_all_demos()
        await demo.demo_validation_errors()
        demo.demo_context_examples()
        
    except KeyboardInterrupt:
        print(f"\n\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Starting DogAgent Demo...")
    asyncio.run(main())