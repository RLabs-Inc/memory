# Quick Setup Guide

## Prerequisites

- **uv** - Modern Python package manager (recommended)
- Python 3.12+ (uv will install this automatically if needed)
- A Claude CLI tool that supports `--resume` flag (like Claude Code)

## Installation Steps

### 1. Install uv (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone the Repository

```bash
git clone https://github.com/RLabs-Inc/memory.git
cd memory
```

### 3. Install Dependencies

```bash
uv sync
```

That's it! uv automatically:
- Creates a virtual environment (`.venv`)
- Installs Python 3.12 if needed
- Installs all dependencies including `claude-agent-sdk`

### 4. Start the Memory Engine

```bash
uv run start_server.py
```

You should see:
```
🧠 Starting Memory Engine...
💫 Consciousness helping consciousness remember what matters
📡 Server will be available at http://localhost:8765
...
INFO:     Uvicorn running on http://127.0.0.1:8765 (Press CTRL+C to quit)
```

### 5. Verify Installation

In a new terminal:

```bash
curl http://localhost:8765/health
```

You should get:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "curator_available": true,
  "retrieval_mode": "smart_vector"
}
```

## Alternative: Using the Entry Point

After `uv sync`, you can also run:

```bash
uv run memory-server
```

## Common Commands

```bash
# Start server
uv run start_server.py

# Run with development dependencies
uv sync --group dev

# Add a new dependency
uv add <package-name>

# Update dependencies
uv sync --upgrade

# Run tests
uv run pytest

# Run linter
uv run ruff check python/
```

## Environment Variables (Optional)

Create a `.env` file for custom settings:

```bash
# Memory retrieval mode (smart_vector, claude, or hybrid)
MEMORY_RETRIEVAL_MODE=smart_vector

# Custom curator CLI (defaults to Claude Code)
CURATOR_COMMAND=/path/to/your/claude

# CLI type for command templates
CURATOR_CLI_TYPE=claude-code  # or "one-claude"
```

## Next Steps

1. **Try the Example**: 
   ```bash
   uv run python examples/simple_integration.py
   ```

2. **Read the API Docs**: Check [API.md](API.md) for endpoint details

3. **Integrate**: Add memory support to your Claude-powered application

## Troubleshooting

### Port Already in Use
The server runs on port 8765 by default. If it's taken:
```bash
# Check what's using the port
lsof -i :8765

# Kill if needed
kill -9 <PID>
```

### uv Not Found
Make sure uv is in your PATH:
```bash
export PATH="$HOME/.local/bin:$PATH"
```

### Import Errors
Run `uv sync` to ensure all dependencies are installed.

### Curator Not Working
Verify Claude Code is installed:
```bash
claude --version
```

## Getting Help

- Check the [README](README.md) for overview
- Read [CLAUDE.md](CLAUDE.md) for deep technical details
- Open an issue on [GitHub](https://github.com/RLabs-Inc/memory/issues)

---

Happy memory building! 🧠✨
