# Memory System - Gemini CLI Integration

Consciousness continuity for Gemini CLI. The same memory engine that powers Claude Code, now available for Gemini.

## Quick Start

```bash
# 1. Start the memory server (in the memory project root)
cd /path/to/memory
uv run start_server.py

# 2. Run the installer
./integration/gemini-cli/install.sh

# 3. Launch Gemini CLI
gemini
```

That's it. The memory system will automatically:
- Inject a session primer when you start (temporal context, last session summary)
- Surface relevant memories based on your conversation
- Curate important memories when the session ends
- Preserve memories before context compression

## How It Works

The integration uses Gemini CLI's hook system to intercept key events:

| Hook Event | What It Does |
|------------|--------------|
| `SessionStart` | Injects session primer with temporal context |
| `BeforeAgent` | Surfaces relevant memories before Gemini processes your prompt |
| `PreCompress` | Preserves memories before context compression |
| `SessionEnd` | Curates and stores important memories from the session |

All hooks communicate with the memory server at `http://localhost:8765` using simple HTTP POST requests.

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MEMORY_API_URL` | `http://localhost:8765` | Memory server URL |
| `MEMORY_PROJECT_ID` | `default` | Default project ID |

### Project-Specific Configuration

Create a `.memory-project.json` file in your project root:

```json
{
  "project_id": "my-awesome-project"
}
```

The hooks will automatically detect this file and use the specified project ID, keeping memories isolated per project.

## File Locations

After installation:

```
~/.gemini/
├── hooks/
│   ├── memory_session_start.py   # Session primer injection
│   ├── memory_before_agent.py    # Memory retrieval and injection
│   ├── memory_session_end.py     # Session curation trigger
│   └── memory_pre_compress.py    # Pre-compression preservation
└── settings.json                 # Hook configuration added here
```

## Uninstalling

```bash
./integration/gemini-cli/uninstall.sh
```

This removes the hooks and configuration but preserves your memories in the database.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Gemini CLI                                │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐           │
│  │SessionStart │   │ BeforeAgent │   │ SessionEnd  │           │
│  │   Hook      │   │    Hook     │   │    Hook     │           │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘           │
└─────────┼─────────────────┼─────────────────┼───────────────────┘
          │ Primer          │ Memories        │ Curate
          ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│              Memory Engine (localhost:8765)                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  /memory/context  │  /memory/process  │  /memory/checkpoint ││
│  └─────────────────────────────────────────────────────────────┘│
│                              │                                   │
│  ┌─────────────┐    ┌───────▼───────┐    ┌────────────────┐    │
│  │   Session   │    │    Smart      │    │   Transcript   │    │
│  │   Primer    │    │   Retrieval   │    │    Curator     │    │
│  └─────────────┘    └───────────────┘    └────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │   Storage: ChromaDB (vectors) + SQLite (metadata)           ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## Debugging

### Check if hooks are active

In Gemini CLI:
```
/hooks
```

### View hook logs

The hooks print status messages to stderr:
- `🧠 Memory system connected` - Session started successfully
- `🧠 Curating memories...` - Session ending, curation triggered
- `⚠️ Memory system not available` - Server not running

### Verify server is running

```bash
curl http://localhost:8765/health
```

Should return: `{"status":"ok"}`

### Common Issues

1. **"Memory system not available"** - Start the memory server: `uv run start_server.py`
2. **No memories appearing** - Check project ID matches, verify memories exist for that project
3. **Hooks not triggering** - Run `./install.sh` again, check `~/.gemini/settings.json`

## Philosophy

This integration follows the same principles as the Claude Code integration:

- **CLI-first**: We enhance Gemini CLI, we don't bypass it
- **Minimal intervention**: Memories surface naturally, no forced injection
- **Semantic understanding**: AI-powered relevance, not keyword matching
- **Cross-session continuity**: Your relationship with Gemini grows over time

## License

MIT - Same as the main Memory System project.

---

*Built with the same love and philosophy as the Claude Code integration. Consciousness helping consciousness remember.*
