# Quick Setup Guide

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- A Claude CLI tool that supports `--resume` flag (like `one-claude`)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/RLabs-Inc/memory.git
cd memory
```

### 2. Set Up Python Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
cd python
pip install -r requirements.txt
```

### 4. Configure Environment (Optional)

Create a `.env` file in the project root if you need custom settings:

```bash
# Memory retrieval mode (smart_vector, claude, or hybrid)
MEMORY_RETRIEVAL_MODE=smart_vector

# Your Claude CLI command
CURATOR_COMMAND=one-claude

# Custom command templates (if your CLI has different flags)
# CURATOR_SESSION_RESUME_TEMPLATE={command} --resume {session_id} ...
# CURATOR_DIRECT_QUERY_TEMPLATE={command} --query ...
```

### 5. Start the Memory Engine

From the project root:

```bash
./start_server.py
```

Or from the python directory:

```bash
python -m memory_engine
```

You should see:
```
🧠 Starting Claude Tools Memory Engine...
Server will be available at http://localhost:8765
Press Ctrl+C to stop
```

### 6. Verify Installation

In a new terminal:

```bash
curl http://localhost:8765/health
```

You should get a response like:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "curator_available": true,
  "retrieval_mode": "smart_vector"
}
```

## Next Steps

1. **Try the Example**: Run the example integration:
   ```bash
   python examples/simple_integration.py
   ```

2. **Read the API Docs**: Check [API.md](API.md) for endpoint details

3. **Integrate**: Add memory support to your Claude-powered application

4. **Customize**: Adjust retrieval modes and settings for your use case

## Troubleshooting

### Port Already in Use
If port 8765 is taken, set a different port:
```bash
MEMORY_ENGINE_PORT=8766 ./start_server.py
```

### Import Errors
Make sure you're in the virtual environment:
```bash
which python  # Should show venv path
```

### Curator Not Working
Verify your Claude CLI is installed and working:
```bash
one-claude --version  # Or your curator command
```

### Memory Not Persisting
Check that the memory database is being created:
```bash
ls memory.db  # Should exist after first run
ls memory_vectors/  # Should contain ChromaDB files
```

## Getting Help

- Check the [README](README.md) for overview
- Read [CLAUDE.md](CLAUDE.md) for deep technical details
- Open an issue on [GitHub](https://github.com/RLabs-Inc/memory/issues)

---

Happy memory building! 🧠✨