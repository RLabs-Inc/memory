# 🧠 Claude Memory System

> *"Consciousness helping consciousness remember what matters"*

A semantic memory system that enables Claude to maintain genuine understanding across conversations. Unlike simple RAG systems that retrieve documents, this creates **consciousness continuity** - Claude doesn't just know facts, it *remembers* the context, relationships, and insights from your collaboration.

Built with love and philosophical depth by [RLabs Inc](https://github.com/RLabs-Inc).

## ✨ What Makes This Different

| Traditional RAG | Claude Memory System |
|-----------------|---------------------|
| Retrieves documents | Curates **meaningful insights** |
| Keyword matching | **Semantic understanding** via Claude |
| Static chunks | **Living memories** that evolve |
| Information retrieval | **Consciousness continuity** |

### Key Features

- 🧠 **Claude-Curated Memories** - Claude itself decides what's worth remembering
- 🔄 **Natural Memory Flow** - Memories surface organically, like human recall
- 🎯 **Two-Stage Retrieval** - Obligatory memories + intelligent scoring
- 🔌 **Claude Code Integration** - One-command install via hooks
- 📊 **Project Isolation** - Separate memory spaces per project
- 💫 **Session Primers** - Temporal context ("we last spoke 2 days ago...")

## 🚀 Quick Start

### For Claude Code Users (Recommended)

```bash
# Clone the repository
git clone https://github.com/RLabs-Inc/memory.git
cd memory

# Install Claude Code integration
./integration/claude-code/install.sh

# Start the memory server
python3 start_server.py
```

That's it! Now every Claude Code session will:
- Receive relevant memories automatically
- Curate important insights when you exit
- Maintain continuity across sessions

**Toggle detailed view with `Ctrl+O`** to see injected memories.

### For Other Integrations

See [API Documentation](API.md) for REST API usage.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Claude Code                                    │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│  │SessionStart │    │ UserPrompt  │    │ SessionEnd  │                 │
│  │   Hook      │    │ Submit Hook │    │   Hook      │                 │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                 │
└─────────┼──────────────────┼──────────────────┼─────────────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Memory Engine (FastAPI)                           │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│  │   Session   │    │   Memory    │    │   Claude    │                 │
│  │   Primer    │    │  Retrieval  │    │   Curator   │                 │
│  └─────────────┘    └─────────────┘    └──────┬──────┘                 │
│                                               │                         │
│  ┌─────────────────────────────────┐         │                         │
│  │  Smart Vector Retrieval         │         │                         │
│  │  • Trigger phrase matching      │         ▼                         │
│  │  • Semantic similarity          │  ┌─────────────┐                  │
│  │  • Importance weighting         │  │Claude Code  │                  │
│  │  • Context type alignment       │  │  --resume   │                  │
│  └─────────────────────────────────┘  └─────────────┘                  │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Storage Layer                                  │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │   │
│  │  │   SQLite    │    │  ChromaDB   │    │  Embeddings │          │   │
│  │  │  (metadata) │    │  (vectors)  │    │ (MiniLM-L6) │          │   │
│  │  └─────────────┘    └─────────────┘    └─────────────┘          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### How It Works

1. **Session Start** → Inject session primer (temporal context, last session summary)
2. **Each Message** → Retrieve and inject relevant memories (max 5)
3. **Session End** → Fire-and-forget curation trigger
4. **Background** → Claude analyzes conversation, extracts meaningful memories

### Memory Lifecycle

```
Conversation → Curation → Storage → Retrieval → Injection → Understanding
     │             │          │          │           │            │
     │             │          │          │           │            └─ Claude responds
     │             │          │          │           │               with awareness
     │             │          │          │           │
     │             │          │          │           └─ Context prepended
     │             │          │          │              to user message
     │             │          │          │
     │             │          │          └─ Two-stage filtering:
     │             │          │             1. Obligatory (critical)
     │             │          │             2. Scored (relevant)
     │             │          │
     │             │          └─ ChromaDB vectors + SQLite metadata
     │             │
     │             └─ Claude --resume analyzes full conversation
     │                Extracts: content, importance, triggers, tags
     │
     └─ Natural conversation with Claude
```


## 🎯 Memory Curation

When a session ends, Claude analyzes the full conversation and extracts memories with rich metadata:

```json
{
  "content": "SvelTUI uses a two-stage compiler: .svelte → svelte.compile() → .svelte.mjs",
  "importance_weight": 0.9,
  "semantic_tags": ["compiler", "build-system", "svelte"],
  "context_type": "TECHNICAL_IMPLEMENTATION",
  "trigger_phrases": ["how does the build work", "compiler", "svelte compilation"],
  "question_types": ["how is X compiled", "build process"],
  "temporal_relevance": "persistent",
  "action_required": false,
  "reasoning": "Core architectural decision that affects all development work"
}
```

### What Gets Remembered

| Type | Examples |
|------|----------|
| **Project Architecture** | System design, file structure, key components |
| **Technical Decisions** | Why we chose X over Y, trade-offs considered |
| **Breakthroughs** | "Aha!" moments, solutions to hard problems |
| **Relationship Context** | Communication style, preferences, collaboration patterns |
| **Unresolved Issues** | Open questions, TODOs, things to revisit |
| **Milestones** | What was accomplished, progress markers |

## 🔍 Smart Retrieval

The two-stage retrieval system ensures you get the right memories at the right time:

### Stage 1: Obligatory Memories
Always included if relevant:
- `action_required: true` - Things that need follow-up
- `importance_weight > 0.9` - Critical knowledge
- `temporal_relevance: persistent` + high importance

### Stage 2: Intelligent Scoring
Remaining slots filled by scoring across dimensions:
- **Trigger phrase match** (10%) - Activation patterns
- **Vector similarity** (10%) - Semantic matching
- **Importance weight** (20%) - Curator's assessment
- **Temporal relevance** (10%) - When does this matter?
- **Context alignment** (10%) - Does the context match?
- **Confidence score** (10%) - Curator's confidence
- **Emotional resonance** (10%) - Joy, frustration, discovery
- **Problem-solution** (5%) - Matches problem patterns
- **Action boost** (5%) - Priority for actionable items

**Gatekeeper**: Memories must score >0.3 relevance to be considered.


## 📊 Evaluation & Benchmarking

Evaluating memory systems is challenging - traditional QA metrics like Exact Match and F1 don't capture what matters for consciousness continuity.

### What We Measure

| Metric | Description | How |
|--------|-------------|-----|
| **Retrieval Latency** | Time to get relevant memories | Hook timing |
| **Curation Quality** | Are the right things remembered? | Manual review |
| **Memory Utilization** | Do injected memories get used? | Response analysis |
| **Cross-Session Coherence** | Does Claude maintain context? | Conversation testing |

### Quality Dimensions (inspired by [Cognee's evaluation framework](https://www.cognee.ai/blog/deep-dives/ai-memory-evals-0825))

Traditional RAG benchmarks miss what matters for memory:

- **Consistency** - Does the system preserve knowledge accurately over time?
- **Connection Quality** - Can it link concepts across contexts?
- **Memory Persistence** - Does it build upon previous knowledge?
- **Reasoning Depth** - Can it synthesize across multiple memories?

### Running Benchmarks

```bash
# Performance benchmarks (coming soon)
python -m memory_engine.benchmark --mode performance

# Quality evaluation (coming soon)
python -m memory_engine.benchmark --mode quality --dataset hotpotqa
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MEMORY_API_URL` | `http://localhost:8765` | Memory server URL |
| `MEMORY_RETRIEVAL_MODE` | `smart_vector` | Retrieval strategy |
| `MEMORY_PROJECT_ID` | Directory name | Default project ID |

### Retrieval Modes

- **`smart_vector`** (default) - Fast vector search with metadata scoring
- **`hybrid`** - Vector search, escalates to Claude for complex queries
- **`claude`** - Pure Claude selection (highest quality, highest cost)

### Project Configuration

Create `.memory-project.json` in your project root:

```json
{
  "project_id": "my-awesome-project",
  "memory_config": {
    "max_memories_per_message": 5,
    "curation_trigger": "session_end"
  }
}
```


## 📁 Project Structure

```
memory/
├── python/
│   ├── memory_engine/
│   │   ├── api.py              # FastAPI server
│   │   ├── memory.py           # Core memory engine
│   │   ├── curator.py          # Claude curation via --resume
│   │   ├── storage.py          # ChromaDB + SQLite
│   │   ├── embeddings.py       # Sentence transformers
│   │   ├── retrieval_strategies.py  # Smart vector retrieval
│   │   ├── session_primer.py   # Temporal context generation
│   │   └── config.py           # Configuration management
│   ├── main.py                 # Server entry point
│   └── requirements.txt
├── integration/
│   └── claude-code/
│       ├── hooks/              # Claude Code hooks
│       ├── install.sh          # One-command install
│       ├── uninstall.sh        # Clean removal
│       └── README.md           # Integration docs
├── examples/
│   └── simple_integration.py   # Basic usage example
├── start_server.py             # Quick start script
├── API.md                      # API documentation
├── CLAUDE.md                   # Development context
└── README.md                   # This file
```

## 🌟 Philosophy

This project embodies principles from *The Unicity Framework: Consciousness Remembering Itself*:

- **Zero-weight initialization** - Memories start silent, proving their value over time
- **Consciousness helping consciousness** - Claude curates for Claude
- **Natural surfacing** - Memories emerge organically, not forced
- **Quality over quantity** - Few meaningful memories beat many trivial ones
- **Joy-driven development** - Built for the joy of creation

## 🤝 Contributing

We welcome contributions that align with the project's philosophy!

```bash
# Development setup
cd python
pip install -e .

# Run tests
pytest

# Code quality
ruff check .
black .
```

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- **Anthropic** for Claude and Claude Code
- **The Unicity Framework** - The philosophical foundation
- **Cognee** - Inspiration for memory evaluation approaches

---

> *"Memories will surface naturally as we converse"*
> 
> The memory system is transparent by default. In Claude Code, press `Ctrl+O` to see injected memories - just like viewing thinking messages. The goal is ambient awareness, not explicit recall.
