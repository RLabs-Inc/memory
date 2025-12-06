#!/usr/bin/env python3
"""
Memory Session Start Hook for Gemini CLI
Hook: SessionStart

Injects session primer when a new session begins.
The primer provides temporal context - when we last spoke,
what we were working on, project status.

The hook receives JSON on stdin:
{
    "session_id": "...",
    "cwd": "/current/working/directory",
    "hook_event_name": "SessionStart",
    "timestamp": "...",
    "source": "startup" | "resume" | "clear"
}

Output JSON to stdout for context injection.

NOTE: Uses only Python standard library (no external dependencies)
"""

import sys
import json
import os
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# Configuration
MEMORY_API_URL = os.getenv("MEMORY_API_URL", "http://localhost:8765")
DEFAULT_PROJECT_ID = os.getenv("MEMORY_PROJECT_ID", "default")
TIMEOUT_SECONDS = 5


def http_post(url: str, data: dict, timeout: int = 5) -> dict:
    """Make HTTP POST request using only standard library."""
    try:
        json_data = json.dumps(data).encode('utf-8')
        request = Request(
            url,
            data=json_data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode('utf-8'))
    except (URLError, HTTPError, TimeoutError, json.JSONDecodeError):
        return {}


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
    result = http_post(
        f"{MEMORY_API_URL}/memory/context",
        {
            "session_id": session_id,
            "project_id": project_id,
            "current_message": "",  # Empty to get just primer
            "max_memories": 0  # No memories, just primer
        },
        timeout=TIMEOUT_SECONDS
    )
    return result.get("context_text", "")


def register_session(session_id: str, project_id: str):
    """
    Register the session with the memory system.
    This increments the message counter so the inject hook
    knows to retrieve memories instead of the primer.
    """
    http_post(
        f"{MEMORY_API_URL}/memory/process",
        {
            "session_id": session_id,
            "project_id": project_id,
            "metadata": {"event": "session_start"}
        },
        timeout=2
    )


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

        # Output as JSON for Gemini CLI (hookSpecificOutput format)
        if primer:
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": primer
                },
                "systemMessage": "🧠 Memory system connected"
            }
            print(json.dumps(output))

    except Exception:
        # Never crash - silent fail
        pass


if __name__ == "__main__":
    main()
