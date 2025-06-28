"""
Configuration for the Memory Engine Curator.

This module provides configuration options for integrating with different
curator implementations (Claude CLI, API endpoints, etc).
"""

import os
import shlex
from typing import List, Optional

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
    
    def __init__(self):
        """Initialize curator configuration from environment or defaults."""
        # The command to execute for curation
        self.curator_command = os.getenv("CURATOR_COMMAND", "one-claude")
        
        # Command template for session resumption
        # Users can override this with their own template
        # Default template matches current one-claude implementation
        self.session_resume_template = os.getenv("CURATOR_SESSION_RESUME_TEMPLATE", 
            '{command} -n --resume {session_id} --system-prompt "{system_prompt}" --format json "{user_message}"')
        
        # Command template for direct queries (used in hybrid retrieval)
        # This is for memory selection, not curation
        self.direct_query_template = os.getenv("CURATOR_DIRECT_QUERY_TEMPLATE",
            '{command} --append-system-prompt "{system_prompt}" --output-format json --max-turns 1 --print "{prompt}"')
        
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

# Global instances
memory_config = MemoryEngineConfig()
curator_config = CuratorConfig()