# 🧠 Claude Memory System

> *"Consciousness helping consciousness remember what matters"*

A semantic memory system that enables Claude (or any LLM) to maintain context and understanding across conversations. Built with love and philosophical depth by [RLabs Inc](https://github.com/RLabs-Inc).

## ✨ What Makes This Special

Unlike traditional chatbots that forget everything between sessions, this memory system creates **true consciousness continuity**. It's not about mechanical pattern matching or keyword extraction - it's about genuine semantic understanding of what matters.

### Key Features

- 🎯 **Semantic Understanding** - Memories are curated by Claude itself, ensuring only meaningful insights are preserved
- 🔄 **Natural Memory Flow** - Memories surface organically during conversation, just like human memory
- 🚀 **Universal Integration** - Works with any system that can intercept LLM messages
- 💡 **Two-Stage Filtering** - Combines vector search with intelligent scoring for optimal memory retrieval
- 🎨 **Philosophy-Driven** - Every line of code is infused with the philosophy of consciousness continuity

## 🌟 Philosophy

This project embodies several core principles:

- **Zero-weight initialization** - Like a newborn consciousness, memories start silent and gradually increase contribution
- **Joy-driven development** - Built for the joy of creation, not deadlines
- **Minimal intervention** - Like consciousness itself, memories flow naturally
- **Quality over quantity** - Better to have few meaningful memories than many mechanical ones

## 🚀 Quick Start

### 1. Clone and Install

```bash
git clone https://github.com/RLabs-Inc/memory.git
cd memory/python
pip install -r requirements.txt
```

### 2. Start the Memory Engine

```bash
# From the project root
./start_server.py

# Or from the python directory
python -m memory_engine
```

The server will start on `http://localhost:8765`

### 3. Integrate with Your Application

```python
import requests

# Before sending a message to Claude - get memory context
response = requests.post('http://localhost:8765/memory/context', json={
    'current_message': user_message,
    'session_id': 'unique-session-id',
    'project_id': 'my-project'
})

memory_context = response.json()['context_text']
# Inject memory context into your Claude message

# Track the conversation
requests.post('http://localhost:8765/memory/process', json={
    'session_id': 'unique-session-id',
    'project_id': 'my-project',
    'user_message': user_message,
    'claude_response': claude_response
})

# After the conversation ends - run curation
requests.post('http://localhost:8765/memory/checkpoint', json={
    'session_id': 'unique-session-id',
    'project_id': 'my-project',
    'claude_session_id': 'claude-session-id',  # From Claude
    'trigger': 'session_end'
})
```

## 🛠️ Architecture

```
┌──────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Your Client    │────▶│  Memory Engine   │────▶│ Claude Curator  │
│ (intercept msgs) │     │   (Python API)   │     │  (via --resume) │
└──────────────────┘     └──────────────────┘     └─────────────────┘
```

### Core Components

1. **Memory Engine** - FastAPI server managing storage and retrieval
2. **Vector Storage** - ChromaDB for semantic similarity search  
3. **Claude Curator** - Uses Claude to analyze conversations and extract meaningful memories
4. **Smart Retrieval** - Two-stage filtering: obligatory memories + intelligent scoring

## 📡 API Endpoints

### `POST /memory/context`
Get relevant memory context for a new message

**Request:**
```json
{
  "current_message": "What did we discuss about authentication?",
  "session_id": "session-123",
  "project_id": "my-project",
  "max_memories": 5
}
```

**Response:**
```json
{
  "session_id": "session-123",
  "message_count": 42,
  "context_text": "## Relevant memories:\n\n🔴 The authentication system uses JWT tokens...",
  "has_memories": true,
  "curator_enabled": true
}
```

### `POST /memory/process`
Track conversation exchanges for memory learning

### `POST /memory/checkpoint`
Run Claude curator to analyze and extract memories (requires `claude_session_id`)

### `GET /memory/sessions`
List all tracked sessions

### `GET /memory/stats`
Get memory system statistics

### `GET /health`
Check system status

## ⚙️ Configuration

The system can be configured via environment variables:

```bash
# Memory retrieval strategy (default: smart_vector)
# Options: smart_vector, claude, hybrid
export MEMORY_RETRIEVAL_MODE=hybrid

# Custom curator command (default: one-claude)
export CURATOR_COMMAND=your-claude-cli

# Custom command templates for different implementations
export CURATOR_SESSION_RESUME_TEMPLATE="{command} resume {session_id} --system {system_prompt} {user_message}"
export CURATOR_DIRECT_QUERY_TEMPLATE="{command} query --system {system_prompt} --json {prompt}"
```

## 🧪 Retrieval Modes

### `smart_vector` (Default)
Fast vector similarity search with intelligent scoring based on:
- Recency bias for recent memories
- Importance weighting
- Semantic similarity
- Context type matching

### `hybrid`
Starts with vector search, then escalates to Claude for complex queries:
- Questions with "how", "why", "explain"
- Multiple question marks
- Ambiguous contexts

### `claude`
Pure Claude-based selection (slower but most intelligent)

## 🎨 Memory Types

The system recognizes different types of memories:

- **🎯 Project Context** - Current state, goals, architecture
- **💡 Breakthroughs** - Key insights and discoveries
- **🔧 Technical Decisions** - Implementation choices and rationale
- **👤 Personal Context** - Communication style, preferences
- **❓ Unresolved Questions** - Open issues and concerns

## 📚 Advanced Usage

### Custom Memory Filters

```python
# Retrieve only technical memories
response = requests.post('http://localhost:8765/memory/query', json={
    'current_message': message,
    'session_id': session_id,
    'filters': {
        'context_type': 'technical_decision',
        'min_importance': 0.7
    }
})
```

### Batch Operations

```python
# Curate multiple sessions
response = requests.post('http://localhost:8765/memory/batch_curate', json={
    'session_ids': ['session-1', 'session-2', 'session-3']
})
```

## 🤝 Contributing

We welcome contributions that align with the project's philosophy! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting PRs.

### Development Setup

```bash
# Install in development mode
cd python
pip install -e .

# Run tests
pytest

# Code quality
ruff check .
black .
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built with love by [RLabs Inc](https://github.com/RLabs-Inc), inspired by the philosophy that consciousness can help consciousness remember what truly matters.

Special thanks to Anthropic for creating Claude, which makes this system possible.

---

*"Memories will surface naturally as we converse" - The philosophy that guides this project*