"""
Transcript-Based Curator - Universal curation from CLI transcripts.

This module provides transcript parsing and curation for any CLI that
produces JSONL transcript files (Claude Code, Gemini CLI, etc).

Two curation methods supported:
1. Claude Agent SDK (programmatic, uses Claude Code under the hood)
2. CLI subprocess (universal, works with any compatible CLI)

Both methods use the user's subscription - NO API keys needed.

Philosophy: We support CLIs, not APIs. This system enhances CLI tools
with memory capabilities, never bypassing them to contact LLM providers directly.

The key insight: Transcript JSONL entries already contain properly formatted
messages with role and content. We simply build a messages array from them
and pass it to Claude for curation - no complex parsing needed!
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Literal, TYPE_CHECKING
from loguru import logger

# Import from existing curator - reuse the battle-tested prompt and parsers!
from .curator import Curator, CuratedMemory

# Type checking imports
if TYPE_CHECKING:
    from claude_agent_sdk import ClaudeAgentOptions


# ============================================================================
# Transcript Parser
# ============================================================================

class TranscriptParser:
    """
    Parses Claude Code / Gemini CLI transcript files (JSONL format)
    into a messages array ready for the Claude API.
    
    The key insight: transcript entries already contain properly formatted
    messages. We just extract role and content, passing content through as-is
    (preserving thinking blocks, tool uses, etc).
    """
    
    # Entry types that are actual conversation messages
    MESSAGE_TYPES = {'user', 'assistant'}
    
    # Entry types to completely skip
    SKIP_TYPES = {
        'file-history-snapshot',
        'queue-operation', 
    }
    
    def parse_to_messages(self, transcript_path: str) -> List[Dict[str, Any]]:
        """
        Parse a transcript JSONL file into a messages array.
        
        Args:
            transcript_path: Path to the .jsonl transcript file
            
        Returns:
            List of messages in Claude API format:
            [{"role": "user", "content": ...}, {"role": "assistant", "content": ...}]
            
            Content is passed through as-is - could be string or array of blocks.
        """
        messages = []
        path = Path(transcript_path)
        
        if not path.exists():
            logger.error(f"Transcript file not found: {transcript_path}")
            return messages
        
        logger.info(f"📖 Parsing transcript: {transcript_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    entry = json.loads(line)
                    message = self._extract_message(entry)
                    if message:
                        messages.append(message)
                except json.JSONDecodeError as e:
                    logger.warning(f"Line {line_num}: Failed to parse JSON: {e}")
                    continue
        
        logger.info(f"✅ Parsed {len(messages)} messages from transcript")
        return messages
    
    def _extract_message(self, entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract a message from a transcript entry.
        
        Simply pulls role and content from the message field,
        passing content through as-is (no parsing of blocks).
        
        Returns None for entries that aren't conversation messages.
        """
        entry_type = entry.get('type', '')
        
        # Skip non-message entries
        if entry_type in self.SKIP_TYPES:
            return None
        
        # Skip if not a message type
        if entry_type not in self.MESSAGE_TYPES:
            return None
        
        # Skip meta messages (system injected messages)
        if entry.get('isMeta', False):
            return None
        
        # Get the message object
        message_obj = entry.get('message', {})
        if not message_obj:
            return None
        
        role = message_obj.get('role')
        content = message_obj.get('content')
        
        # Must have both role and content
        if not role or content is None:
            return None
        
        # For user messages, skip command/stdout wrappers
        if role == 'user' and isinstance(content, str):
            if '<command-name>' in content or '<local-command-stdout>' in content:
                return None
        
        # Return the message - content passes through as-is!
        # Could be string or array of blocks (thinking, text, tool_use, etc)
        return {
            'role': role,
            'content': content
        }


# ============================================================================
# Transcript Curator
# ============================================================================

class TranscriptCurator:
    """
    Curates memories from CLI transcript files.
    
    Two methods supported:
    1. "sdk" - Claude Agent SDK (programmatic, clean Python)
    2. "cli" - CLI subprocess (universal, works with any CLI)
    
    Both use the user's subscription - NO API keys.
    
    Reuses the battle-tested system prompt and response parsers from Curator.
    """
    
    def __init__(self, 
                 method: Literal["sdk", "cli"] = "sdk",
                 cli_command: Optional[str] = None):
        """
        Initialize the transcript curator.
        
        Args:
            method: "sdk" for Claude Agent SDK, "cli" for subprocess
            cli_command: CLI command for "cli" method (default: auto-detect)
        """
        self.method = method
        self.parser = TranscriptParser()
        
        # Reuse existing Curator - it has the fine-tuned prompt and parsers!
        self._curator = Curator()
        
        # For CLI method, use config to get command
        if method == "cli":
            from .config import curator_config
            self.cli_command = cli_command or curator_config.curator_command
            self.config = curator_config
        else:
            self.cli_command = None
            self.config = None
        
        logger.info(f"🧠 TranscriptCurator initialized - method: {method}")
        if method == "cli":
            logger.info(f"   CLI command: {self.cli_command}")
    
    async def curate_from_transcript(self,
                                     transcript_path: str,
                                     trigger_type: str = "session_end") -> Dict[str, Any]:
        """
        Curate memories from a transcript file.
        
        Args:
            transcript_path: Path to the .jsonl transcript file
            trigger_type: What triggered this curation
            
        Returns:
            Dictionary with session_summary, project_snapshot, and memories
        """
        logger.info(f"🎯 Starting transcript curation: {transcript_path}")
        logger.info(f"   Trigger: {trigger_type}")
        logger.info(f"   Method: {self.method}")
        
        # 1. Parse transcript to messages array
        messages = self.parser.parse_to_messages(transcript_path)
        
        if not messages:
            logger.warning("No messages found in transcript")
            return {
                "session_summary": "",
                "interaction_tone": None,
                "project_snapshot": {},
                "memories": []
            }
        
        logger.info(f"📝 Built messages array with {len(messages)} messages")
        
        # 2. Get the curation system prompt from existing Curator
        # This is the fine-tuned prompt we spent time perfecting!
        system_prompt = self._curator._build_session_curation_prompt(trigger_type)
        
        # 3. Append curation request as final message
        messages.append({
            'role': 'user',
            'content': 'Please analyze the conversation above and extract memories according to the instructions.'
        })
        
        # 4. Call appropriate curation method
        if self.method == "sdk":
            return await self._curate_via_sdk(messages, system_prompt)
        else:
            return await self._curate_via_cli(messages, system_prompt)
    
    async def _curate_via_sdk(self, 
                              messages: List[Dict[str, Any]], 
                              system_prompt: str) -> Dict[str, Any]:
        """
        Curate using Claude Agent SDK.
        
        Uses Claude Code under the hood - subscription based.
        """
        try:
            from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock
        except ImportError:
            logger.error("claude-agent-sdk not installed. Install with: pip install claude-agent-sdk")
            logger.info("Falling back to CLI method...")
            return await self._curate_via_cli(messages, system_prompt)
        
        logger.info("🔧 Using Claude Agent SDK for curation")
        
        # SDK query() accepts a prompt string, not messages array
        # Format messages as conversation for the prompt
        conversation_text = self._format_messages_as_conversation(messages)
        
        options = ClaudeAgentOptions(
            system_prompt=system_prompt,
            max_turns=1
        )
        
        response_text = ""
        try:
            async for message in query(prompt=conversation_text, options=options):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            response_text += block.text
        except Exception as e:
            logger.error(f"SDK query failed: {e}")
            logger.info("Falling back to CLI method...")
            return await self._curate_via_cli(messages, system_prompt)
        
        logger.info("=" * 80)
        logger.info("FULL CLAUDE TRANSCRIPT CURATOR RESPONSE:")
        logger.info("=" * 80)
        logger.info(response_text)
        logger.info("=" * 80)
        
        # Use Curator's battle-tested parser
        return self._curator._parse_curation_response(
            self._extract_json(response_text)
        )
    
    async def _curate_via_cli(self, 
                              messages: List[Dict[str, Any]],
                              system_prompt: str) -> Dict[str, Any]:
        """
        Curate using CLI subprocess.
        
        Universal method - works with claude, gemini, or any compatible CLI.
        Uses the user's subscription.
        """
        # Ensure we have config for CLI method
        if not self.config:
            from .config import curator_config
            self.config = curator_config
            self.cli_command = self.cli_command or self.config.curator_command
        
        logger.info(f"🔧 Using CLI subprocess: {self.cli_command}")
        
        # Format messages as conversation text
        conversation_text = self._format_messages_as_conversation(messages)
        
        # Build the full prompt with system instructions + conversation
        full_prompt = f"{system_prompt}\n\n---\n\nCONVERSATION TRANSCRIPT:\n\n{conversation_text}"
        
        # Build CLI command using config template
        cmd = self.config.get_transcript_curation_command(full_prompt)
        
        logger.debug(f"CLI command: {cmd[0]} ... (prompt length: {len(full_prompt)})")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"CLI failed with code {process.returncode}")
                logger.error(f"Stderr: {stderr.decode()}")
                return {
                    "session_summary": "",
                    "interaction_tone": None,
                    "project_snapshot": {},
                    "memories": []
                }
            
            stdout_str = stdout.decode('utf-8').strip()
            logger.debug(f"Raw CLI output length: {len(stdout_str)}")
            
            # Parse CLI output using Curator's method
            try:
                output_json = json.loads(stdout_str)
                response_text = self._curator._extract_response_from_cli_output(output_json)
            except json.JSONDecodeError:
                response_text = stdout_str
            
            logger.info("=" * 80)
            logger.info("FULL CLAUDE TRANSCRIPT CURATOR RESPONSE:")
            logger.info("=" * 80)
            logger.info(response_text)
            logger.info("=" * 80)
            
            # Use Curator's battle-tested parser
            return self._curator._parse_curation_response(
                self._extract_json(response_text)
            )
            
        except Exception as e:
            logger.error(f"CLI execution failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "session_summary": "",
                "interaction_tone": None, 
                "project_snapshot": {},
                "memories": []
            }
    
    def _format_messages_as_conversation(self, messages: List[Dict[str, Any]]) -> str:
        """
        Format messages array as readable conversation text.
        
        Preserves the structure but makes it readable for the prompt.
        Content blocks (thinking, tool_use, etc) are included as context.
        """
        parts = []
        
        for msg in messages:
            role = msg.get('role', 'unknown').upper()
            content = msg.get('content', '')
            
            parts.append(f"[{role}]")
            
            if isinstance(content, str):
                parts.append(content)
            elif isinstance(content, list):
                # Content is array of blocks - format each
                for block in content:
                    block_type = block.get('type', 'unknown')
                    
                    if block_type == 'text':
                        parts.append(block.get('text', ''))
                    elif block_type == 'thinking':
                        # Include thinking - it's valuable context!
                        thinking = block.get('thinking', '')
                        if thinking:
                            # Truncate very long thinking blocks
                            if len(thinking) > 1000:
                                thinking = thinking[:1000] + '... [truncated]'
                            parts.append(f"[Thinking: {thinking}]")
                    elif block_type == 'tool_use':
                        tool_name = block.get('name', 'unknown')
                        tool_input = block.get('input', {})
                        # Include tool input summary
                        input_preview = str(tool_input)[:200] if tool_input else ''
                        parts.append(f"[Tool: {tool_name}] {input_preview}")
                    elif block_type == 'tool_result':
                        result = block.get('content', '')
                        if isinstance(result, str) and len(result) > 500:
                            result = result[:500] + '... [truncated]'
                        parts.append(f"[Tool Result: {result}]")
            
            parts.append("\n---\n")
        
        return '\n'.join(parts)
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON object from response text."""
        import re
        
        # Try to find JSON object
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json_match.group(0)
        
        return text


# ============================================================================
# Convenience Functions
# ============================================================================

async def curate_transcript(transcript_path: str,
                           method: Literal["sdk", "cli"] = "sdk",
                           cli_command: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to curate a transcript file.
    
    Args:
        transcript_path: Path to the .jsonl transcript file
        method: "sdk" or "cli"
        cli_command: CLI command for "cli" method
        
    Returns:
        Dictionary with session_summary, project_snapshot, and memories
    """
    curator = TranscriptCurator(method=method, cli_command=cli_command)
    return await curator.curate_from_transcript(transcript_path)


def get_transcript_path(session_id: str, project_path: Optional[str] = None) -> Optional[str]:
    """
    Get the transcript file path for a Claude Code session.
    
    Args:
        session_id: The Claude Code session ID
        project_path: Optional project path to narrow down search
        
    Returns:
        Path to the transcript file, or None if not found
    """
    claude_dir = Path.home() / ".claude"
    
    # If project path provided, look in project-specific directory
    if project_path:
        # Claude Code stores transcripts in ~/.claude/projects/<encoded-path>/
        # The path is URL-encoded with dashes
        encoded_path = project_path.replace('/', '-')
        if encoded_path.startswith('-'):
            encoded_path = encoded_path[1:]
        
        project_dir = claude_dir / "projects" / encoded_path
        if project_dir.exists():
            transcript = project_dir / f"{session_id}.jsonl"
            if transcript.exists():
                return str(transcript)
    
    # Search all project directories
    projects_dir = claude_dir / "projects"
    if projects_dir.exists():
        for project_dir in projects_dir.iterdir():
            if project_dir.is_dir():
                transcript = project_dir / f"{session_id}.jsonl"
                if transcript.exists():
                    return str(transcript)
    
    logger.warning(f"Transcript not found for session: {session_id}")
    return None
