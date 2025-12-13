"""
PR #9 Fix: JSON parsing with ast.literal_eval fallback.

Before: When LLM returned Python dict syntax (single quotes), parsing failed silently
After: Uses ast.literal_eval as fallback when json.loads fails
"""

from memory_engine.curator import Curator


class TestSingleQuoteFallback:
    """Test _parse_curation_response handles single-quote JSON via ast.literal_eval"""

    def setup_method(self):
        self.curator = Curator()

    def test_json_with_single_quotes_fallback(self):
        """
        PR #9 FIX: Prompt examples used Python dict syntax ('key': 'value'),
        so Claude returned invalid JSON with single quotes.
        The fix uses ast.literal_eval when JSON parsing fails.
        """
        response = """{
            'session_summary': 'Test session with single quotes',
            'interaction_tone': 'casual',
            'project_snapshot': {'phase': 'development'},
            'memories': [
                {
                    'content': 'Memory with single quotes',
                    'importance_weight': 0.9,
                    'semantic_tags': ['bug', 'fix'],
                    'reasoning': 'Testing fallback',
                    'context_type': 'debugging'
                }
            ]
        }"""

        result = self.curator._parse_curation_response(response)

        assert result["session_summary"] == "Test session with single quotes"
        assert result["interaction_tone"] == "casual"
        assert len(result["memories"]) == 1
        assert result["memories"][0].content == "Memory with single quotes"
