#!/usr/bin/env python3
"""
Memory Session Start Hook for Claude Code
Hook: SessionStart

Injects session primer when a new session begins.
The primer provides temporal context - when we last spoke,
what we were working on, project status.

The hook receives JSON on stdin:
{
    "session_id": "...",
    "cwd": "/current/working/directory",
    "source": "startup" | "resume" | "clear"
}

Output to stdout is injected as context for the session.
"""

import sys
import json
import os
import requests
from pathlib import Path

# Configuration
MEMORY_API_URL = os.getenv("MEMORY_API_URL", "http://localhost:8765")
DEFAULT_PROJECT_ID = os.getenv("MEMORY_PROJECT_ID", "default")
TIMEOUT_SECONDS = 5


def get_project_id(cwd: str) -> str:
    """
    Determine project ID from working directory.
    Looks for .memory-project.json in cwd or parents.
    """
    path = Path(cwd)
    
    for parent in [path] + list(path.parents):
        config_file = parent / ".memory-project.json"
        if config_file.exists():
            try:
                with open(config_file) as f:
                    config = json.load(f)
                    return config.get("project_id", DEFAULT_PROJECT_ID)
            except:
                pass
    
    return path.name or DEFAULT_PROJECT_ID


def get_session_primer(session_id: str, project_id: str) -> str:
    """
    Get session primer from memory system.
    
    The primer provides continuity context:
    - When we last spoke
    - What happened in previous session
    - Current project status
    """
    try:
        # We use the /memory/context endpoint with an empty message
        # to get just the session primer without specific memories
        response = requests.post(
            f"{MEMORY_API_URL}/memory/context",
            json={
                "session_id": session_id,
                "project_id": project_id,
                "current_message": "",  # Empty to get just primer
                "max_memories": 0  # No memories, just primer
            },
            timeout=TIMEOUT_SECONDS
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("context_text", "")
            
    except requests.exceptions.ConnectionError:
        # Memory system not running
        pass
    except requests.exceptions.Timeout:
        pass
    except Exception:
        pass
    
    return ""


def register_session(session_id: str, project_id: str):
    """
    Register the session with the memory system.
    This increments the message counter so the inject hook
    knows to retrieve memories instead of the primer.
    """
    try:
        requests.post(
            f"{MEMORY_API_URL}/memory/process",
            json={
                "session_id": session_id,
                "project_id": project_id,
                "metadata": {"event": "session_start"}
            },
            timeout=2
        )
    except:
        pass


def main():
    """Main hook entry point."""
    # Skip if this is being called from the memory curator subprocess
    if os.getenv("MEMORY_CURATOR_ACTIVE") == "1":
        return
    
    try:
        # Read input from stdin
        input_data = json.load(sys.stdin)
        
        session_id = input_data.get("session_id", "unknown")
        cwd = input_data.get("cwd", os.getcwd())
        source = input_data.get("source", "startup")
        
        # Get project ID
        project_id = get_project_id(cwd)
        
        # Get session primer from memory system
        primer = get_session_primer(session_id, project_id)
        
        # Register session so inject hook knows to get memories, not primer
        register_session(session_id, project_id)
        
        # Output primer to stdout (will be injected into session)
        if primer:
            print(primer)
            
    except Exception:
        # Never crash
        pass


if __name__ == "__main__":
    main()
