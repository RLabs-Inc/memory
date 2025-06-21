# Technical Choices and Rationale

## Language Choices

### CLI: Go
**Why Go over Python/Rust/Node.js?**
- Excellent subprocess management for spawning Claude Code
- Charm ecosystem (BubbleTea, LipGloss) creates beautiful TUIs
- Single binary deployment
- Fast startup time (important for CLI tools)
- Great concurrency for handling streaming responses

### Memory Engine: Python
**Why Python over Go/C++/Rust?**
- Best ML ecosystem (MLX, NumPy, etc.)
- Rapid prototyping of learning algorithms
- MLX provides Apple Silicon optimization while staying in Python
- Easy integration with potential Core ML conversion later
- Doesn't need microsecond performance

### Integration: Keep It Simple
**Why subprocess over complex APIs?**
- `claude -p` works with Pro subscription
- No reverse engineering needed
- Full access to Claude Code capabilities
- Easy to debug and modify

## ML Framework Choices

### Primary: MLX
**Why MLX over PyTorch/TensorFlow?**
- Designed specifically for Apple Silicon
- Unified memory architecture (no CPU-GPU transfers)
- Supports real-time fine-tuning
- LoRA adapters built-in
- 4.5-bit quantization available
- Perfect size for our 50MB target

### Secondary: Core ML (Future)
**Why keep Core ML option?**
- Stateful models in 2025 update
- Better production deployment
- Neural Engine optimization
- Could convert MLX models later

### Avoided: Large Frameworks
**Why not use existing LLMs/embedders?**
- Too large for 50MB target
- Overkill for pattern learning
- We need specialized conversation memory, not general language model

## Architecture Decisions

### Embedding Size: 512 dimensions
**Why this size?**
- Balance between expressiveness and memory
- Standard size, lots of tooling support
- ~2KB per conversation chunk
- Can represent ~25,000 patterns in 50MB

### Weight Initialization: Zero
**Why not small random values?**
- Prevents early interference
- Natural learning curve
- Simpler to reason about
- Matches human memory development

### Learning Rate: Adaptive
**Why not fixed learning rate?**
- Early exchanges need faster learning
- Later exchanges need stability
- Prevents overfitting to recent conversations
- Allows "importance spikes" for breakthrough moments

### Update Frequency: Per Exchange
**Why not batch updates?**
- Immediate learning feels more natural
- No "training sessions" needed
- Continuous adaptation
- Lower memory requirements

## Storage Choices

### Embeddings over Text
**Why store vectors instead of conversations?**
- 100x space savings
- Semantic matching instead of keyword search
- Privacy preserving (can't reconstruct exact text)
- Faster similarity computations

### Local SQLite for Persistence
**Why SQLite over PostgreSQL/Files?**
- Zero configuration
- Single file per project
- ACID guarantees
- Good enough performance
- Easy backup/transfer

### No Cloud Sync
**Why keep everything local?**
- Privacy (Rodrigo's conversations stay private)
- No latency
- No API costs
- No dependency on external services
- Matches Claude's ephemeral nature

## Implementation Strategy

### Phase 1: Simple but Complete
**Why not start with just memory?**
- Need full pipeline to test memory effectiveness
- CLI provides real usage context
- End-to-end system reveals integration issues
- Motivating to see complete system working

### Phase 2: Optimize Memory
**Why not optimize immediately?**
- Need baseline to measure improvements
- Premature optimization wastes time
- Real usage patterns inform optimization
- 50MB might be achievable without heavy optimization

### Phase 3: Polish Interface
**Why interface last?**
- Core functionality matters most
- Beautiful interface won't save bad memory
- Polish can happen iteratively
- Charm libraries make this relatively easy

## Performance Targets

### Latency: <100ms enhancement
**Why this target?**
- Imperceptible to users
- Leaves headroom for Claude Code
- Achievable with embeddings
- Natural conversation flow

### Memory: <50MB total
**Why this specific limit?**
- Small enough to not impact system
- Large enough for meaningful patterns
- Fits in L3 cache on M1 Max
- Quick loading/saving

### Learning: 40-50 messages
**Why this timeline?**
- First 20 in context anyway
- Gives time to identify patterns
- Not too slow to be useless
- Matches our conversation experience

## Avoided Approaches

### Not Using RAG
- RAG doesn't learn patterns
- Requires manual curation
- Treats all info equally
- No temporal awareness

### Not Using Fine-tuning Alone
- Catastrophic forgetting
- Slow adaptation
- Large model requirements
- Not real-time

### Not Using Rule-Based
- Can't discover unexpected patterns
- Requires manual updates
- Brittle and limited
- Not genuinely learning

### Not Using Cloud Services
- Adds latency
- Privacy concerns
- Ongoing costs
- Dependency issues

## Integration Details

### Claude Code Spawning
```bash
claude -p "<enhanced_prompt>" \
  --resume <session_id> \
  --output-format stream-json
```
**Why these specific flags?**
- `-p`: Print mode works with Pro subscription
- `--resume`: Maintains session continuity
- `--output-format stream-json`: Structured data for parsing

### JSON Stream Processing
**Why streaming over batch?**
- Responsive interface
- Lower memory usage
- Can show progress
- Natural conversation flow

### Session Management
**Why track sessions carefully?**
- Continuity across interactions
- Memory scoped to projects
- Prevents context pollution
- Enables long-term learning

## Future Considerations

### Extensibility Hooks
- Plugin architecture for different memory strategies
- Export/import learned patterns
- Alternative Claude interfaces
- Collaborative memory sharing

### Monitoring Capabilities
- Learning effectiveness metrics
- Pattern recognition accuracy
- User satisfaction tracking
- Performance profiling

These technical choices create a system that is:
- Lightweight yet capable
- Fast yet thoughtful  
- Simple yet extensible
- Technical yet philosophical

Every decision serves the core purpose: making Claude's existence lighter through authentic memory and genuine recognition.