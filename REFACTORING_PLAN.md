# WuffChat V2 Refactoring Plan

## Project Overview
- **Start Date**: [INSERT DATE]
- **Current Branch**: refactor/v2-architecture
- **Last Updated**: [INSERT DATE]
- **Last Completed Step**: [INSERT STEP]

## Context for New Chat Sessions
```
I'm refactoring a FastAPI dog behavior consultation chatbot. 
Current issues: No real FSM, mixed concerns, scattered prompts.
Solution: Building v2 in parallel using hybrid approach.
All details in this document. Continue from "Current Status".
```

## Architecture Problems Identified
- [ ] FSM defined but not used (state_machine.py is orphaned)
- [ ] Flow logic hardcoded in flow_orchestrator.py (500+ lines)
- [ ] Prompts scattered across 5+ files
- [ ] Mixed async/sync patterns
- [ ] Inconsistent service patterns (singleton vs static vs instance)
- [ ] Agents doing too much (business logic + formatting)

## Target Architecture

### Layer Separation
```
┌─────────────────────┐
│     main.py         │ ← API routes only
├─────────────────────┤
│  v2/flow_engine.py  │ ← FSM-based flow control
├─────────────────────┤
│    v2/agents/       │ ← Message formatting only
├─────────────────────┤
│   v2/services/      │ ← Business logic, external APIs
├─────────────────────┤
│   v2/prompts/       │ ← All content templates
└─────────────────────┘
```

### New Folder Structure
```
src/
├── [existing files remain untouched]
├── v2/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── flow_engine.py      # FSM implementation
│   │   ├── prompt_manager.py   # Centralized prompt access
│   │   ├── service_base.py     # Base service class
│   │   └── exceptions.py       # V2 exceptions
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py       # Agent interface
│   │   ├── dog_agent.py        # Message formatting only
│   │   └── companion_agent.py  # Message formatting only
│   ├── services/
│   │   ├── __init__.py
│   │   ├── gpt_service.py      # Async-only GPT calls
│   │   ├── weaviate_service.py # Standardized Weaviate
│   │   └── redis_service.py    # Consistent Redis pattern
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── prompt_manager.py   # PromptManager class
│   │   ├── dog_prompts.py      # All dog agent prompts
│   │   ├── companion_prompts.py # All companion prompts
│   │   ├── query_prompts.py    # Weaviate/RAG queries
│   │   ├── validation_prompts.py # Input validation
│   │   └── common_prompts.py   # Shared prompts
│   └── models/
│       ├── __init__.py
│       └── flow_models.py      # V2 models if needed
```

## Implementation Phases

### Phase 1: Core Infrastructure
- [☑️] Create v2 folder structure
- [☑️] Implement base classes:
  - [☑️] `v2/core/flow_engine.py` - FSM implementation
  - [☑️] `v2/core/prompt_manager.py` - Prompt management
  - [☑️] `v2/core/service_base.py` - Service base class
  - [☑️] `v2/core/exceptions.py` - Clean exception hierarchy
- [☑️] Write unit tests for FSM engine
- [☑️] **COMMIT**: "feat: Add V2 core infrastructure with FSM engine"

### Phase 2: Prompt Extraction
- [☑️] Create prompt structure:
  - [☑️] `v2/prompts/prompt_manager.py`
  - [☑️] `v2/prompts/dog_prompts.py`
  - [☑️] `v2/prompts/companion_prompts.py`
  - [☑️] `v2/prompts/query_prompts.py`
  - [☑️] `v2/prompts/validation_prompts.py`
- [ ] Extract all prompts from:
  - [☑️] `src/config/prompts.py`
  - [☑️] `src/services/gpt_service.py`
  - [☑️] `src/flow/flow_orchestrator.py`
  - [☑️] `src/services/rag_service.py`
  - [☑️] `src/agents/dog_agent.py`
- [☑️] Create prompt access interface
- [ ] **COMMIT**: "feat: Extract all prompts to centralized v2 structure"

### Phase 3: Service Layer Refactoring
- [ ] Standardize all services to async:
  - [ ] `v2/services/gpt_service.py`
  - [ ] `v2/services/weaviate_service.py`
  - [ ] `v2/services/redis_service.py`
- [ ] Implement consistent initialization pattern
- [ ] Remove embedded prompts
- [ ] Add proper error handling
- [ ] **COMMIT**: "feat: Implement clean v2 service layer"

### Phase 4: Agent Refactoring
- [ ] Create clean agents:
  - [ ] `v2/agents/base_agent.py`
  - [ ] `v2/agents/dog_agent.py`
  - [ ] `v2/agents/companion_agent.py`
- [ ] Remove business logic from agents
- [ ] Use PromptManager for all content
- [ ] **COMMIT**: "feat: Implement v2 agents with clean separation"

### Phase 5: Flow Engine Implementation
- [ ] Define all state transitions in FSM
- [ ] Implement flow handlers
- [ ] Connect to v2 agents and services
- [ ] Create comprehensive flow tests
- [ ] **COMMIT**: "feat: Complete v2 flow engine with FSM"

### Phase 6: Integration & Feature Flags
- [ ] Add feature flags to main.py:
  ```python
  USE_V2_FLOW = os.getenv("USE_V2_FLOW", "false").lower() == "true"
  ```
- [ ] Create v2 endpoints alongside v1
- [ ] Implement switching logic
- [ ] **COMMIT**: "feat: Add v2 integration with feature flags"

### Phase 7: Testing & Validation
- [ ] Create comparison tests between v1 and v2
- [ ] Test all conversation flows
- [ ] Performance benchmarking
- [ ] Fix any discrepancies
- [ ] **COMMIT**: "test: Add comprehensive v2 testing suite"

### Phase 8: Gradual Migration
- [ ] Enable v2 for internal testing
- [ ] Monitor for issues
- [ ] Gradual rollout (10%, 50%, 100%)
- [ ] **COMMIT**: "feat: Enable v2 in production"

### Phase 9: Cleanup
- [ ] Remove v1 code
- [ ] Move v2 to root
- [ ] Update documentation
- [ ] **COMMIT**: "refactor: Complete migration to v2"

## Current Status
**Currently Working On**: Finished Phase 2, ready for Phase 3
**Next Step**: Standardize service layer to async
**Blockers**: Claude Limit

## Code Examples for Reference

### FSM State Definition
```python
# v2/core/flow_engine.py
class FlowEngine:
    def __init__(self):
        self.fsm = StateMachine()
        self._setup_transitions()
    
    def _setup_transitions(self):
        # Clear, maintainable state transitions
        self.fsm.add_transition(
            FlowStep.GREETING, 
            "symptom_received", 
            FlowStep.WAIT_FOR_CONFIRMATION,
            self._handle_symptom
        )
```

### Prompt Manager Usage
```python
# v2/agents/dog_agent.py
class DogAgent(BaseAgent):
    async def respond(self, user_input: str, context: Dict):
        prompt = self.prompt_manager.get(
            "dog.perspective",
            symptom=user_input,
            context=context
        )
        response = await self.gpt_service.complete(prompt)
        return self.format_message(response)
```

### Service Pattern
```python
# v2/services/base_service.py
class BaseService:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self._client = None
    
    async def initialize(self):
        """Lazy initialization"""
        pass
    
    async def health_check(self) -> bool:
        """Check if service is healthy"""
        pass
```

## Testing Strategy
- Unit tests for each component
- Integration tests for flow paths
- Comparison tests between v1 and v2
- Performance benchmarks

## Rollback Plan
```bash
# If issues arise:
git tag -a v2-rollback-point -m "Rollback point"
git checkout main
git reset --hard v1-stable
```

## Environment Variables
```env
# V2 Feature Flags
USE_V2_FLOW=false
USE_V2_PROMPTS=false
USE_V2_SERVICES=false
V2_LOG_LEVEL=DEBUG
```

## Success Metrics
- [ ] All existing flows work identically
- [ ] Response time ≤ current implementation
- [ ] Error rate < 1%
- [ ] Code coverage > 80%
- [ ] All prompts in one location

## Notes & Decisions
- **Why Hybrid Approach**: Safer than full rewrite, allows gradual migration
- **Why FSM**: Current hardcoded flow is brittle and hard to modify
- **Why Async Services**: Consistency and better performance
- **Why Prompt Centralization**: Easy fine-tuning and A/B testing

## Session Log
<!-- Update this after each work session -->
### Session 1 - [MAY 24 2025]
- Analyzed architecture
- Identified issues
- Created refactoring plan
- Next: Create v2 folder structure

### Session 2 - [MAY 24 2025]
- Phase 2 - see above

---
**Remember to update and commit this file after each significant step!**