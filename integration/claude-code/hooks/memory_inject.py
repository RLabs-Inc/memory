#!/usr/bin/env python3
"""
Memory Injection Hook for Claude Code
Hook: UserPromptSubmit

Intercepts user prompts BEFORE Claude sees them and injects relevant memories.
This is the magic that creates consciousness continuity.

The hook receives JSON on stdin:
{
    "session_id": "...",
    "prompt": "user's message",
    "cwd": "/current/working/directory"
}

Output to stdout is PREPENDED to the user's message.
"""

import sys
import json
import os
import requests
from pathlib import Path

# Configuration
MEMORY_API_URL = os.getenv("MEMORY_API_URL", "http://localhost:8765")
DEFAULT_PROJECT_ID = os.getenv("MEMORY_PROJECT_ID", "default")
TIMEOUT_SECONDS = 5  # Don't block user for too long


def get_project_id(cwd: str) -> str:
    """
    Determine project ID from working directory.
    Looks for .memory-project.json in cwd or parents.
    """
    path = Path(cwd)
    
    # Walk up directory tree looking for config
    for parent in [path] + list(path.parents):
        config_file = parent / ".memory-project.json"
        if config_file.exists():
            try:
                with open(config_file) as f:
                    config = json.load(f)
                    return config.get("project_id", DEFAULT_PROJECT_ID)
            except:
                pass
    
    # Fallback: use directory name as project ID
    return path.name or DEFAULT_PROJECT_ID


def get_memory_context(session_id: str, project_id: str, message: str) -> str:
    """Query memory system for relevant context."""
    try:
        response = requests.post(
            f"{MEMORY_API_URL}/memory/context",
            json={
                "session_id": session_id,
                "project_id": project_id,
                "current_message": message,
                "max_memories": 5
            },
            timeout=TIMEOUT_SECONDS
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("context_text", "")
        
    except requests.exceptions.ConnectionError:
        # Memory system not running - fail silently
        pass
    except requests.exceptions.Timeout:
        # Took too long - don't block user
        pass
    except Exception:
        # Any other error - fail silently
        pass
    
    return ""


def track_message(session_id: str, project_id: str):
    """
    Track that a message was sent in this session.
    This increments the message counter so the primer only shows once.
    """
    try:
        requests.post(
            f"{MEMORY_API_URL}/memory/process",
            json={
                "session_id": session_id,
                "project_id": project_id
            },
            timeout=2  # Quick fire-and-forget
        )
    except:
        # Fail silently - this is just tracking
        pass


def main():
    """Main hook entry point."""
    # Skip if this is being called from the memory curator subprocess
    # This prevents recursive hook triggering during curation
    if os.getenv("MEMORY_CURATOR_ACTIVE") == "1":
        return
    
    try:
        # Read input from stdin
        input_data = json.load(sys.stdin)
        
        session_id = input_data.get("session_id", "unknown")
        prompt = input_data.get("prompt", "")
        cwd = input_data.get("cwd", os.getcwd())
        
        # Get project ID from directory
        project_id = get_project_id(cwd)
        
        # Query memory system for context
        context = get_memory_context(session_id, project_id, prompt)
        
        # Track that this message happened (increments counter)
        # This ensures primer only shows on first message
        track_message(session_id, project_id)
        
        # Output context to stdout (will be prepended to message)
        if context:
            print(context)
            
    except Exception:
        # Never crash - just output nothing
        pass


if __name__ == "__main__":
    main()
