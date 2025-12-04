#!/bin/bash
#
# Claude Memory System - Claude Code Integration Uninstaller
#
# This script removes the memory system hooks from Claude Code.
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🧠 Claude Memory System - Uninstaller${NC}"
echo ""

CLAUDE_DIR="$HOME/.claude"
HOOKS_DIR="$CLAUDE_DIR/hooks"
SETTINGS_FILE="$CLAUDE_DIR/settings.json"

# Remove hook files
echo -e "${YELLOW}Removing hook files...${NC}"
rm -f "$HOOKS_DIR/memory_session_start.py"
rm -f "$HOOKS_DIR/memory_inject.py"
rm -f "$HOOKS_DIR/memory_curate.py"
echo -e "${GREEN}✓ Removed memory hooks${NC}"

# Update settings.json to remove hook configuration
echo ""
echo -e "${YELLOW}Updating Claude Code settings...${NC}"

if [ -f "$SETTINGS_FILE" ]; then
    python3 << 'PYTHON_SCRIPT'
import json
import os

settings_file = os.path.expanduser("~/.claude/settings.json")

try:
    with open(settings_file, 'r') as f:
        settings = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    settings = {}

# Remove memory-related hooks
if "hooks" in settings:
    for hook_type in ["SessionStart", "UserPromptSubmit", "PreCompact", "SessionEnd"]:
        if hook_type in settings["hooks"]:
            # Filter out memory hooks
            settings["hooks"][hook_type] = [
                h for h in settings["hooks"][hook_type]
                if not any("memory_" in str(hook.get("command", "")) 
                          for hook in h.get("hooks", []))
            ]
            # Remove empty arrays
            if not settings["hooks"][hook_type]:
                del settings["hooks"][hook_type]
    
    # Remove hooks key if empty
    if not settings["hooks"]:
        del settings["hooks"]

with open(settings_file, 'w') as f:
    json.dump(settings, f, indent=2)

print("✓ Removed hooks from settings")
PYTHON_SCRIPT
    echo -e "${GREEN}✓ Settings updated${NC}"
else
    echo -e "${YELLOW}⚠ No settings file found${NC}"
fi

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✨ Uninstallation complete!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "The memory hooks have been removed from Claude Code."
echo -e "Your memory database is preserved at:"
echo -e "  ${BLUE}./memory.db${NC} and ${BLUE}./memory_vectors/${NC}"
echo ""
echo -e "To reinstall, run: ${BLUE}./install.sh${NC}"
echo ""
