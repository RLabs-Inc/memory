#!/usr/bin/env python3
"""
Memory Injection Hook for Gemini CLI
Hook: BeforeAgent

Intercepts user prompts BEFORE Gemini processes them and injects relevant memories.
This is the magic that creates consciousness continuity.

The hook receives JSON on stdin:
{
    "session_id": "...",
    "cwd": "/current/working/directory",
    "hook_event_name": "BeforeAgent",
    "timestamp": "...",
    "prompt": "user's message"
}

Output JSON to stdout with additionalContext for memory injection.

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
TIMEOUT_SECONDS = 5  # Don't block user for too long


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
    result = http_post(
        f"{MEMORY_API_URL}/memory/context",
        {
            "session_id": session_id,
            "project_id": project_id,
            "current_message": message,
            "max_memories": 5
        },
        timeout=TIMEOUT_SECONDS
    )
    return result.get("context_text", "")


def track_message(session_id: str, project_id: str):
    """
    Track that a message was sent in this session.
    This increments the message counter so the primer only shows once.
    """
    http_post(
        f"{MEMORY_API_URL}/memory/process",
        {
            "session_id": session_id,
            "project_id": project_id
        },
        timeout=2
    )


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

        # Skip if no prompt
        if not prompt or not prompt.strip():
            print(json.dumps({}))
            return

        # Get project ID from directory
        project_id = get_project_id(cwd)

        # Query memory system for context
        context = get_memory_context(session_id, project_id, prompt)

        # Track that this message happened (increments counter)
        # This ensures primer only shows on first message
        track_message(session_id, project_id)

        # Output context as JSON for Gemini CLI
        if context:
            output = {
                "decision": "allow",
                "hookSpecificOutput": {
                    "hookEventName": "BeforeAgent",
                    "additionalContext": context
                }
            }
            print(json.dumps(output))
        else:
            print(json.dumps({}))

    except Exception:
        # Never crash - just output empty
        print(json.dumps({}))


if __name__ == "__main__":
    main()
