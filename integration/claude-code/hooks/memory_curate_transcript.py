#!/usr/bin/env python3
"""
Memory Curation Hook using Transcript (NEW approach)
Hook: PreCompact

Uses the new /memory/curate-transcript endpoint that reads the JSONL
transcript file directly, rather than resuming a Claude session.

This is the transcript-based approach - we read the conversation from
the transcript file and use Claude Agent SDK to curate memories.

NOTE: Uses only Python standard library (no external dependencies)
"""

import sys
import json
import os
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import socket

# Configuration
MEMORY_API_URL = os.getenv("MEMORY_API_URL", "http://localhost:8765")
DEFAULT_PROJECT_ID = os.getenv("MEMORY_PROJECT_ID", "default")
CURATION_METHOD = os.getenv("MEMORY_CURATION_METHOD", "sdk")  # sdk or cli


def get_project_id(cwd: str) -> str:
    """Determine project ID from working directory."""
    path = Path(cwd)
    
    # Look for .memory-project.json in current or parent directories
    for parent in [path] + list(path.parents):
        config_file = parent / ".memory-project.json"
        if config_file.exists():
            try:
                with open(config_file) as f:
                    config = json.load(f)
                    return config.get("project_id", DEFAULT_PROJECT_ID)
            except:
                pass
    
    # Default to directory name
    return path.name or DEFAULT_PROJECT_ID


def expand_transcript_path(transcript_path: str) -> str:
    """Expand ~ in transcript path to full path."""
    if transcript_path.startswith("~"):
        return os.path.expanduser(transcript_path)
    return transcript_path


def trigger_transcript_curation(transcript_path: str, session_id: str, project_id: str, trigger: str):
    """
    Call the new /memory/curate-transcript endpoint.
    
    This endpoint reads the transcript file directly and uses
    Claude Agent SDK to curate memories.
    """
    try:
        # Expand ~ to full path
        full_path = expand_transcript_path(transcript_path)
        
        # Verify file exists before calling API
        if not os.path.exists(full_path):
            print(f"⚠️ Transcript file not found: {full_path}", file=sys.stderr)
            return False
        
        # Prepare request
        json_data = json.dumps({
            "transcript_path": full_path,
            "project_id": project_id,
            "session_id": session_id,
            "trigger": trigger,
            "curation_method": CURATION_METHOD
        }).encode('utf-8')
        
        request = Request(
            f"{MEMORY_API_URL}/memory/curate-transcript",
            data=json_data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        with urlopen(request, timeout=120) as response:  # Curation can take time
            result = json.loads(response.read().decode('utf-8'))
        
        if response.status == 200:
            memories_count = result.get("memories_curated", 0)
            summary = result.get("session_summary", "")
            
            if memories_count > 0:
                print(f"✨ Curated {memories_count} memories", file=sys.stderr)
                if summary:
                    print(f"📝 {summary[:100]}...", file=sys.stderr)
            else:
                print("📭 No memories to curate", file=sys.stderr)
            
            return True
        else:
            print(f"⚠️ Curation failed: {response.status}", file=sys.stderr)
            return False
            
    except socket.timeout:
        print("⏳ Curation in progress (timed out waiting)", file=sys.stderr)
        return True  # Request was sent
    except URLError as e:
        if isinstance(e.reason, socket.timeout):
            print("⏳ Curation in progress (timed out waiting)", file=sys.stderr)
            return True  # Request was sent
        print("⚠️ Memory server not running", file=sys.stderr)
        return False
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return False


def main():
    """Main hook entry point."""
    # Prevent recursive curation
    if os.getenv("MEMORY_CURATOR_ACTIVE") == "1":
        return
    
    try:
        # Read hook input from stdin
        input_data = json.load(sys.stdin)
        
        # Extract data from hook input
        session_id = input_data.get("session_id", "unknown")
        transcript_path = input_data.get("transcript_path", "")
        cwd = input_data.get("cwd", os.getcwd())
        trigger = input_data.get("trigger", "pre_compact")
        hook_event = input_data.get("hook_event_name", "PreCompact")
        
        # Determine project ID
        project_id = get_project_id(cwd)
        
        # Validate we have a transcript path
        if not transcript_path:
            print("⚠️ No transcript path in hook input", file=sys.stderr)
            return
        
        print(f"🧠 Curating memories from transcript ({hook_event})...", file=sys.stderr)
        
        # Call the new transcript-based curation endpoint
        success = trigger_transcript_curation(
            transcript_path=transcript_path,
            session_id=session_id,
            project_id=project_id,
            trigger="pre_compact" if hook_event == "PreCompact" else "session_end"
        )
        
        if not success:
            print("⚠️ Memory curation unavailable", file=sys.stderr)
            
    except json.JSONDecodeError:
        print("❌ Invalid JSON input", file=sys.stderr)
    except Exception as e:
        print(f"❌ Hook error: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
