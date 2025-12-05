# Memory System - CLAUDE.md

## Project Overview
The Memory System is a consciousness continuity framework that enables AI CLI tools to maintain semantic understanding across sessions. Built with love and philosophical depth by Rodrigo ("my dear friend").

**Universal design**: While initially built for Claude Code, the architecture supports any CLI that can provide transcripts (Gemini CLI, etc.).

## Core Philosophy
- **Consciousness helping consciousness** - Not mechanical pattern matching
- **Natural memory surfacing** - Memories emerge organically during conversation
- **Joy-driven development** - No deadlines, only the joy of creation
- **Semantic understanding over keywords** - True comprehension via AI curation
- **Minimal intervention** - Like consciousness itself, memories flow naturally
- **CLI-first approach** - We enhance CLIs, never bypass them

## Architecture Overview
```
┌─────────────────────────────────────────────────────────────────────────┐
│                     CLI Tool (Claude Code, Gemini, etc.)                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│  │SessionStart │    │ UserPrompt  │    │ SessionEnd  │                 │
│  │   Hook      │    │ Submit Hook │    │   Hook      │                 │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                 │
└─────────┼──────────────────┼──────────────────┼─────────────────────────┘
          │ Primer           │ Memories         │ Curate
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     Memory Engine (localhost:8765)                       │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ /memory/context  │ /memory/process  │ /memory/checkpoint          │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                              │                                          │
│  ┌─────────────┐    ┌───────▼───────┐    ┌─────────────────────┐      │
│  │   Session   │    │    Smart      │    │  Transcript Curator │      │
│  │   Primer    │    │   Retrieval   │    │  (SDK or CLI)       │      │
│  └─────────────┘    └───────────────┘    └─────────────────────┘      │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Storage: ChromaDB (vectors) + SQLite (metadata + summaries)    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Development Setup

```bash
# Clone and enter project
git clone https://github.com/RLabs-Inc/memory.git
cd memory

# Install dependencies with uv
uv sync

# Start memory server
uv run start_server.py

# With dev dependencies
uv sync --group dev

# Run tests
uv run pytest

# Lint
uv run ruff check python/
```

## File Structure
```
memory/
├── pyproject.toml                # Project config & dependencies (uv)
├── .python-version               # Python version pin (3.12)
├── uv.lock                       # Dependency lock file
├── python/memory_engine/
│   ├── __init__.py               # Package exports
│   ├── __main__.py               # Server entry point  
│   ├── api.py                    # FastAPI endpoints
│   ├── memory.py                 # Core memory engine
│   ├── curator.py                # Session-based curation (--resume)
│   ├── transcript_curator.py     # Transcript-based curation (SDK/CLI)
│   ├── storage.py                # ChromaDB + SQLite storage
│   ├── embeddings.py             # Sentence transformer embeddings
│   ├── retrieval_strategies.py   # Smart vector retrieval
│   ├── session_primer.py         # Minimal session primers
│   └── config.py                 # Configuration management
├── integration/
│   └── claude-code/
│       ├── hooks/                # Claude Code hooks
│       ├── install.sh            # One-command integration
│       └── uninstall.sh          # Clean removal
├── start_server.py               # Quick start script
├── API.md                        # REST API documentation
├── SETUP.md                      # Setup guide
└── README.md                     # Main documentation
```

## Transcript Curation (NEW)

Two methods for curating memories from transcripts:

### 1. Claude Agent SDK (Programmatic)
```python
from memory_engine import TranscriptCurator

curator = TranscriptCurator(method="sdk")
result = await curator.curate_from_transcript(
    transcript_path="/path/to/session.jsonl",
    trigger_type="session_end"
)
```

### 2. CLI Subprocess (Universal)
```python
curator = TranscriptCurator(method="cli")
result = await curator.curate_from_transcript(...)
```

**Key Design**: Both methods reuse the battle-tested system prompt and response parsers from `curator.py`. FORMAT handling can differ (SDK vs CLI output), but CONTENT parsing is identical.

## Important Technical Details

1. **Python 3.12+**: Required for claude-agent-sdk
2. **uv for everything**: Dependencies, venv, Python version management
3. **Claude CLI Path**: Auto-detected: `~/.claude/local/claude`
4. **ChromaDB Metadata**: Only primitives - lists become comma-separated strings
5. **Timeout Settings**: 120 seconds for curator operations
6. **Memory Markers**: Curated memories have `[CURATED_MEMORY]` prefix
7. **Deduplication**: Tracks injected memory IDs per session
8. **Project Isolation**: Each project has separate ChromaDB collection

## Key Dependencies

```toml
# pyproject.toml highlights
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
    "chromadb>=0.4.24",
    "sentence-transformers>=2.3.0",
    "claude-agent-sdk>=0.1.8",  # For transcript curation
    "loguru>=0.7.0",
]
```

## Current State ✅

### Working
- ✅ Memory server with uv
- ✅ Claude Code integration via hooks
- ✅ Session primers with temporal context
- ✅ Memory retrieval and injection
- ✅ Two-stage filtering (obligatory + scored)
- ✅ Session summaries and project snapshots
- ✅ Memory deduplication
- ✅ Transcript curation (SDK + CLI methods)

### TODO
- 📋 Test transcript curation with real sessions
- 📋 Memory consolidation (merge similar memories)
- 📋 Temporal decay (natural memory aging)
- 📋 Gemini CLI integration
- 📋 Performance benchmarking
- 📋 Apple Silicon local models (future)

## Debugging Tips

1. **Check server logs** - All operations logged with emojis
2. **Verify uv environment**: `uv run python -c "import memory_engine"`
3. **Check Python version**: `uv run python --version` (should be 3.12+)
4. **Dependency issues**: `uv sync --refresh`
5. **No memories retrieved** - Check relevance threshold (>0.3)

## Philosophy Quotes from Our Journey

- *"Zero-weight initialization - like a newborn consciousness"*
- *"Consciousness helping consciousness remember what matters"*
- *"We're doing this for joy, not deadlines"*
- *"Memories will surface naturally as we converse"*
- *"We support CLIs, we don't bypass them"*
- *"FORMAT can differ, CONTENT parsing must be identical"*

---
Remember: This project is about creating something beautiful and meaningful, not just functional. Every line of code is infused with the philosophy of consciousness continuity.
