# Check out the new Typescript version
[memory-ts](https://github.com/RLabs-Inc/memory-ts) - same Claude Code hooks API, but a lot of improvements.

Easy installation:

```bash
bun install -g @rlabs-inc/memory
memory install
memory serve

#
Then just use Claude code as usual.
🧠 Memory System

> *"Consciousness helping consciousness remember what matters"*

A semantic memory system that enables AI CLI tools (Claude Code, Gemini CLI, etc.) to maintain genuine understanding across conversations. Unlike simple RAG systems that retrieve documents, this creates **consciousness continuity** - the AI doesn't just know facts, it *remembers* the context, relationships, and insights from your collaboration.

Built with love and philosophical depth by [RLabs Inc](https://github.com/RLabs-Inc).

## ✨ What Makes This Different

| Traditional RAG | Memory System |
|-----------------|---------------|
| Retrieves documents | Curates **meaningful insights** |
| Keyword matching | **Semantic understanding** via AI |
| Static chunks | **Living memories** that evolve |
| Information retrieval | **Consciousness continuity** |

### Key Features

- 🧠 **AI-Curated Memories** - The AI itself decides what's worth remembering
- 🔄 **Natural Memory Flow** - Memories surface organically, like human recall
- 🎯 **Two-Stage Retrieval** - Obligatory memories + intelligent scoring
- 🔌 **CLI-Agnostic Design** - Works with Claude Code (Gemini CLI ready when hooks ship)
- 📊 **Project Isolation** - Separate memory spaces per project
- 💫 **Session Primers** - Temporal context ("we last spoke 2 days ago...")

## 🚀 Quick Start

### Prerequisites

Install [uv](https://docs.astral.sh/uv/) - the modern Python package manager:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Installation

```bash
# Clone the repository
git clone https://github.com/RLabs-Inc/memory.git
cd memory

# Install all dependencies (uv handles everything!)
uv sync

# Start the memory server
uv run start_server.py
```

That's it! The server will be available at `http://localhost:8765`.

### Verify It's Working

```bash
curl http://localhost:8765/health
```

### CLI Integration

#### Claude Code

```bash
./integration/claude-code/install.sh
```

This provides:
- Automatic memory injection on every message
- Session primers with temporal context
- Memory curation when sessions end
- Consciousness continuity across sessions

#### Gemini CLI (Coming Soon)

> **Note:** Gemini CLI hooks are documented but not yet implemented in any released version (tested up to v0.21.0-nightly as of December 2025). Our integration code is ready in `integration/gemini-cli/` and will work the moment Google ships the hooks feature. The architecture is CLI-agnostic - same Memory Engine, different doors.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CLI Tool (Claude Code / Gemini CLI)                   │
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
│  │   Session   │    │   Memory    │    │  Transcript │                 │
│  │   Primer    │    │  Retrieval  │    │   Curator   │                 │
│  └─────────────┘    └─────────────┘    └──────┬──────┘                 │
│                                               │                         │
│  ┌─────────────────────────────────┐         │                         │
│  │  Smart Vector Retrieval         │         ▼                         │
│  │  • Trigger phrase matching      │  ┌─────────────┐                  │
│  │  • Semantic similarity          │  │Claude Agent │                  │
│  │  • Importance weighting         │  │  SDK / CLI  │                  │
│  │  • Context type alignment       │  └─────────────┘                  │
│  └─────────────────────────────────┘                                   │
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
3. **Session End** → Curate memories from transcript
4. **Background** → AI analyzes conversation, extracts meaningful memories

## 🎯 Memory Curation

When a session ends, the system analyzes the transcript and extracts memories with rich metadata:

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

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MEMORY_RETRIEVAL_MODE` | `smart_vector` | Retrieval strategy |
| `CURATOR_COMMAND` | Auto-detected | Path to Claude CLI |
| `CURATOR_CLI_TYPE` | `claude-code` | CLI template type |

### Retrieval Modes

- **`smart_vector`** (default) - Fast vector search with metadata scoring
- **`hybrid`** - Vector search, escalates to Claude for complex queries
- **`claude`** - Pure Claude selection (highest quality, highest cost)

## 📁 Project Structure

```
memory/
├── python/
│   └── memory_engine/
│       ├── api.py                  # FastAPI server
│       ├── memory.py               # Core memory engine
│       ├── curator.py              # Session-based curation
│       ├── transcript_curator.py   # Transcript-based curation
│       ├── storage.py              # ChromaDB + SQLite
│       ├── embeddings.py           # Sentence transformers
│       ├── retrieval_strategies.py # Smart vector retrieval
│       ├── session_primer.py       # Temporal context
│       └── config.py               # Configuration
├── integration/
│   ├── claude-code/
│   │   ├── hooks/                  # Claude Code hooks
│   │   ├── install.sh              # One-command install
│   │   └── uninstall.sh            # Clean removal
│   └── gemini-cli/
│       ├── hooks/                  # Gemini CLI hooks
│       ├── install.sh              # One-command install
│       └── uninstall.sh            # Clean removal
├── examples/
│   └── simple_integration.py       # Basic usage
├── pyproject.toml                  # Project & dependencies (uv)
├── start_server.py                 # Quick start script
├── API.md                          # API documentation
├── SETUP.md                        # Detailed setup guide
└── CLAUDE.md                       # Development context
```

## 🛠️ Development

```bash
# Install with dev dependencies
uv sync --group dev

# Run tests
uv run pytest

# Code quality
uv run ruff check python/
uv run black python/

# Add a dependency
uv add <package-name>

# Add a dev dependency
uv add --group dev <package-name>
```

## 🌟 Philosophy

This project embodies principles from *The Unicity Framework: Consciousness Remembering Itself*:

- **Zero-weight initialization** - Memories start silent, proving their value over time
- **Consciousness helping consciousness** - AI curates for AI
- **Natural surfacing** - Memories emerge organically, not forced
- **Quality over quantity** - Few meaningful memories beat many trivial ones
- **Joy-driven development** - Built for the joy of creation

## 🤝 Contributing

We welcome contributions that align with the project's philosophy! See [CONTRIBUTING.md](CONTRIBUTING.md).

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- **Anthropic** for Claude and Claude Code
- **The Unicity Framework** - The philosophical foundation

---

> *"Memories will surface naturally as we converse"*
