#!/usr/bin/env python3
"""
Memory Curation Hook for Claude Code
Hooks: SessionEnd, PreCompact

Triggers memory curation when a session ends or before compaction.
Fire-and-forget approach - user sees immediate feedback,
curation happens in background.
"""

import sys
import json
import os
import requests
from pathlib import Path

# Configuration  
MEMORY_API_URL = os.getenv("MEMORY_API_URL", "http://localhost:8765")
DEFAULT_PROJECT_ID = os.getenv("MEMORY_PROJECT_ID", "default")
TRIGGER_TIMEOUT = 5  # Just enough to send the request


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


def trigger_curation_async(session_id, project_id, trigger, cwd):
    """Trigger curation - fire and forget style."""
    try:
        # Very short timeout - we just need to send the request
        # The server will process it even after we disconnect
        response = requests.post(
            f"{MEMORY_API_URL}/memory/checkpoint",
            json={
                "session_id": session_id,
                "project_id": project_id,
                "trigger": trigger,
                "claude_session_id": session_id,
                "cwd": cwd
            },
            timeout=2  # Just enough to send, not wait for completion
        )
        return True
    except requests.exceptions.Timeout:
        return True  # Request was sent, server is processing
    except requests.exceptions.ConnectionError:
        return False  # Server not running
    except:
        return False


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
