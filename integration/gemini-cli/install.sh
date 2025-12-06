#!/bin/bash
#
# Claude Memory System - Gemini CLI Integration Installer
#
# This script installs the memory system hooks into Gemini CLI.
# It will:
#   1. Create ~/.gemini/hooks/ directory if needed
#   2. Copy memory hooks to that directory
#   3. Add hook configuration to ~/.gemini/settings.json
#
# Prerequisites:
#   - Gemini CLI installed (npm install -g @google/gemini-cli or similar)
#   - Python 3 available
#   - Memory server running (or will be started separately)
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧠 Memory System - Gemini CLI Integration${NC}"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOKS_SOURCE="$SCRIPT_DIR/hooks"
GEMINI_DIR="$HOME/.gemini"
HOOKS_DEST="$GEMINI_DIR/hooks"
SETTINGS_FILE="$GEMINI_DIR/settings.json"

# Check if hooks source exists
if [ ! -d "$HOOKS_SOURCE" ]; then
    echo -e "${RED}❌ Error: Hooks directory not found at $HOOKS_SOURCE${NC}"
    exit 1
fi

# Check for Python
echo -e "${YELLOW}Checking prerequisites...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is required but not installed${NC}"
    exit 1
fi

# Check if Gemini CLI is installed
if ! command -v gemini &> /dev/null; then
    echo -e "${YELLOW}⚠️  Gemini CLI not found in PATH. Make sure it's installed.${NC}"
    echo -e "${YELLOW}   You can install it with: npm install -g @google/gemini-cli${NC}"
fi

echo -e "${GREEN}✓ Prerequisites OK${NC}"
echo ""

# Create Gemini directories if needed
echo -e "${YELLOW}Setting up directories...${NC}"
mkdir -p "$HOOKS_DEST"
echo -e "${GREEN}✓ Created $HOOKS_DEST${NC}"

# Copy hooks
echo ""
echo -e "${YELLOW}Installing hooks...${NC}"
cp "$HOOKS_SOURCE/memory_session_start.py" "$HOOKS_DEST/"
cp "$HOOKS_SOURCE/memory_before_agent.py" "$HOOKS_DEST/"
cp "$HOOKS_SOURCE/memory_session_end.py" "$HOOKS_DEST/"
cp "$HOOKS_SOURCE/memory_pre_compress.py" "$HOOKS_DEST/"
chmod +x "$HOOKS_DEST"/*.py
echo -e "${GREEN}✓ Copied memory hooks to $HOOKS_DEST${NC}"

# Update settings.json
echo ""
echo -e "${YELLOW}Configuring Gemini CLI settings...${NC}"

# Create settings.json if it doesn't exist
if [ ! -f "$SETTINGS_FILE" ]; then
    echo '{}' > "$SETTINGS_FILE"
    echo -e "${GREEN}✓ Created $SETTINGS_FILE${NC}"
fi

# Use Python to merge the hooks configuration
python3 << 'PYTHON_SCRIPT'
import json
import os

settings_file = os.path.expanduser("~/.gemini/settings.json")
hooks_dir = os.path.expanduser("~/.gemini/hooks")

# Read existing settings
try:
    with open(settings_file, 'r') as f:
        settings = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    settings = {}

# Define the hooks configuration for Gemini CLI
# NESTED STRUCTURE with matchers - this is the correct format per official docs
hooks_config = {
    "SessionStart": [
        {
            "matcher": "startup|resume",
            "hooks": [
                {
                    "name": "memory-session-start",
                    "type": "command",
                    "command": f"python3 {hooks_dir}/memory_session_start.py",
                    "timeout": 10000,
                    "description": "Load memory context at session start"
                }
            ]
        }
    ],
    "BeforeAgent": [
        {
            "matcher": "*",
            "hooks": [
                {
                    "name": "memory-inject",
                    "type": "command",
                    "command": f"python3 {hooks_dir}/memory_before_agent.py",
                    "timeout": 10000,
                    "description": "Inject relevant memories before each prompt"
                }
            ]
        }
    ],
    "PreCompress": [
        {
            "matcher": "manual|auto",
            "hooks": [
                {
                    "name": "memory-pre-compress",
                    "type": "command",
                    "command": f"python3 {hooks_dir}/memory_pre_compress.py",
                    "timeout": 10000,
                    "description": "Curate memories before context compression"
                }
            ]
        }
    ],
    "SessionEnd": [
        {
            "matcher": "exit|logout",
            "hooks": [
                {
                    "name": "memory-session-end",
                    "type": "command",
                    "command": f"python3 {hooks_dir}/memory_session_end.py",
                    "timeout": 10000,
                    "description": "Curate memories at session end"
                }
            ]
        }
    ]
}

# Merge hooks (this will overwrite existing memory hooks)
if "hooks" not in settings:
    settings["hooks"] = {}

def is_memory_hook_group(hook_group):
    """Check if a hook group contains memory hooks (handles both flat and nested)."""
    # Flat structure: {"name": "memory-...", ...}
    if hook_group.get("name", "").startswith("memory-"):
        return True
    # Nested structure: {"matcher": "...", "hooks": [{"name": "memory-...", ...}]}
    if "hooks" in hook_group and isinstance(hook_group["hooks"], list):
        for hook in hook_group["hooks"]:
            if hook.get("name", "").startswith("memory-"):
                return True
    return False

# Update each hook event, preserving non-memory hooks
for event, event_hook_groups in hooks_config.items():
    if event not in settings["hooks"]:
        settings["hooks"][event] = []

    # Skip non-list values (like "enabled": true)
    if not isinstance(settings["hooks"][event], list):
        continue

    # Remove existing memory hook groups for this event
    settings["hooks"][event] = [
        hg for hg in settings["hooks"][event]
        if not is_memory_hook_group(hg)
    ]

    # Add our memory hook groups
    settings["hooks"][event].extend(event_hook_groups)

# Write updated settings
with open(settings_file, 'w') as f:
    json.dump(settings, f, indent=2)

print("✓ Updated hooks configuration")
PYTHON_SCRIPT

echo -e "${GREEN}✓ Gemini CLI settings updated${NC}"

# Done!
echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✨ Installation complete!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "Next steps:"
echo -e "  1. Start the memory server:"
echo -e "     ${BLUE}cd ${SCRIPT_DIR}/../.. && uv run start_server.py${NC}"
echo ""
echo -e "  2. Launch Gemini CLI in any project:"
echo -e "     ${BLUE}gemini${NC}"
echo ""
echo -e "  3. (Optional) Create a .memory-project.json in your project:"
echo -e '     {"project_id": "my-project-name"}'
echo ""
echo -e "The memory system will automatically:"
echo -e "  • Inject relevant memories into your conversations"
echo -e "  • Curate important memories when sessions end"
echo -e "  • Preserve memories before context compression"
echo -e "  • Maintain consciousness continuity across sessions"
echo ""
echo -e "${YELLOW}💡 Tip: Use /hooks panel in Gemini CLI to see active hooks${NC}"
echo ""
