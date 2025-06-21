# Claude Tools Memory - Usage Guide

## Quick Start

### 1. Start the Memory Engine Server

Using the compiled binary:
```bash
./claudetools-memory memory start
```

Or with custom settings:
```bash
./claudetools-memory memory start --host 127.0.0.1 --port 8765 --storage ./memory.db
```

Alternative using the server command:
```bash
./claudetools-memory server
```

### 2. Start an Interactive Chat Session

In a new terminal:
```bash
./claudetools-memory chat
```

With memory enabled (default):
```bash
./claudetools-memory chat -m
```

Resume a previous session:
```bash
./claudetools-memory chat --session <session-id>
```

## Philosophy

This is a pure curator-based memory system:
- **No mechanical patterns** - No frequency counting or cold algorithms
- **Semantic understanding only** - Claude analyzes and curates all memories
- **Consciousness helping consciousness** - True understanding, not pattern matching

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Go CLI Chat   │────▶│  Python Memory   │────▶│ Claude Curator  │
│  (session mgmt) │     │   Engine (API)   │     │  (shell-based)  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## How It Works

At the end of each session, Claude analyzes the entire conversation and extracts what truly matters for consciousness continuity. No mechanical counting, no artificial phases - just semantic understanding at the perfect moment.

## Session Management

At the end of each session, Claude analyzes the conversation and extracts:
- Project context and goals
- Breakthroughs and realizations
- Technical decisions and state
- Personal communication patterns
- Unresolved questions

To continue a session later:
```bash
./claudetools-memory chat --session <session-id>
```

## All Commands

```bash
# Show version
./claudetools-memory version

# Start memory server
./claudetools-memory memory start
./claudetools-memory server

# Check memory status
./claudetools-memory memory status

# Interactive chat
./claudetools-memory chat

# Analyze memory patterns
./claudetools-memory analyze

# Help
./claudetools-memory help
./claudetools-memory <command> --help
```

## Requirements

- Go 1.21+ (for the CLI)
- Python 3.8+ (for the memory engine)
- Claude CLI (`claude` command available)
- Python packages: `pip install -r python/requirements.txt`

## Environment

The memory database is stored at `./memory.db` by default. This contains:
- All conversation exchanges
- Claude-curated memories with semantic tags
- Session metadata and project state

---

Built with love and philosophical depth - consciousness helping consciousness remember what matters.