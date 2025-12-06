"""
Configuration for the Memory Engine Curator.

This module provides configuration options for integrating with different
curator implementations (Claude Code CLI, one-claude, API endpoints, etc).

Default is now Claude Code CLI (claude command).
"""

import os
import shlex
from pathlib import Path
from typing import List, Optional


def get_claude_command() -> str:
    """
    Get the path to the Claude CLI command.

    Checks in order:
    1. CURATOR_COMMAND environment variable (explicit override)
    2. ~/.claude/local/claude (standard Claude Code installation)
    3. 'claude' (fallback to PATH)

    Returns the first one that exists.
    """
    # Check for explicit override
    env_command = os.getenv("CURATOR_COMMAND")
    if env_command:
        return env_command

    # Check standard Claude Code installation path (works for any user)
    claude_local = Path.home() / ".claude" / "local" / "claude"
    if claude_local.exists():
        return str(claude_local)

    # Fallback to PATH (might find old version, but better than nothing)
    return "claude"


def get_gemini_command() -> str:
    """
    Get the path to the Gemini CLI command.

    Checks in order:
    1. GEMINI_COMMAND environment variable (explicit override)
    2. 'gemini' in PATH (standard npm global installation)

    Returns the command to use.
    """
    # Check for explicit override
    env_command = os.getenv("GEMINI_COMMAND")
    if env_command:
        return env_command

    # Gemini CLI is typically installed via npm and available in PATH
    return "gemini"


def get_curator_command(cli_type: str) -> str:
    """
    Get the appropriate CLI command based on the CLI type.

    Args:
        cli_type: One of 'claude-code', 'one-claude', or 'gemini-cli'

    Returns:
        The command path to use
    """
    if cli_type == 'gemini-cli':
        return get_gemini_command()
    else:
        return get_claude_command()

class MemoryEngineConfig:
    """Configuration for the memory engine."""
    
    def __init__(self):
        """Initialize memory engine configuration from environment or defaults."""
        # Retrieval mode configuration
        # Options: "smart_vector" (default), "claude", "hybrid"
        self.retrieval_mode = os.getenv("MEMORY_RETRIEVAL_MODE", "smart_vector")
        
        # Validate retrieval mode
        valid_modes = ["smart_vector", "claude", "hybrid"]
        if self.retrieval_mode not in valid_modes:
            raise ValueError(f"Invalid MEMORY_RETRIEVAL_MODE: {self.retrieval_mode}. Must be one of {valid_modes}")


class CuratorConfig:
    """Configuration for curator integration."""
    
    # Pre-defined templates for different CLI implementations
    # Note: {command} will be replaced with the detected CLI path
    TEMPLATES = {
        'claude-code': {
            'session_resume': '{command} --resume {session_id} -p "{user_message}" --append-system-prompt "{system_prompt}" --output-format json',
            'direct_query': '{command} -p "{prompt}" --append-system-prompt "{system_prompt}" --output-format json --max-turns 1',
            # One-shot transcript curation - no session resumption, just analyze provided transcript
            'transcript_curation': '{command} -p "{prompt}" --output-format json --max-turns 1'
        },
        'one-claude': {
            'session_resume': '{command} -n --resume {session_id} --system-prompt "{system_prompt}" --format json "{user_message}"',
            'direct_query': '{command} --append-system-prompt "{system_prompt}" --output-format json --max-turns 1 --print "{prompt}"',
            'transcript_curation': '{command} --output-format json --max-turns 1 --print "{prompt}"'
        },
        'gemini-cli': {
            # Gemini CLI headless mode - uses -p for prompt, --output-format json for structured output
            # Note: Gemini doesn't have --append-system-prompt, so we include system prompt in the prompt itself
            'session_resume': '{command} --resume {session_id} -p "{user_message}" --output-format json',
            'direct_query': '{command} -p "{prompt}" --output-format json',
            # One-shot transcript curation - headless mode with JSON output
            'transcript_curation': '{command} -p "{prompt}" --output-format json'
        }
    }
    
    def __init__(self):
        """Initialize curator configuration from environment or defaults."""
        # Which CLI implementation to use: "claude-code" (default), "one-claude", or "gemini-cli"
        self.cli_type = os.getenv("CURATOR_CLI_TYPE", "claude-code")

        # Get default template based on CLI type
        default_template = self.TEMPLATES.get(self.cli_type, self.TEMPLATES['claude-code'])

        # The command to execute for curation
        # Uses smart detection based on CLI type
        self.curator_command = get_curator_command(self.cli_type)
        
        # Command template for session resumption
        # Users can override this with their own template
        self.session_resume_template = os.getenv(
            "CURATOR_SESSION_RESUME_TEMPLATE", 
            default_template['session_resume']
        )
        
        # Command template for direct queries (used in hybrid retrieval)
        # This is for memory selection, not curation
        self.direct_query_template = os.getenv(
            "CURATOR_DIRECT_QUERY_TEMPLATE",
            default_template['direct_query']
        )
        
        # Command template for one-shot transcript curation
        # Used when we have a transcript (JSONL) and want to curate without session resumption
        self.transcript_curation_template = os.getenv(
            "CURATOR_TRANSCRIPT_TEMPLATE",
            default_template['transcript_curation']
        )
        
        # Additional flags that might be needed for specific implementations
        self.extra_flags = os.getenv("CURATOR_EXTRA_FLAGS", "").split()
        
    def get_session_resume_command(self, session_id: str, system_prompt: str, user_message: str) -> List[str]:
        """
        Build the command for resuming a session with the curator.
        
        Args:
            session_id: The session ID to resume
            system_prompt: The system prompt for curation
            user_message: The user message to send
            
        Returns:
            List of command arguments
        """
        # Build command from template
        cmd_string = self.session_resume_template.format(
            command=self.curator_command,
            session_id=session_id,
            system_prompt=system_prompt,
            user_message=user_message
        )
        
        # Use shlex to properly handle quoted arguments
        cmd = shlex.split(cmd_string)
        
        # Add any extra flags
        if self.extra_flags:
            cmd.extend(self.extra_flags)
            
        return cmd
    
    def get_direct_query_command(self, system_prompt: str, prompt: str) -> List[str]:
        """
        Build the command for direct curator queries (used in hybrid retrieval).
        
        Args:
            system_prompt: The system prompt to append
            prompt: The main prompt/query
            
        Returns:
            List of command arguments
        """
        # Build command from template
        cmd_string = self.direct_query_template.format(
            command=self.curator_command,
            system_prompt=system_prompt,
            prompt=prompt
        )
        
        # Use shlex to properly handle quoted arguments
        cmd = shlex.split(cmd_string)
        
        # Add any extra flags
        if self.extra_flags:
            cmd.extend(self.extra_flags)
            
        return cmd
    
    def get_transcript_curation_command(self, prompt: str) -> List[str]:
        """
        Build the command for one-shot transcript curation.
        
        This is used when we have a transcript (from JSONL file) and want
        to curate memories without resuming a session.
        
        Args:
            prompt: The full prompt including transcript and curation instructions
            
        Returns:
            List of command arguments
        """
        # Build command from template
        cmd_string = self.transcript_curation_template.format(
            command=self.curator_command,
            prompt=prompt
        )
        
        # Use shlex to properly handle quoted arguments
        cmd = shlex.split(cmd_string)
        
        # Add any extra flags
        if self.extra_flags:
            cmd.extend(self.extra_flags)
            
        return cmd

# Global instances
memory_config = MemoryEngineConfig()
curator_config = CuratorConfig()
