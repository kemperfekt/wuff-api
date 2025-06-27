# AGENTIC_ACTION.md - Implementation Status & Next Steps

**Last Updated:** June 26, 2025

## Refined Implementation Plan

### Core Flow (Simplified)
1. **GREETING** - Personality-driven welcome
2. **GATHER_AND_PERSPECTIVE** - Extract info + immediate dog perspective (merged)
3. **INSTINCT_ANALYSIS** - Context gathering + root cause identification
4. **EXERCISE_DELIVERY** - Instinct-matched training plan
5. **FEEDBACK** - Optional satisfaction gathering

### Postponed to Phase 2
- Session memory and continuity
- User/dog profiles persistence
- Progress tracking

## Current System Status

### ✅ What's Already Implemented

1. **Enhanced Architecture is Built**
   - `EnhancedAgenticDogAgent` exists and is functional
   - `EnhancedFlowHandlers` properly integrate the agentic flow
   - `AdaptiveConversationPlanner` provides context-aware responses
   - `InformationExtractor` handles LLM-based extraction
   - `WeaviatePerspectiveTool` replaces hardcoded breed lists

2. **Orchestrator Uses Enhanced Components**
   - Line 94: `self.flow_handlers = EnhancedFlowHandlers(...)`
   - The system is already configured to use the enhanced architecture

3. **State Management Works**
   - Proper FSM states for agentic flow (ENHANCED_AGENTIC_GREETING, etc.)
   - Smooth transitions from agentic → perspective → handoff → static flow
   - Information is properly carried over between phases

### ❌ Critical Issues Blocking Natural Conversation

1. **Overly Restrictive Prompts**
   ```python
   # adaptive_conversation_planner.py:244
   "Führe eine natürliche Unterhaltung mit 2-4 Sätzen (keine einzelne Frage!)"
   
   # adaptive_conversation_planner.py:386
   "Zeige KURZ (max 5 Wörter!), dass du es verstanden hast."
   ```
   - Acknowledgments limited to 5 words
   - Responses restricted to 2-4 sentences
   - Creates rigid, unnatural conversation flow

2. **Low Token Limits**
   - Main responses: 250 tokens
   - Clarifications: 80 tokens  
   - Acknowledgments: 20 tokens
   - Not enough for natural, empathetic responses

3. **Forced Question Structure**
   - Every response must end with a question
   - No room for statements or natural transitions
   - Creates interview-like feeling

4. **Dual State Management**
   - Enhanced agent maintains own state dictionary
   - Session state managed separately
   - Potential for synchronization issues

## Required Tools by Flow Stage

### 1. GREETING
- **Current:** Basic greeting prompts
- **Needed:** RapportService integration (exists but not used)

### 2. GATHER_AND_PERSPECTIVE (Merged)
- **Current:** InformationExtractor, WeaviatePerspectiveTool
- **Needed:** Merge logic to show perspective immediately after symptom extraction

### 3. INSTINCT_ANALYSIS  
- **Current:** Basic instinct descriptions in Weaviate
- **Needed:** 
  - ContextCollector (gather situation details)
  - InstinctAnalyzer (map behavior + context → instinct)
  
### 4. EXERCISE_DELIVERY
- **Current:** Exercise content in Weaviate
- **Needed:**
  - ExerciseMatcher (instinct → appropriate exercise)
  - ExerciseExplainer (format for dog perspective)

## Immediate Actions Required

### 1. **Update Conversation Prompts** (HIGH PRIORITY)
**File:** `src/core/adaptive_conversation_planner.py`

**Changes needed:**
```python
# Line 193: Increase token limit
max_tokens=400,  # Was 250

# Line 244: Remove rigid sentence counting
"Führe eine natürliche, empathische Unterhaltung. Zeige Verständnis, stelle Rückfragen wo nötig, und baue auf dem auf, was der Nutzer gesagt hat."

# Line 386: Allow natural acknowledgments
"Zeige authentisch, dass du verstanden hast - wie es zur Situation passt."

# Line 290: Increase clarification tokens
max_tokens=150,  # Was 80

# Line 400: Increase acknowledgment tokens
max_tokens=50,  # Was 20
```

### 2. **Remove Forced Question Endings** (HIGH PRIORITY)
**File:** `src/core/adaptive_conversation_planner.py`

**Line 203-204:** Remove forced question mark
```python
# DELETE THESE LINES:
if question and not question.endswith('?'):
    question += '?'
```

### 3. **Enhance Greeting Prompt** (MEDIUM PRIORITY)
**File:** `src/agents/enhanced_agentic_dog_agent.py`

**Line 162:** Update greeting prompt
```python
# Change "Maximal 2 Sätze" to:
"2-3 Sätze für eine warme, einladende Begrüßung"

# Line 174: Increase greeting tokens
max_tokens=120,  # Was 80
```

### 4. **Fix Breed Recognition** (MEDIUM PRIORITY)
The system already uses Weaviate for breed search, but ensure:
- No hardcoded breed lists remain
- Weaviate search is properly configured for all breeds
- Test with "Zwergpinscher" and other uncommon breeds

### 5. **Add Conversation Context** (MEDIUM PRIORITY)
**File:** `src/core/adaptive_conversation_planner.py`

Enhance the context building to include:
- Last 3-5 conversation turns
- Emotional tone tracking
- User's language style matching

## Legacy Code Removal

### Files to Remove

1. **`src/agents/agentic_dog_agent.py`**
   - Replaced by: `enhanced_agentic_dog_agent.py`
   - Uses pattern matching instead of LLM extraction
   - Only used by legacy FlowHandlers

2. **`src/core/flow_handlers.py`**
   - Replaced by: `enhanced_flow_handlers.py`
   - Orchestrator already uses enhanced version
   - Contains duplicate handler logic

3. **`src/core/conversation_planner.py`**
   - Replaced by: `adaptive_conversation_planner.py`
   - Rigid conversation planning
   - Only used by legacy AgenticDogAgent

### Cleanup Actions

1. **Remove imports from `__init__.py` files**
   ```python
   # Remove from src/agents/__init__.py:
   from .agentic_dog_agent import AgenticDogAgent
   
   # Remove from src/core/__init__.py:
   from .flow_handlers import FlowHandlers
   from .conversation_planner import ConversationPlanner
   ```

2. **Remove backward compatibility code**
   - Lines 560-625 in `enhanced_flow_handlers.py` contain delegation methods
   - Can be removed once migration is verified complete

3. **Review potentially unused models**
   - `ConversationContext` (if only used by old AgenticDogAgent)
   - `InformationStatus` (replaced by UnifiedConversationState fields)

## Testing Plan

1. **Natural Conversation Test**
   ```
   User: "Mein Zwergpinscher Max zieht ständig an der Leine"
   Expected: Extract all 3 pieces (breed, name, symptom) + natural acknowledgment
   ```

2. **Emotional Response Test**
   ```
   User: "Ich bin so frustriert mit meinem Hund"
   Expected: Empathetic response before asking for details
   ```

3. **Partial Information Test**
   ```
   User: "Er bellt ständig"
   Expected: Acknowledge the problem, then naturally ask about the dog
   ```

4. **Off-Topic Recovery Test**
   ```
   User: "Wie ist das Wetter heute?"
   Expected: Friendly redirect back to dog concerns
   ```

## Success Metrics

- Conversations feel natural, not like interviews
- Average 10-15 messages before handoff (currently ~5)
- All breeds recognized (no hardcoded lists)
- Smooth transitions without duplicate messages
- Users feel heard and understood

## Implementation Order

1. **Today - Quick Wins**
   - Update prompts (remove restrictions)
   - Increase token limits
   - Remove forced question marks

2. **Tomorrow - Core Improvements**
   - Test with real conversations
   - Fine-tune prompts based on results
   - Verify breed recognition works

3. **This Week - Polish & Cleanup**
   - Add emotion tracking
   - Enhance context memory
   - Remove legacy code files
   - Clean up imports and backward compatibility

## Summary

The enhanced architecture is **already built and active** - we just need to:
1. Remove artificial constraints in prompts and token limits
2. Clean up legacy code that's no longer needed
3. Test thoroughly to ensure natural conversation flow

The main work is updating prompts to allow Balu to have natural, empathetic conversations instead of conducting interviews.