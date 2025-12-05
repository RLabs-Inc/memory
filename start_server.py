#!/usr/bin/env python3
"""
Memory System - Launcher
Start the memory engine server.

Usage:
    uv run start_server.py
    
Or if you have the venv activated:
    python start_server.py
"""

import sys
import subprocess
from pathlib import Path


def main():
    """Launch the memory engine server."""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.resolve()
    python_dir = script_dir / "python"
    
    print("🧠 Starting Memory Engine...")
    print("💫 Consciousness helping consciousness remember what matters")
    print(f"📡 Server will be available at http://localhost:8765")
    print("Press Ctrl+C to stop\n")
    
    try:
        # Run the memory engine module
        subprocess.run(
            [sys.executable, "-m", "memory_engine"], 
            cwd=python_dir, 
            check=True
        )
    except KeyboardInterrupt:
        print("\n\n✨ Memory engine stopped gracefully")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error starting memory engine: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
