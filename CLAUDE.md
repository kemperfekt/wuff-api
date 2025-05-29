# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Running the Application
```bash
# V2 (recommended - clean architecture)
python -m uvicorn src.v2.main:app --port 8000

# V1 (legacy - currently in production)
python -m uvicorn src.main:app --port 8000
```

### Testing
```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/v2/agents/test_dog_agent.py

# Run with verbose output
pytest -v

# Run tests matching pattern
pytest -k "test_flow"
```

### Environment Setup
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Required Environment Variables
```bash
OPENAI_APIKEY=sk-...          # OpenAI API key
WEAVIATE_URL=https://...       # Weaviate Cloud URL
WEAVIATE_API_KEY=...           # Weaviate API key
REDIS_URL=redis://...          # Optional: Redis for feedback
LOG_LEVEL=INFO                 # Optional: Logging level
```

## High-Level Architecture

### V2 Architecture (Clean FSM-based)
The V2 architecture uses a state machine (FSM) to manage conversation flow:

1. **FlowEngine**: Core FSM with 11 states and 12 events
   - States: GREETING, WAIT_FOR_SYMPTOM, WAIT_FOR_CONFIRMATION, etc.
   - Events: USER_INPUT, YES_RESPONSE, NO_RESPONSE, etc.
   - Handles transitions via FlowHandlers

2. **V2Orchestrator**: Main coordinator
   - Manages flow engine, services, and agents
   - Provides backward compatibility with V1 API
   - Handles session management

3. **Agents**: Message formatting only (no business logic)
   - `DogAgent`: Generates responses from dog's perspective
   - `CompanionAgent`: Handles feedback collection
   - All agents inherit from BaseAgent with dependency injection

4. **Services**: External integrations
   - `GPTService`: OpenAI GPT-4 integration
   - `WeaviateService`: Vector database for symptom/instinct matching
   - `RedisService`: Optional feedback storage
   - All services follow initialize() and health_check() patterns

5. **PromptManager**: Centralized prompt management
   - Categories: DOG, COMPANION, QUERY, VALIDATION
   - Variable substitution with validation
   - Loaded from src/v2/prompts/ modules

### Key Architectural Decisions
- **Separation of Concerns**: Flow logic (FlowEngine), business logic (Handlers), external calls (Services), message formatting (Agents)
- **Async-First**: All components use async/await
- **Dependency Injection**: Services injected into agents for testability
- **Backward Compatibility**: V2 maintains same API surface as V1
- **Graceful Degradation**: Optional services (Redis) fail gracefully

### Conversation Flow
1. User starts with `/flow_intro` → GREETING state
2. User describes behavior → searches Weaviate for symptoms
3. System confirms understanding → asks for context
4. System provides diagnosis from dog's perspective
5. System offers training exercise
6. Optional feedback collection (5 questions)

### Testing Strategy
- Unit tests for each component
- Integration tests for flow transitions
- Postman collection for API testing (tests/postman/)
- Mock services available for testing without external dependencies