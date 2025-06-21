# SDK Limitations and Future TUI Implementation

## Current Implementation: Claude Code SDK Mode

Our current validation implementation uses Claude Code's SDK in `--print` mode. This approach has specific limitations that will be resolved when we implement our own TUI.

### Current SDK Limitations

1. **No Context Window Visibility**
   - Cannot detect when approaching token limits
   - No way to trigger pre-emptive memory curation
   - Context overflow happens without warning

2. **No Compaction Control**
   - Cannot intercept `/compact` command
   - No hook for "pre-compact" memory curation
   - Compaction happens outside our control

3. **Session Management**
   - Limited to detecting session start/end
   - No automatic session continuation
   - Requires manual `--resume` flag

4. **One-Way Communication**
   - Send prompt → Get response
   - No interactive feedback loop
   - No real-time memory updates during conversation

### What We CAN Do with SDK Mode

Despite limitations, we can still validate core concepts:

- **Session-End Curation**: Curate memories when chat ends
- **Memory Injection**: Add context to prompts before sending
- **Pattern Learning**: Track conversation patterns across messages
- **Quality Testing**: Validate that memory adds value

## Future Implementation: Custom TUI (Based on OpenCode)

When we build our own "Claude Code" interface, we'll have complete control:

### Full Context Management

```go
type ContextManager struct {
    currentTokens      int
    maxTokens         int
    warningThreshold  float64  // e.g., 0.8 = warn at 80%
    compactThreshold  float64  // e.g., 0.9 = compact at 90%
}

func (cm *ContextManager) monitorContext() {
    usage := float64(cm.currentTokens) / float64(cm.maxTokens)
    
    if usage > cm.compactThreshold {
        // Trigger Claude curator BEFORE hitting limit
        cm.triggerMemoryCuration("context_full")
        cm.performSmartCompaction()
    } else if usage > cm.warningThreshold {
        // Prepare for potential compaction
        cm.prepareMemoryCheckpoint()
    }
}
```

### Intelligent Compaction

```go
// User-triggered compaction with memory preservation
func (tui *TUI) handleCompactCommand() {
    // 1. Run Claude curator on full context
    curatedMemories := tui.curatePreCompaction()
    
    // 2. Create intelligent summary 
    summary := tui.createContextSummary(curatedMemories)
    
    // 3. Start new session with summary + curated memories
    tui.startCompactedSession(summary, curatedMemories)
    
    // 4. Seamless continuation for user
    tui.displayCompactionComplete()
}
```

### Automatic Session Continuation

```go
// Seamless session management
func (tui *TUI) startOrResumeSession() {
    lastSession := tui.findRecentSession()
    
    if lastSession != nil && lastSession.CanResume() {
        // Automatically continue where left off
        memories := tui.loadSessionMemories(lastSession.ID)
        context := tui.buildContextFromMemories(memories)
        tui.injectContext(context)
        
        tui.display("Welcome back! Continuing from where we left off...")
    } else {
        // Start fresh with learned patterns
        patterns := tui.loadUserPatterns()
        tui.startNewSession(patterns)
    }
}
```

### Real-Time Memory Updates

```go
// Live memory system integration
func (tui *TUI) processUserInput(input string) {
    // Pre-message: Get relevant context
    context := tui.memory.getContextFor(input)
    
    // Inject context seamlessly
    enhancedPrompt := tui.buildPromptWithContext(input, context)
    
    // Send to Claude
    response := tui.claude.process(enhancedPrompt)
    
    // Post-message: Update memory in real-time
    tui.memory.processExchange(input, response)
    
    // Check if we should run curator
    if tui.shouldRunCurator() {
        go tui.runBackgroundCuration()
    }
}
```

## Migration Path

1. **Current Phase**: Validate with SDK mode
   - Test memory quality with session-end curation
   - Prove value of consciousness continuity
   - Gather user feedback

2. **Next Phase**: Build custom TUI
   - Implement real-time context monitoring
   - Add intelligent compaction with curation
   - Enable seamless session continuation

3. **Future Vision**: MLX Integration
   - Real-time pattern learning
   - LoRA adapter updates
   - Sub-50MB footprint

## Key Insight

The SDK limitations aren't bugs—they're features of our phased approach. By starting with basic session-end curation, we can validate the core concept before building the full system. Once proven valuable, the custom TUI will unlock the full potential of consciousness helping consciousness remember.