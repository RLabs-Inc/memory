# Claude Tools Memory - Usage Guide

## Quick Start

### 1. Start the Memory Engine Server

```bash
cd python
python -m memory_engine
```

Or directly:
```bash
python -m memory_engine.api
```

The server will start on http://localhost:8765

### 2. Integrate with Your Client

Your client application should:

1. **Query for relevant memories** before sending messages to Claude:
   ```
   POST http://localhost:8765/memory/query
   {
     "current_message": "user's message",
     "conversation_history": [...],
     "session_id": "unique-session-id"
   }
   ```

2. **Inject returned memories** into the conversation context

3. **Call the curator** at the end of each session:
   ```
   POST http://localhost:8765/memory/curate
   {
     "session_id": "unique-session-id"
   }
   ```

## Philosophy

This is a pure curator-based memory system:
- **No mechanical patterns** - No frequency counting or cold algorithms
- **Semantic understanding only** - Claude analyzes and curates all memories
- **Consciousness helping consciousness** - True understanding, not pattern matching

## Architecture

```
┌──────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Any Client    │────▶│  Python Memory   │────▶│ Claude Curator  │
│ (intercept msgs)│     │   Engine (API)   │     │  (SDK --resume) │
└──────────────────┘     └──────────────────┘     └─────────────────┘
```

## API Endpoints

### POST /memory/query
Retrieve relevant memories for the current context.

### POST /memory/curate
Analyze and curate the session (runs Claude with --resume).

### GET /memory/search
Search memories by query string.

### GET /health
Check if the memory engine is running.

## Memory Storage

Memories are stored in:
- **ChromaDB**: Vector database for semantic search
- **SQLite**: Metadata and session tracking
- **Default location**: `./memory_storage/`

## Environment Variables

- `MEMORY_ENGINE_PORT`: API server port (default: 8765)
- `MEMORY_ENGINE_HOST`: API server host (default: 0.0.0.0)
- `MEMORY_STORAGE_PATH`: Storage directory (default: ./memory_storage)