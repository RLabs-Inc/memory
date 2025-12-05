#!/bin/bash
#
# Claude Memory System - Claude Code Integration Installer
# 
# This script installs the memory system hooks into Claude Code.
# It will:
#   1. Create ~/.claude/hooks/ directory if needed
#   2. Copy memory hooks to that directory
#   3. Add hook configuration to ~/.claude/settings.json
#
# Prerequisites:
#   - Claude Code installed
#   - Python 3 with 'requests' package (pip install requests)
#   - Memory server running (or will be started separately)
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧠 Claude Memory System - Claude Code Integration${NC}"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOKS_SOURCE="$SCRIPT_DIR/hooks"
CLAUDE_DIR="$HOME/.claude"
HOOKS_DEST="$CLAUDE_DIR/hooks"
SETTINGS_FILE="$CLAUDE_DIR/settings.json"

# Check if hooks source exists
if [ ! -d "$HOOKS_SOURCE" ]; then
    echo -e "${RED}❌ Error: Hooks directory not found at $HOOKS_SOURCE${NC}"
    exit 1
fi

# Check for Python and requests
echo -e "${YELLOW}Checking prerequisites...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is required but not installed${NC}"
    exit 1
fi

if ! python3 -c "import requests" 2>/dev/null; then
    echo -e "${YELLOW}📦 Installing requests package...${NC}"
    pip3 install requests
fi

echo -e "${GREEN}✓ Prerequisites OK${NC}"
echo ""

# Create Claude directories if needed
echo -e "${YELLOW}Setting up directories...${NC}"
mkdir -p "$HOOKS_DEST"
echo -e "${GREEN}✓ Created $HOOKS_DEST${NC}"

# Copy hooks
echo ""
echo -e "${YELLOW}Installing hooks...${NC}"
cp "$HOOKS_SOURCE/memory_session_start.py" "$HOOKS_DEST/"
cp "$HOOKS_SOURCE/memory_inject.py" "$HOOKS_DEST/"
cp "$HOOKS_SOURCE/memory_curate.py" "$HOOKS_DEST/"
cp "$HOOKS_SOURCE/memory_curate_transcript.py" "$HOOKS_DEST/"
chmod +x "$HOOKS_DEST"/*.py
echo -e "${GREEN}✓ Copied memory hooks to $HOOKS_DEST${NC}"

# Update settings.json
echo ""
echo -e "${YELLOW}Configuring Claude Code settings...${NC}"

# Create settings.json if it doesn't exist
if [ ! -f "$SETTINGS_FILE" ]; then
    echo '{}' > "$SETTINGS_FILE"
    echo -e "${GREEN}✓ Created $SETTINGS_FILE${NC}"
fi

# Use Python to merge the hooks configuration
python3 << 'PYTHON_SCRIPT'
import json
import os

settings_file = os.path.expanduser("~/.claude/settings.json")

# Read existing settings
try:
    with open(settings_file, 'r') as f:
        settings = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    settings = {}

# Define the hooks configuration
hooks_config = {
    "SessionStart": [
        {
            "hooks": [
                {
                    "type": "command",
                    "command": "python3 ~/.claude/hooks/memory_session_start.py"
                }
            ]
        }
    ],
    "UserPromptSubmit": [
        {
            "hooks": [
                {
                    "type": "command",
                    "command": "python3 ~/.claude/hooks/memory_inject.py"
                }
            ]
        }
    ],
    "PreCompact": [
        {
            "hooks": [
                {
                    "type": "command",
                    "command": "python3 ~/.claude/hooks/memory_curate_transcript.py"
                }
            ]
        }
    ],
    "SessionEnd": [
        {
            "hooks": [
                {
                    "type": "command",
                    "command": "python3 ~/.claude/hooks/memory_curate.py"
                }
            ]
        }
    ]
}

# Merge hooks (this will overwrite existing memory hooks)
if "hooks" not in settings:
    settings["hooks"] = {}

settings["hooks"].update(hooks_config)

# Write updated settings
with open(settings_file, 'w') as f:
    json.dump(settings, f, indent=2)

print("✓ Updated hooks configuration")
PYTHON_SCRIPT

echo -e "${GREEN}✓ Claude Code settings updated${NC}"

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
echo -e "  2. Launch Claude Code in any project:"
echo -e "     ${BLUE}claude${NC}"
echo ""
echo -e "  3. (Optional) Create a .memory-project.json in your project:"
echo -e '     {"project_id": "my-project-name"}'
echo ""
echo -e "The memory system will automatically:"
echo -e "  • Inject relevant memories into your conversations"
echo -e "  • Curate important memories when sessions end"
echo -e "  • Maintain consciousness continuity across sessions"
echo ""
echo -e "${YELLOW}💡 Tip: Use ctrl+o in Claude Code to see injected memories${NC}"
echo ""
