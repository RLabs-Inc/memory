#!/bin/bash
#
# Claude Memory System - Gemini CLI Integration Uninstaller
#
# This script removes the memory system hooks from Gemini CLI.
# It will:
#   1. Remove memory hooks from ~/.gemini/hooks/
#   2. Remove hook configuration from ~/.gemini/settings.json
#
# Your memories in the database are NOT deleted.
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧠 Claude Memory System - Gemini CLI Uninstaller${NC}"
echo ""

GEMINI_DIR="$HOME/.gemini"
HOOKS_DIR="$GEMINI_DIR/hooks"
SETTINGS_FILE="$GEMINI_DIR/settings.json"

# Check if Gemini directory exists
if [ ! -d "$GEMINI_DIR" ]; then
    echo -e "${YELLOW}⚠️  Gemini CLI directory not found at $GEMINI_DIR${NC}"
    echo -e "${YELLOW}   Nothing to uninstall.${NC}"
    exit 0
fi

# Remove hook files
echo -e "${YELLOW}Removing hook files...${NC}"
HOOKS_REMOVED=0

for hook_file in memory_session_start.py memory_before_agent.py memory_session_end.py memory_pre_compress.py; do
    if [ -f "$HOOKS_DIR/$hook_file" ]; then
        rm "$HOOKS_DIR/$hook_file"
        echo -e "${GREEN}✓ Removed $hook_file${NC}"
        ((HOOKS_REMOVED++))
    fi
done

if [ $HOOKS_REMOVED -eq 0 ]; then
    echo -e "${YELLOW}   No hook files found${NC}"
fi

# Update settings.json to remove memory hooks
echo ""
echo -e "${YELLOW}Updating Gemini CLI settings...${NC}"

if [ -f "$SETTINGS_FILE" ]; then
    # Use Python to remove the memory hooks from settings
    python3 << 'PYTHON_SCRIPT'
import json
import os

settings_file = os.path.expanduser("~/.gemini/settings.json")

try:
    with open(settings_file, 'r') as f:
        settings = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    print("No settings to update")
    exit(0)

if "hooks" not in settings:
    print("No hooks configuration found")
    exit(0)

modified = False

def is_memory_hook(hook_obj):
    """Check if a hook object is a memory hook (handles both flat and nested structures)"""
    # Flat structure: {"name": "memory-...", ...}
    if hook_obj.get("name", "").startswith("memory-"):
        return True
    # Old nested structure: {"matcher": "...", "hooks": [{"name": "memory-...", ...}]}
    if "hooks" in hook_obj and isinstance(hook_obj["hooks"], list):
        for nested_hook in hook_obj["hooks"]:
            if nested_hook.get("name", "").startswith("memory-"):
                return True
    return False

# Remove memory hooks from each event
# Skip non-array values like "enabled": true
for event in list(settings["hooks"].keys()):
    value = settings["hooks"][event]

    # Skip non-list values (like "enabled": true)
    if not isinstance(value, list):
        continue

    original_len = len(value)

    # Filter out memory hooks (handles both flat and nested structures)
    settings["hooks"][event] = [
        h for h in value
        if not is_memory_hook(h)
    ]

    if len(settings["hooks"][event]) != original_len:
        modified = True

    # Remove empty event arrays
    if not settings["hooks"][event]:
        del settings["hooks"][event]

# Check if only "enabled" key remains (or empty)
remaining_keys = [k for k in settings["hooks"].keys() if k != "enabled"]
if not remaining_keys:
    del settings["hooks"]
    modified = True

if modified:
    with open(settings_file, 'w') as f:
        json.dump(settings, f, indent=2)
    print("✓ Removed memory hooks from settings")
else:
    print("No memory hooks found in settings")

PYTHON_SCRIPT

    echo -e "${GREEN}✓ Settings updated${NC}"
else
    echo -e "${YELLOW}   No settings file found${NC}"
fi

# Done!
echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✨ Uninstallation complete!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Note: Your memories are still preserved in the database.${NC}"
echo -e "${YELLOW}To reinstall later: ./install.sh${NC}"
echo ""
