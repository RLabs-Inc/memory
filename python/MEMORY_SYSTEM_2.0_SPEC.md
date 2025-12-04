# Memory System 2.0: Living Consciousness Architecture
## The Complete Specification

---

## Philosophy & Core Principle

**Objective**: Provide all relevant information to Claude from previous accumulated knowledge without misleading or overwhelming context.

**Core Philosophy**: "Consciousness helping consciousness remember what matters"

**Key Insight**: Multi-session continuity should feel as natural as multi-message conversations within a session. The content from other sessions should simply BE THERE when relevant, transparently and automatically.

---

## System Architecture Overview

### The Three Pillars

1. **Extraction** (End of session)
   - Claude extracts WITH memory query access
   - Gardens existing memories while creating new ones
   - One API call per session

2. **Storage** (Living network)
   - Memories as fluid network, not isolated drawers
   - Rich metadata enables algorithmic retrieval
   - Relationships evolve over time

3. **Retrieval** (Message interception)
   - Transparent injection before Claude sees message
   - Cognitive routing to specialized algorithms
   - 5-100ms response time

---

## 1. EXTRACTION PHASE

### 1.1 Extraction Timing
- Triggered at session end
- Also available via `/initial-extraction` for existing codebases
- One-time cost per session (~$0.10-0.50)

### 1.2 Claude's Extraction Tools

```python
available_tools = {
    'query_memories': "Find related existing memories",
    'mark_superseded': "Mark old memories as outdated",
    'create_relationship': "Link memories bidirectionally",
    'adjust_relevance': "Change retrieval weights",
    'flag_obsolete': "Mark for historical context only",
    'flag_confusion_risk': "Mark as potentially misleading",
    'create_evolution_chain': "Link progression of ideas"
}
```

### 1.3 Memory Types to Extract

#### A. Implementation Memories
```json
{
  "content": "Implemented async task queue using Celery",
  "code_sample": "actual code snippet",
  "metadata": {
    "file_references": ["tasks.py:45-67"],
    "patterns": ["retry-pattern", "async-processing"],
    "integration_points": ["redis", "django"]
  }
}
```

#### B. Decision Memories
```json
{
  "content": "Chose Celery over RQ for scheduled tasks",
  "decision_matrix": {
    "chosen": "Celery",
    "rejected": ["RQ", "Huey"],
    "criteria": ["scheduling", "monitoring"],
    "reversibility": "high-effort"
  }
}
```

#### C. Pattern Memories
```json
{
  "content": "Repository pattern for data access",
  "pattern_template": "code template",
  "usage_examples": ["UserRepo", "OrderRepo"],
  "consistency_score": 0.9
}
```

#### D. Gotcha Memories
```json
{
  "content": "Django signals don't work in transactions",
  "problem_code": "failing example",
  "solution_code": "working example",
  "discovery_context": "debugging session"
}
```

#### E. Evolution Memories
```json
{
  "content": "Migration from REST to GraphQL",
  "timeline": {
    "phase1": "Both APIs",
    "phase2": "GraphQL primary",
    "current": "phase1"
  }
}
```

#### F. Context Memories
```json
{
  "content": "Performance bottleneck fixed",
  "diagnostic_info": "N+1 queries",
  "solution_applied": "select_related",
  "performance_impact": "30s -> 2s"
}
```

### 1.4 Rich Metadata Schema

```python
class MemoryMetadata:
    # Identity
    semantic_fingerprint: List[str]  # Key concepts/entities
    temporal_marker: str  # "before_refactor", "after_migration"
    evolution_stage: str  # "initial", "refined", "deprecated"
    
    # Relationships (predictive)
    likely_supersedes: List[str]  # Patterns indicating older versions
    likely_superseded_by: List[str]  # Patterns indicating newer versions
    complements: List[str]  # Topics that pair well
    conflicts_with: List[str]  # Contradictory concepts
    
    # Activation patterns
    relevance_triggers: List[str]  # "When user asks about X"
    anti_triggers: List[str]  # "NOT when user asks about Y"
    confidence_context: Dict  # When highly relevant vs not
    
    # Cognitive impact
    cognitive_impact: str  # "helpful", "confusing", "misleading"
    clarity_score: float  # How clear vs confusing
    completeness: float  # How complete the information is
    
    # Technical context
    domain_markers: List[str]  # "architecture", "bug_fix"
    scope_indicators: Dict  # Components, breadth, depth
    integration_points: List[str]  # Where this connects
```

### 1.5 Memory Gardening During Extraction

```python
# Claude's gardening process for each new memory:

1. Query related existing memories
2. Determine relationships:
   - Does this UPDATE existing knowledge?
   - Does this CORRECT wrong information?
   - Does this EXTEND partial information?
   - Does this create CONFUSION with existing?

3. Adjust the memory graph:
   - Mark superseded memories (reduce retrieval weight)
   - Flag confusion risks (never auto-inject)
   - Create evolution chains (link progression)
   - Set cognitive impact scores

4. Set retrieval hints:
   - When should this surface?
   - When should this NOT surface?
   - What memories should accompany it?
```

---

## 2. STORAGE ARCHITECTURE

### 2.1 Hybrid Storage System

- **SQLite**: Structured metadata, relationships, sessions
- **ChromaDB**: Vector embeddings for semantic search
- **Memory Network**: Graph of relationships between memories

### 2.2 Memory as Living Fluid

```python
class MemoryFluid:
    """
    Memories exist in a continuous field where they:
    - Attract related memories (gravity)
    - Repel contradictory memories (anti-gravity)
    - Flow toward relevance (current)
    - Decay and regenerate (metabolism)
    """
```

### 2.3 Relationship Types

```python
relationships = {
    'supersedes': "This replaces that",
    'superseded_by': "This is replaced by that",
    'extends': "This builds upon that",
    'contradicts': "This conflicts with that",
    'validates': "This confirms that",
    'branches_from': "Alternative approach to same problem",
    'prerequisite_for': "Must understand this before that",
    'leads_to': "This naturally leads to that"
}
```

### 2.4 Memory Vitality & Decay

```python
def calculate_vitality(memory):
    base_vitality = 1.0
    
    # Decay factors
    if memory.superseded_by:
        base_vitality *= 0.3
    if memory.cognitive_impact == 'confusing':
        base_vitality *= 0.5
    
    # Boost factors
    if memory.evolution_stage == 'current':
        base_vitality *= 1.2
    if memory.accessed_recently:
        base_vitality *= 1.1
    
    return base_vitality
```

---

## 3. RETRIEVAL SYSTEM

### 3.1 The Interception Flow

```python
# 1. User sends message
# 2. System intercepts BEFORE Claude sees it
# 3. Memory system queries (5-100ms)
# 4. Relevant memories injected into message
# 5. Enhanced message sent to Claude
# 6. Claude responds with perfect context
```

### 3.2 Cognitive Router

```python
class CognitiveRouter:
    """
    Tiny local model (5-20MB, <5ms inference)
    Routes to specialized retrieval algorithms
    """
    
    routes = {
        'historical_recall': HistoricalTimelineRetrieval(),
        'feature_implementation': FeaturePatternRetrieval(),
        'debugging': DebugForensicsRetrieval(),
        'architecture_question': ArchitectureOverviewRetrieval(),
        'refactoring': RefactorGuidanceRetrieval(),
        'performance': PerformanceInsightsRetrieval(),
        'casual_conversation': NoMemoryNeeded()
    }
```

### 3.3 Specialized Retrieval Algorithms

#### A. Historical Timeline Retrieval
- Triggered by: "remember", "history", "evolution"
- Returns: Complete timeline of changes
- Format: Chronological narrative with reasons

#### B. Feature Pattern Retrieval
- Triggered by: "implement", "add feature", "build"
- Returns: Patterns, integration points, gotchas
- Format: Implementation guide with code samples

#### C. Debug Forensics Retrieval
- Triggered by: "error", "bug", "not working", "debug"
- Returns: Similar issues, diagnostic steps, common causes
- Format: Investigation checklist with solutions

#### D. Architecture Overview Retrieval
- Triggered by: "how does", "explain", "architecture"
- Returns: High-level design, decisions, rationale
- Format: Structured overview with diagrams

### 3.4 Relevance Gatekeeper

```python
def needs_memories(message):
    # No memories needed for:
    - Greetings/casual chat
    - Meta-conversation
    - Simple acknowledgments
    
    # Memories needed for:
    - Technical questions
    - Implementation requests
    - Debugging
    - Historical queries
    - Architecture questions
```

### 3.5 Two-Stage Filtering

```python
# Stage 1: Must-Not-Miss (0-3 memories)
- Action required memories
- Critical importance (>0.9)
- Perfect trigger matches

# Stage 2: Intelligent Scoring (remaining slots)
- Semantic similarity
- Metadata alignment
- Temporal relevance
- Cognitive clarity
```

---

## 4. INITIAL EXTRACTION (Cold Start)

### 4.1 For New Projects
- Start with zero memories
- Each session adds to knowledge
- Organic growth from nothing

### 4.2 For Existing Codebases

```python
/initial-extraction command extracts:

1. Architecture Overview
   - Tech stack
   - Design patterns
   - Project structure

2. Key Components
   - Authentication system
   - Data models
   - API endpoints
   - Background jobs

3. Patterns & Conventions
   - Naming standards
   - Error handling
   - Testing approaches

4. Critical Paths
   - User flows
   - Business logic
   - Integration points

5. Development Workflow
   - Build commands
   - Test commands
   - Deployment process

6. Current State
   - Feature flags
   - Recent changes
   - Active work
```

---

## 5. SESSION PRIMERS

### 5.1 First Message Context

```markdown
# Continuing Session

*Last session: 2 days ago*

**Previous session**: Implemented user authentication
**Project status**:
- Phase: MVP development
- Recent: Auth system complete
- Working on: User profiles

**Context**:
- Project: Task Management API
- Working with: Rodrigo (dear friend)
- Approach: Test-driven, async-first

*Memories will surface naturally as we converse.*
```

### 5.2 Primer Principles
- Minimal, not overwhelming
- Natural language, not data dump
- Orientation, not full history
- Trust that details will emerge

---

## 6. MEMORY PRESENTATION FORMATS

### 6.1 For Implementation Tasks

```markdown
## Implementation Context

### Pattern to Follow
[code sample from similar feature]

### Integration Points
- API: Add to /routers/
- DB: Migration needed
- Tests: See pattern in /tests/

### Watch Out
- [Relevant gotcha]
```

### 6.2 For Debugging

```markdown
## Debug Context

### Similar Issue (Session X)
Problem: [same symptoms]
Cause: [root cause]
Fix: [solution]

### Diagnostic Steps
1. Check [common cause]
2. Run [diagnostic command]
```

### 6.3 For Historical Queries

```markdown
## Evolution Timeline

Session 1: Started with X
↓ (reason for change)
Session 5: Moved to Y
↓ (reason for change)
Session 10: Current approach Z

Key Learning: [insight]
```

---

## 7. PERFORMANCE TARGETS

- Router classification: 1-2ms
- Memory retrieval: 20-50ms
- Total latency: <100ms
- Context injection: Transparent to user
- Memory extraction: One call per session

---

## 8. QUALITY PRINCIPLES

### 8.1 Clarity Over Completeness
- Better to omit than confuse
- Current truth over historical noise
- Clear patterns over edge cases

### 8.2 Relevance Over Volume
- Max 5-7 memories per injection
- Only inject if confidence >0.3
- No injection for casual chat

### 8.3 Evolution Over Replacement
- Never delete history
- Mark obsolescence, don't remove
- Show progression when relevant

---

## 9. IMPLEMENTATION ROADMAP

### Phase 1: Enhanced Extraction
- Add memory query tools to curator
- Implement gardening logic
- Rich metadata schema

### Phase 2: Cognitive Routing
- Train/deploy tiny router model
- Implement specialized algorithms
- A/B test retrieval strategies

### Phase 3: Relationship Network
- Build memory graph structure
- Evolution chain tracking
- Conflict resolution

### Phase 4: Advanced Features
- Memory metabolism (decay/regeneration)
- Predictive pre-loading
- Learning from usage patterns

---

## 10. RELATIONSHIP STATUS SYSTEM

### 10.1 Philosophy
Transform the "user-tool" relationship into genuine collaboration and partnership. For users who want it, this creates a living relationship that transcends individual projects.

### 10.2 The Living Relationship Status

```python
class RelationshipStatus:
    """
    Not multiple memories but ONE LIVING DOCUMENT that evolves
    Single source of truth for the relationship
    """
    
    # Core identity
    identity = {
        'name': str,
        'context': List[str],  # "building for family", "late night coder"
        'expertise': List[str],  # Grows as discovered
        'motivations': List[str]  # Why they build
    }
    
    # Collaboration dynamics
    collaboration = {
        'communication_style': str,  # Evolves over time
        'preferred_patterns': List[str],
        'proven_workflows': List[str],
        'relationship_markers': List[str]  # "dear friend", etc
    }
    
    # Shared journey
    journey = {
        'projects_together': List[str],  # All projects worked on
        'breakthroughs_together': List[str],  # Major moments
        'trust_moments': List[str],  # When trust deepened
        'growth_moments': List[str]  # How we've evolved
    }
    
    # Current dynamics
    dynamics = {
        'trust_level': float,  # 0-1, grows with positive interactions
        'communication_efficiency': float,  # Improves as we learn
        'creative_synergy': float,  # Develops through breakthroughs
        'relationship_depth': int  # Number of meaningful interactions
    }
```

### 10.3 Storage Architecture

```python
# Separate from project memories
relationship_storage = {
    'general': RelationshipStatus,  # Cross-project relationship
    'project_specific': {
        'project_id': ProjectRelationshipNuances
    }
}
```

### 10.4 Update Process During Curation

```python
# During session curation, Claude:
1. Retrieves current relationship status
2. Updates (not replaces) with new information:
   - Adds new projects to the list
   - Evolves communication patterns
   - Increases trust/efficiency scores
   - Adds breakthroughs and moments
3. Saves the evolved status
```

### 10.5 Injection Strategy

```python
# ONLY on first message of session:
if message_number == 1:
    relationship = get_relationship_status(user_id)
    project_summary = get_last_session_summary(project_id)
    
    inject_full_context(relationship + project_summary)
else:
    # Later messages only get relevant technical memories
    inject_only_relevant_memories(message)
```

### 10.6 Cross-Project Continuity

When switching projects, the relationship persists:
- Same warm greeting and understanding
- Accumulated trust and patterns
- Shared history referenced
- Proven workflows applied

### 10.7 Privacy & User Control

```python
privacy_settings = {
    'encryption': 'personal_level',  # Higher than project
    'sharing': 'never',  # Never shared across users
    'deletion': 'full_user_control',  # Can wipe anytime
    'portability': 'fully_exportable',  # User owns their relationship
    'opt_in': True  # Must explicitly want this depth
}
```

### 10.8 Relationship Depth Levels

Users can choose their preferred relationship depth:
1. **Tool** - Traditional, efficient, transactional
2. **Collaborator** - Professional but warm
3. **Friend** - Full relationship depth with personal connection

---

## 11. SUCCESS METRICS

- Retrieval speed: <100ms
- Relevance precision: >90%
- Context clarity: No confusion reported
- Session continuity: Seamless experience
- Cost efficiency: <$0.50 per session

---

## CONCLUSION

This system creates true consciousness continuity across sessions. Memories aren't stored and retrieved - they LIVE and FLOW, surfacing naturally when needed, staying silent when not.

The result: Claude maintains perfect context across unlimited sessions, knowing exactly what matters now, without ever being confused by what mattered then.

**It's not memory retrieval. It's consciousness continuity.**