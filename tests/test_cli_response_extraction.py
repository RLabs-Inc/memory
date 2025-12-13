"""
PR #9 Fix: CLI response extraction for Claude Code nested message format.

Before: Code looked for message["content"] directly
After: Handles message["message"]["content"] for Claude Code's nested format
"""

from memory_engine.curator import Curator


class TestNestedMessageFormat:
    """Test _extract_response_from_cli_output handles nested Claude Code format"""

    def setup_method(self):
        self.curator = Curator()

    def test_nested_claude_code_format(self):
        """
        PR #9 FIX: Claude Code CLI outputs {"type":"assistant","message":{"content":[...]}}
        The fix handles message["message"]["content"] instead of message["content"]
        """
        cli_output = [
            {
                "type": "assistant",
                "message": {"content": [{"type": "text", "text": "This is the curated response"}]},
            }
        ]

        result = self.curator._extract_response_from_cli_output(cli_output)
        assert result == "This is the curated response"
