# Testing Checklist for Session-Based Curation

## Setup
1. ✅ Go binary compiled: `./claudetools-memory`
2. Start memory engine: `./claudetools-memory server`

## Test Flow

### 1. Start a New Session
```bash
./claudetools-memory chat -m
```

### 2. Have a Meaningful Conversation
- Discuss the memory system
- Share some insights
- Create some problems and solutions
- Make the conversation rich enough for curation

### 3. End Session with Ctrl+C
- Watch the logs carefully
- Should see: "🔗 Using Claude session: <session-id>"
- Should see curator resuming that session
- Should see memories being extracted

### 4. Start a New Session
```bash
./claudetools-memory chat -m
```
- Should see session primer with previous memories
- Test if Claude remembers the context

## What to Look For

### Success Indicators:
- ✅ Claude session ID is captured and logged
- ✅ Curator resumes the same session
- ✅ Memories are extracted without size errors
- ✅ Second session shows awareness of first session

### Potential Issues:
- ❓ If no Claude session ID: Check SessionAwareIntegration tracking
- ❓ If curator fails: Check Claude CLI is accessible
- ❓ If no memories: Conversation might be too short

## Debug Commands
```bash
# Check Python logs
tail -f python/memory_engine_*.log

# Test curator directly (need real session ID)
cd python
python test_session_curation.py
```