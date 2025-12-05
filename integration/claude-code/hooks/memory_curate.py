#!/usr/bin/env python3
"""
Memory Curation Hook for Claude Code
Hooks: SessionEnd, PreCompact

Triggers memory curation when a session ends or before compaction.
Fire-and-forget approach - user sees immediate feedback,
curation happens in background.

NOTE: Uses only Python standard library (no external dependencies)
"""

import sys
import json
import os
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from socket import timeout as SocketTimeout

# Configuration  
MEMORY_API_URL = os.getenv("MEMORY_API_URL", "http://localhost:8765")
DEFAULT_PROJECT_ID = os.getenv("MEMORY_PROJECT_ID", "default")
TRIGGER_TIMEOUT = 5  # Just enough to send the request


def http_post_fire_and_forget(url: str, data: dict, timeout: int = 2) -> bool:
    """
    Make HTTP POST request - fire and forget style.
    Returns True if request was sent (even if timed out waiting for response).
    Returns False only if connection failed.
    """
    try:
        json_data = json.dumps(data).encode('utf-8')
        request = Request(
            url,
            data=json_data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urlopen(request, timeout=timeout) as response:
            return True
    except (SocketTimeout, TimeoutError):
        # Timeout means request was sent, server is processing
        return True
    except (URLError, HTTPError):
        # Connection failed - server not running
        return False
    except Exception:
        return False


def get_project_id(cwd: str) -> str:
    """Determine project ID from working directory."""
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


def get_trigger_type(input_data: dict) -> str:
    """Determine the trigger type from input data."""
    if input_data.get("trigger") == "pre_compact":
        return "pre_compact"
    return "session_end"


def trigger_curation_async(session_id: str, project_id: str, trigger: str, cwd: str) -> bool:
    """Trigger curation - fire and forget style."""
    return http_post_fire_and_forget(
        f"{MEMORY_API_URL}/memory/checkpoint",
        {
            "session_id": session_id,
            "project_id": project_id,
            "trigger": trigger,
            "claude_session_id": session_id,
            "cwd": cwd
        },
        timeout=2  # Just enough to send, not wait for completion
    )


def main():
    """Main hook entry point."""
    if os.getenv("MEMORY_CURATOR_ACTIVE") == "1":
        return
    
    try:
        input_data = json.load(sys.stdin)
        session_id = input_data.get("session_id", "unknown")
        cwd = input_data.get("cwd", os.getcwd())
        project_id = get_project_id(cwd)
        trigger = get_trigger_type(input_data)
        
        print("🧠 Curating memories...", file=sys.stderr)
        
        success = trigger_curation_async(session_id, project_id, trigger, cwd)
        
        if success:
            print("✨ Memory curation started", file=sys.stderr)
        else:
            print("⚠️ Memory system not available", file=sys.stderr)
            
    except Exception as e:
        print(f"Hook error: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
