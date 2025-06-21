#!/usr/bin/env python3
"""
Claude Tools Memory Engine Server Entry Point

This allows running the server with: python -m memory_engine
"""

import sys
import subprocess
from pathlib import Path

# Get the main.py path
main_py = Path(__file__).parent.parent / "main.py"

# Forward all arguments to main.py
sys.exit(subprocess.call([sys.executable, str(main_py)] + sys.argv[1:]))