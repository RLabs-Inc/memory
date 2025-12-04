# Claude Code Integration

This directory contains everything needed to integrate the Claude Memory System with Claude Code.

## Quick Install

```bash
./install.sh
```

That's it! The script will:
1. Copy memory hooks to `~/.claude/hooks/`
2. Configure Claude Code to use the hooks
3. Verify prerequisites (Python 3, requests package)

## Quick Uninstall

```bash
./uninstall.sh
```

This removes the hooks but preserves your memory database.

## How It Works

The integration uses Claude Code's [hooks system](https://docs.anthropic.com/en/docs/claude-code/hooks) to intercept key events:

### Hooks

| Hook | File | Purpose |
|------|------|---------|
| `SessionStart` | `memory_session_start.py` | Injects session primer (temporal context, last session summary) |
| `UserPromptSubmit` | `memory_inject.py` | Retrieves and injects relevant memories for each message |
| `SessionEnd` | `memory_curate.py` | Triggers memory curation when session ends |
| `PreCompact` | `memory_curate.py` | Triggers curation before context compaction |

### Flow

```
Session Start
    │
    ▼
┌─────────────────────────────────┐
│  SessionStart Hook              │
│  → Get session primer           │
│  → Inject temporal context      │
└─────────────────────────────────┘
    │
    ▼
User sends message
    │
    ▼
┌─────────────────────────────────┐
│  UserPromptSubmit Hook          │
│  → Query memory system          │
│  → Get relevant memories        │
│  → Inject into message context  │
└─────────────────────────────────┘
    │
    ▼
Claude responds (with memory awareness)
    │
    ▼
... more messages ...
    │
    ▼
User exits (/exit or Ctrl+C)
    │
    ▼
┌─────────────────────────────────┐
│  SessionEnd Hook                │
│  → Trigger background curation  │
│  → Claude Code closes instantly │
│  → Memory server curates async  │
└─────────────────────────────────┘
```

## Configuration

### Project-Specific Memory

Create a `.memory-project.json` in your project root:

```json
{
  "project_id": "my-awesome-project"
}
```

This keeps memories isolated per project. Without this file, the directory name is used as the project ID.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MEMORY_API_URL` | `http://localhost:8765` | Memory server URL |
| `MEMORY_PROJECT_ID` | Directory name | Default project ID |

## Viewing Injected Memories

In Claude Code, press `Ctrl+O` to toggle detailed output view. You'll see:
- Injected memories with importance weights
- Hook execution status
- Claude's thinking process

## Troubleshooting

### Memory system not running

```
⚠️ Memory system not available
```

Start the memory server:
```bash
cd /path/to/memory
python3 start_server.py
```

### Hooks not firing

Check that hooks are configured in `~/.claude/settings.json`:
```json
{
  "hooks": {
    "SessionStart": [...],
    "UserPromptSubmit": [...],
    "SessionEnd": [...]
  }
}
```

### View memory server logs

The memory server logs all operations:
```
🎯 Resuming Claude session ... for curation
📂 Working directory: ...
🧠 CLAUDE CURATOR EXTRACTED N MEMORIES:
💎 CURATED MEMORY #1: ...
✅ Checkpoint complete: N memories curated
```

## Files

```
claude-code/
├── hooks/
│   ├── memory_session_start.py  # Session primer injection
│   ├── memory_inject.py         # Memory retrieval & injection
│   └── memory_curate.py         # Session curation trigger
├── install.sh                   # Installation script
├── uninstall.sh                 # Removal script
└── README.md                    # This file
```
