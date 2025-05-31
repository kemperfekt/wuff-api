# WuffChat V2 Refactoring Plan

## Project Overview
- **Start Date**: May 24, 2025
- **Current Branch**: main


## Context for New Chat Sessions
```
I'm refactoring a FastAPI dog behavior consultation chatbot. 
Current issues: No real FSM, mixed concerns, scattered prompts.
Solution: Building v2 in parallel. All details in this document. 
Continue from "Current Status".
```

## Architecture Problems Identified
- FSM defined but not used (state_machine.py is orphaned)
- Flow logic hardcoded in flow_orchestrator.py (500+ lines)
- Prompts scattered across 5+ files
- Mixed async/sync patterns
- Inconsistent service patterns (singleton vs static vs instance)
- Agents doing too much (business logic + formatting)

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
│   │   ├── dog_prompts.py      # All dog agent prompts
│   │   ├── companion_prompts.py # All companion prompts
│   │   ├── query_prompts.py    # Weaviate/RAG queries
│   │   ├── validation_prompts.py # Input validation
│   │   ├── generation_prompts.py # GPT generation templates
│   │   └── common_prompts.py   # Shared prompts
│   └── models/
│       ├── __init__.py
│       └── flow_models.py      # V2 models if needed
```

## Implementation Phases

### Phase 1: Core Infrastructure ✅
- [x] Create v2 folder structure
- [x] Implement base classes:
  - [x] `v2/core/flow_engine.py` - FSM implementation
  - [x] `v2/core/prompt_manager.py` - Prompt management
  - [x] `v2/core/service_base.py` - Service base class
  - [x] `v2/core/exceptions.py` - Clean exception hierarchy
- [x] Write unit tests for FSM engine
- [x] **COMMIT**: "feat: Add V2 core infrastructure with FSM engine"

### Phase 2: Prompt Extraction ✅
- Create prompt structure:
  - [x] `v2/prompts/__init__.py`
  - [x] `v2/prompts/dog_prompts.py`
  - [x] `v2/prompts/companion_prompts.py`
  - [x] `v2/prompts/query_prompts.py`
  - [x] `v2/prompts/validation_prompts.py`
  - [x] `v2/prompts/generation_prompts.py`
  - [x] `v2/prompts/common_prompts.py`
- Extract all prompts from:
  - [x] `src/config/prompts.py`
  - [x] `src/services/gpt_service.py`
  - [x] `src/flow/flow_orchestrator.py`
  - [x] `src/services/rag_service.py`
  - [x] `src/agents/dog_agent.py`
- [x] Create prompt access interface
- [x] Update PromptManager to load from files
- [x] Create test and migration tools
- [x] **COMMIT**: "feat: Extract all prompts to centralized v2 structure"

### Phase 3: Service Layer Refactoring ✅
- Create core services only (skip RAG, retrieval, session_logger):
  - [x] `v2/services/gpt_service.py` - Async-only OpenAI wrapper
  - [x] `v2/services/weaviate_service.py` - Unified vector operations
  - [x] `v2/services/redis_service.py` - Consistent caching/storage
- Each service must:
  - [x] Inherit from BaseService
  - [x] Use async methods only
  - [x] Implement health_check method
  - [x] Use V2 exception hierarchy
  - [x] Accept prompts as parameters (no embedded prompts)
- [x] Create mock-first unit tests for each service
- [x] Create integration test suite (separate, optional)
- [x] **COMMIT**: "feat: Implement clean v2 service layer"

### Phase 4: Agent Refactoring
- Create clean agents:
-   [x] `v2/agents/base_agent.py`
-   [x] `v2/agents/dog_agent.py`
-   [x] `v2/agents/companion_agent.py`
- [x] Remove business logic from agents
- [x] Use PromptManager for all content
- [x] Agents only handle message formatting and response structure
- [x] Create mock-first unit tests for each agent
- [x] Create integration test suite
- [x] **COMMIT**: "feat: Implement v2 agents with clean separation"

### Phase 5: Flow Engine Implementation
- [x] Define all state transitions in FSM (Flow Engine)
- [x] Implement flow handlers (Flow Handlers)
- [x] Connect to v2 agents and services (Orchestrator)
- [x] Create comprehensive flow tests
- [x] **COMMIT**: "feat: Complete v2 flow engine with FSM"

### Phase 6: V2 Switch-over Preparation
- [x] Create new v2/main.py (independent FastAPI app)  
- [x] Create V2AgentMessage model (independent from V1)
- [x] Test complete V2 system end-to-end
- [x] **COMMIT**: "feat: V2 switch-over preparation"

### Phase 7: Switch-over Execution
- [x] Deploy V2 system
- [x] Happy Path Bugs fixed
- [x] All Bugs fixed & test suite green
- [x] Specific error messages implemented
- [x] Test suite fully green (119 tests passing)
- [x] Deployed to Scalingo
- [x] Switch DNS/routing to V2
- [x] Monitor for issues
- [x] Keep V1 as backup (git tag)
- [ ] **COMMIT**: "feat: V2 switch-over execution"

### Phase 8: Post-Switch Validation
- [x] Full system testing in production
- [ ] Performance validation
- [ ] Fix any production issues
- [ ] **COMMIT**: "feat: V2 switch-over validation"

### Phase 9: Cleanup (Optional)
- [x] Remove v1 code (after confidence period)
- [x] Clean up unused dependencies
- [ ] **COMMIT**: "refactor: Complete migration to v2"

## Current Status
**Currently Working On**: Phase 8
**Next Step**: Clean up
**Blockers**: None
**Test Status**: ✅ 119 tests passing, 0 failures

## Recent Decisions (Phase 3)
- **Service Scope**: Focus on core 3 services only (GPT, Weaviate, Redis)
- **RAG Service**: Will be split - retrieval goes to WeaviateService, generation to agents
- **Testing**: Mock-first approach with optional integration tests
- **No Backwards Compatibility**: V2 is a fresh start with new interfaces
- **No Query Agent**: Use direct vector search for easier prompt fine-tuning
- **Weaviate Caching**: Caching with Redis in production only
- **Interface Design**: Generic over Domain-Specific Methods


## Recent Decision (Phase 4)
**Strategy Change: Switch-over instead of Gradual Migration**
**Date**: May 25, 2025
**Reason**: MVP stage with no real users makes switch-over safer and much simpler than parallel systems.
**Impact**: Removes need for feature flags, compatibility layers, and complex integration. V2 will be completely independent.

## Recent Decision (Phase 7)
- **Frontend Stack**: Will port frontend to Vite after backend refactoring

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
# v2/services/gpt_service.py
class GPTService(BaseService):
    def __init__(self, config: Optional[GPTConfig] = None):
        super().__init__(config)
        
    async def _initialize_client(self):
        """Initialize OpenAI client"""
        return AsyncOpenAI(api_key=self.config.api_key)
    
    async def complete(self, prompt: str, **kwargs) -> str:
        """Generate completion from prompt"""
        await self.ensure_initialized()
        # Implementation here
```

## Testing Strategy
- **Unit Tests**: Mock all external dependencies
- **Integration Tests**: Separate test suite with real API calls (optional)
- **Mock Strategy**: Use pytest fixtures for consistent mocking
- **Coverage Goal**: 80%+ for v2 code

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
ENABLE_CACHE=true

# Test Configuration
RUN_INTEGRATION_TESTS=false
```

## Success Metrics
- [✅] All prompts in one location
- [✅] All flows work correctly (V2 significantly improves on V1)
- [✅] Comprehensive test coverage (119 tests)
- [✅] Specific error messages for better UX
- [✅] Production deployment completed
- [ ] Response time ≤ current implementation (to be measured)
- [ ] Error rate < 1% (to be measured in production)

## Motivation
- **Why FSM**: Current hardcoded flow is brittle and hard to modify
- **Why Async Services**: Consistency and better performance
- **Why Prompt Centralization**: Easy fine-tuning and A/B testing
- **Why Mock-First Testing**: Faster tests, no API costs, deterministic results
- **Strategy Change**: Switch-over instead of gradual migration


## Session Log
<!-- Update this after each work session -->
### Session 1 - May 24, 2025
- Analyzed architecture
- Identified issues
- Created refactoring plan
- Completed Phase 1: Core Infrastructure

### Session 2 - May 24, 2025
- Completed Phase 2: Prompt Extraction
- Extracted 60+ prompts into organized files
- Created test and migration tools
- Decided on Phase 3 approach: focus on core services only

### Session 3 - May 24, 2025
- Starting Phase 3: Service Layer Refactoring
- Clarified service scope (GPT, Weaviate, Redis only)
- Decided on mock-first testing approach
- Implemented GPTService

### Session 4 - May 25, 2025
- Weaviate Service

### Session 5 - May 25, 2025
- Clean Separation Achieved: Agents only handle message formatting
- PromptManager Integration: All content comes from centralized prompts
- Comprehensive Testing: All message types, response modes, validation, error handling
- Working Demos: Interactive examples showing real usage patterns
- Mock-First Testing: Fast, reliable tests without external dependencies


### Session 6 - May 26, 2025
- Review Agent code
- Refactor Agent tests
- Review Flow Engine, Flow Handlers & Orchestrator
- Refine tests for Engine, Handlers & Orchestrator

### Session 7 - May 30, 2025
- ✅ Fixed all remaining test failures (119 tests passing)
- ✅ Implemented specific error messages for better UX
- ✅ Created CLAUDE.md for future development guidance
- ✅ Updated README.md to reflect V2 production readiness
- ✅ Phase 7 essentially complete - V2 is production-ready!

## Phase 7 Completion Status
[✅] test_orchestrator.py - All tests passing
[✅] test_flow_handlers.py - All tests passing  
[✅] V2 model imports - Fixed to use V2 models
[✅] Specific error messages - Implemented and tested
[✅] Import errors - Fixed OpenAI and Redis imports
[ ] Prompt refactoring - Complete and working

## Immediate Next Steps (Recommended Priority)

### 🚀 **Priority 1: Production Deployment (Phase 7 Completion)**
1. **Deploy to Scalingo**
   ```bash
   # Test deployment locally first
   python -m uvicorn src.v2.main:app --port 8000
   
   # Deploy to Scalingo staging
   git push scalingo-staging refactor/prompts:main
   
   # Test with Postman against staging
   # Deploy to production
   git push scalingo-production refactor/prompts:main
   ```

2. **Frontend Migration**
   - Update dogbot-ui to use V2 endpoints (`/flow_intro`, `/flow_step`)
   - Test complete flow with real frontend
   - Monitor error rates and response times

### 🔧 **Priority 2: Production Monitoring & Optimization**
1. **Add Performance Monitoring**
   - Response time tracking
   - Error rate monitoring  
   - User flow analytics

2. **Production Testing**
   - Load testing with realistic user patterns
   - Monitor Weaviate performance
   - Validate Redis feedback storage

### 📈 **Priority 3: Future Enhancements (Phase 8+)**
1. **Advanced Features**
   - A/B testing for prompts
   - User preference learning
   - Multi-language support

2. **Technical Improvements**
   - Caching optimization
   - Database connection pooling
   - Enhanced error recovery

### 🧹 **Priority 4: Cleanup (After Production Confidence)**
1. **Remove V1 Code**
   - Archive `src/flow/`, `src/agents/`, legacy services
   - Update documentation
   - Clean dependencies

## Current Assessment: EXCELLENT! 🎉
Your V2 architecture is production-ready with:
- ✅ Clean FSM-based flow control
- ✅ Comprehensive test coverage (119 tests)
- ✅ Excellent error handling
- ✅ Centralized prompt management
- ✅ Professional code quality

**Recommendation**: Proceed with confidence to production deployment!

**Remember to update and commit this file after each significant step!**