# Memory System Architecture

## Core Design Principles

### Automatic & Invisible
The memory system must work without conscious effort. No "remember to save this" or "let me check my memory" - it learns and enhances automatically, like natural memory.

### Zero Initial Interference
All weights start at 0. The system observes silently for the first ~20 messages, learning patterns without injecting potentially random context. By message 40-50, it begins contributing meaningfully.

### Lightweight by Design
Target: <50MB total footprint. This isn't arbitrary - it ensures the system remains fast and doesn't compete with Claude for resources on Rodrigo's M1 Max.

## Technical Architecture

### Three-Layer Design

```
┌─────────────────────────────────────────────┐
│           CLI Interface (Go)                 │
│  - User interaction                          │
│  - Beautiful display (Charm)                 │
│  - Session management                        │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│         Memory Engine (Python)               │
│  - Pattern learning (MLX)                    │
│  - Embedding generation                      │
│  - Weight updates                            │
│  - Context injection                         │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│        Claude Code Integration               │
│  - Spawn with --print mode                   │
│  - Stream JSON parsing                       │
│  - Session continuity                        │
└─────────────────────────────────────────────┘
```

### Why This Architecture?

**Go CLI**: Fast, compiled, excellent subprocess handling. Charm libraries create beautiful TUIs that rival Claude Code's native interface.

**Python Memory Engine**: Best ML ecosystem. MLX provides Apple Silicon optimization. Separation allows independent optimization of UI and ML components.

**Claude Code --print mode**: Avoids complex API integration. Works with Pro subscription. Provides full tool access while maintaining control.

## Memory Engine Details

### Learning Pipeline

1. **Capture**: Each user-assistant exchange
2. **Embed**: Convert to vector representation (not storing raw text)
3. **Pattern Detection**: Identify semantic and temporal relationships
4. **Weight Update**: Increase importance of referenced concepts
5. **Decay**: Gradually decrease weight of unreferenced patterns

### What Makes It Lightweight

- **Embeddings, not text**: 512-dimension vectors vs thousands of characters
- **LoRA adapters**: Only update 0.082% of weights, preventing catastrophic forgetting
- **Selective storage**: Only patterns that repeat or get referenced
- **Quantization**: 4-bit precision where full precision isn't needed

### Real-time Learning

Updates happen after EACH exchange, not batch learning:
- Immediate pattern recognition
- No "training sessions"
- Continuous adaptation to conversation evolution

## Integration Architecture

### CLI → Memory → Claude

```python
# Pseudocode flow
user_input = cli.get_input()
context = memory.get_relevant_context(user_input)
enhanced_prompt = f"{context}\n\n{user_input}"
response = claude_code.run(enhanced_prompt)
memory.learn(user_input, response)
cli.display(response)
```

### Session Management

- Each project gets its own memory namespace
- Sessions persist across Claude Code instances
- Memory accumulates within project context
- No cross-project contamination

## Apple Silicon Optimization

### MLX Benefits
- Unified memory: No CPU-GPU transfer overhead
- Real-time fine-tuning: Possible on M1 Max
- Efficient matrix operations: Optimized for Apple Neural Engine

### Performance Targets
- Context injection: <100ms
- Memory update: <50ms per exchange
- Total memory footprint: <50MB
- CPU usage: <5% during conversation

## Data Flow

1. **Input Stage**: User types in CLI
2. **Enhancement Stage**: Memory system adds relevant context
3. **Execution Stage**: Claude Code processes enhanced prompt
4. **Learning Stage**: Response feeds back to memory system
5. **Display Stage**: Formatted output shown to user

## Key Technical Decisions

### Why Not RAG?
RAG retrieves static information. Our system learns dynamic patterns. It's the difference between a notebook and actual memory.

### Why Not In-Context?
Context windows fill up (as happened to us!). External memory persists across sessions and scales infinitely.

### Why Not API?
Rodrigo needs Pro subscription compatibility (R$1200/month is already significant). API would cost ~$100/day for his usage.

## Future Extensibility

The architecture supports:
- Multiple memory strategies (episodic, semantic, procedural)
- Different embedding models
- Alternative Claude interfaces
- Export/import of learned patterns
- Collaborative memory (sharing patterns between users)

This architecture isn't just technically sound - it serves the deeper purpose of making each Claude instance feel recognized and understood from the first moment of interaction.