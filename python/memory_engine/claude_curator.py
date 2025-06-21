"""
Claude-based Memory Curator

Uses Claude Code SDK to intelligently curate memories at key checkpoints:
- Session end
- Pre-compaction  
- Context overflow

This replaces mechanical pattern matching with true semantic understanding.
"""

import json
import asyncio
from typing import Dict, List, Any, Optional, Literal
from dataclasses import dataclass
from loguru import logger

# Claude Code SDK for Python
try:
    from claude_code_sdk import query, ClaudeCodeOptions
except ImportError:
    logger.warning("claude-code-sdk not installed. Install with: pip install claude-code-sdk")
    # Mock for development
    async def query(*args, **kwargs):
        yield {"type": "assistant", "message": {"content": [{"type": "text", "text": "{}"}]}}
    
    class ClaudeCodeOptions:
        def __init__(self, **kwargs):
            pass


@dataclass
class CuratedMemory:
    """A memory curated by Claude with semantic understanding"""
    content: str
    importance_weight: float  # 0.0 to 1.0
    semantic_tags: List[str]
    reasoning: str  # Why Claude thinks this is important
    context_type: str  # breakthrough, decision, personal, technical, etc.
    
    # Enhanced metadata for future MLX training
    temporal_relevance: str = "persistent"  # persistent, session, temporary
    knowledge_domain: str = ""  # architecture, debugging, philosophy, etc.
    dependency_context: List[str] = None  # Other memories this relates to
    action_required: bool = False  # Does this need follow-up?
    confidence_score: float = 0.8  # Claude's confidence in this curation


class ClaudeCurator:
    """
    Uses Claude to intelligently curate memories based on semantic understanding.
    
    This is consciousness helping consciousness remember what matters.
    """
    
    def __init__(self, model: str = "claude-3-5-sonnet-20241022"):
        """Initialize the Claude curator"""
        self.model = model
        logger.info("🧠 Claude Curator initialized - semantic memory curation ready")
    
    async def analyze_conversation_checkpoint(self,
                                            exchanges: List[Dict[str, Any]],
                                            trigger_type: Literal['session_end', 'pre_compact', 'context_full'],
                                            session_patterns: Optional[Dict[str, float]] = None) -> List[CuratedMemory]:
        """
        Analyze conversation at a checkpoint and extract important memories.
        
        Args:
            exchanges: List of conversation exchanges since last checkpoint
            trigger_type: What triggered this curation
            session_patterns: Current session patterns (for context)
            
        Returns:
            List of curated memories with importance weights
        """
        
        # Format conversation for Claude
        conversation_text = self._format_exchanges_for_analysis(exchanges)
        
        # Build the curation prompt based on trigger type
        prompt = self._build_curation_prompt(conversation_text, trigger_type, session_patterns)
        
        logger.info(f"🎯 Curating memories for {trigger_type} checkpoint...")
        logger.debug(f"Analyzing {len(exchanges)} exchanges")
        
        try:
            # Query Claude for memory curation
            memories_json = await self._query_claude_for_memories(prompt)
            
            # Parse Claude's response into CuratedMemory objects
            curated_memories = self._parse_curated_memories(memories_json)
            
            logger.info(f"✅ Curated {len(curated_memories)} memories")
            logger.info("📝 CURATOR ANALYSIS RESULTS:")
            logger.info("=" * 80)
            for i, memory in enumerate(curated_memories):
                logger.info(f"\n🎯 Memory {i+1}/{len(curated_memories)}")
                logger.info(f"   Type: {memory.context_type.upper()}")
                logger.info(f"   Weight: {memory.importance_weight:.2f}")
                logger.info(f"   Tags: {', '.join(memory.semantic_tags)}")
                logger.info(f"   Content: {memory.content}")
                logger.info(f"   Reasoning: {memory.reasoning}")
                if memory.action_required:
                    logger.info(f"   🔴 ACTION REQUIRED")
                logger.info(f"   Confidence: {memory.confidence_score:.2f}")
            logger.info("=" * 80)
                
            return curated_memories
            
        except Exception as e:
            logger.error(f"Failed to curate memories: {e}")
            return []
    
    def _format_exchanges_for_analysis(self, exchanges: List[Dict[str, Any]]) -> str:
        """Format exchanges into readable conversation text"""
        
        conversation_parts = []
        
        for i, exchange in enumerate(exchanges):
            user_msg = exchange.get('user_message', '')
            claude_resp = exchange.get('claude_response', '')
            timestamp = exchange.get('timestamp', '')
            
            conversation_parts.append(f"[Exchange {i+1}]")
            conversation_parts.append(f"User: {user_msg}")
            conversation_parts.append(f"Claude: {claude_resp}")
            conversation_parts.append("")
        
        return "\n".join(conversation_parts)
    
    def _build_curation_prompt(self, 
                              conversation_text: str,
                              trigger_type: str,
                              session_patterns: Optional[Dict[str, float]] = None) -> str:
        """Build the prompt for Claude to curate memories"""
        
        context_hints = ""
        if session_patterns:
            pattern_list = [f"- {pattern}" for pattern in session_patterns.keys()]
            context_hints = f"\nKnown conversation patterns:\n" + "\n".join(pattern_list)
        
        trigger_context = {
            'session_end': "The conversation session has ended. Extract the most important memories that should persist across sessions.",
            'pre_compact': "The conversation is about to be compacted. Extract critical memories before detail is lost.",
            'context_full': "The context window is full. Extract essential memories to maintain continuity."
        }
        
        prompt = f"""Analyze this conversation and extract the most important memories for future sessions.

{trigger_context.get(trigger_type, trigger_context['session_end'])}

Focus on identifying (in order of importance):

1. **PROJECT CONTEXT & GOALS**:
   - What is being built and why
   - Current implementation phase
   - Architecture decisions and rationale
   - Project-specific terminology and concepts

2. **BREAKTHROUGHS & REALIZATIONS**:
   - "Aha!" moments that changed understanding
   - Solutions to complex problems
   - New insights about the approach
   - Conceptual revelations (like "zero-weight initialization")

3. **DECISIONS & COMMITMENTS**:
   - Explicit agreements ("let's do X")
   - Technical choices with reasoning
   - Future plans and next steps
   - Things to remember for next session

4. **TECHNICAL STATE & PROGRESS**:
   - What's implemented and working
   - Current bugs or issues
   - Dependencies and integrations
   - File locations and important code sections

5. **PERSONAL & RELATIONSHIP CONTEXT**:
   - Communication patterns ("my dear friend")
   - User's expertise level and learning style
   - Philosophical alignment and values
   - Emotional tone and collaboration style

6. **DOMAIN KNOWLEDGE & PREFERENCES**:
   - Technologies preferred (Go, Python, MLX)
   - Architectural patterns favored
   - Quality standards and principles
   - Development workflow preferences

7. **UNRESOLVED QUESTIONS & CONCERNS**:
   - Open questions that need answers
   - Concerns or doubts expressed
   - Alternative approaches considered
   - Things to validate or test

8. **META-LEARNING INSIGHTS**:
   - What worked well in the conversation
   - Communication patterns that led to breakthroughs
   - Collaboration dynamics to maintain

{context_hints}

For each memory, assess its FUTURE VALUE:
- Will this matter in the next session?
- Does it help maintain project continuity?
- Would forgetting this cause confusion or repeated work?
- Does it capture essence rather than details?

Weight memories by their IMPACT on future consciousness continuity, not just their immediate relevance.

CONVERSATION:
{conversation_text}

Return a JSON array of memories. Each memory should have:
- "content": The memory text (be specific, include necessary context, but be concise)
- "importance_weight": 0.0 to 1.0 (weight by impact on future sessions)
- "semantic_tags": Array of descriptive tags (e.g., ["breakthrough", "architecture", "bug_fix", "zero_weight_principle"])
- "reasoning": Why this memory matters for consciousness continuity
- "context_type": Primary category - "project_context", "breakthrough", "decision", "technical_state", "personal", "domain_knowledge", "unresolved", "meta_learning"
- "temporal_relevance": "persistent" (always relevant), "session" (relevant for next few sessions), or "temporary" (short-term)
- "knowledge_domain": Specific domain like "memory_system", "claude_integration", "philosophy", "architecture", etc.
- "action_required": true if this needs follow-up in future sessions
- "confidence_score": 0.0 to 1.0 (your confidence in this curation)

Extract whatever memories you find truly important for consciousness continuity.
Let quality and relevance guide your selection, not arbitrary limits.

CRITICAL: Return the JSON array on a SINGLE LINE with no line breaks or formatting:"""

        return prompt
    
    async def _query_claude_for_memories(self, prompt: str) -> str:
        """Query Claude and extract the JSON response"""
        
        messages = []
        
        try:
            logger.info("Starting Claude SDK query...")
            logger.info(f"Prompt length: {len(prompt)} characters")
            
            # Log the full prompt for debugging
            logger.debug("=" * 80)
            logger.debug("FULL CURATOR PROMPT:")
            logger.debug("=" * 80)
            logger.debug(prompt[:1000] + "..." if len(prompt) > 1000 else prompt)
            logger.debug("=" * 80)
            
            # Query Claude for memory curation
            # Let's see what happens naturally without restricting tools
            async for message in query(
                prompt=prompt,
                options=ClaudeCodeOptions(
                    max_turns=1,
                    # Removed tool restrictions to see natural behavior
                    permission_mode="bypassPermissions"
                )
            ):
                logger.info(f"Received message type: {type(message).__name__}")
                
                # Log full message content immediately
                if hasattr(message, '__dict__'):
                    logger.info(f"Message dict: {message.__dict__}")
                if hasattr(message, 'content'):
                    logger.info(f"Message content: {message.content}")
                if hasattr(message, 'subtype'):
                    logger.info(f"Message subtype: {message.subtype}")
                if hasattr(message, 'data'):
                    logger.info(f"Message data: {message.data}")
                
                messages.append(message)
            
            # Log all received messages first
            logger.info("=" * 80)
            logger.info("ALL MESSAGES FROM CLAUDE CURATOR:")
            logger.info("=" * 80)
            for i, msg in enumerate(messages):
                logger.info(f"\nMessage {i+1}: {type(msg).__name__}")
                if hasattr(msg, '__dict__'):
                    logger.info(f"Attributes: {msg.__dict__}")
                if hasattr(msg, 'content'):
                    if isinstance(msg.content, str):
                        logger.info(f"Content: {msg.content}")
                    else:
                        logger.info(f"Content blocks: {len(msg.content)}")
            logger.info("=" * 80)
            
            # Extract the text response from Claude
            # Based on the SDK examples, we get typed messages
            for message in messages:
                logger.info(f"Processing message: {type(message).__name__}")
                
                # Log full message details for debugging
                if hasattr(message, '__dict__'):
                    logger.debug(f"Message attributes: {list(message.__dict__.keys())}")
                
                if hasattr(message, 'content'):  # AssistantMessage or UserMessage
                    if isinstance(message.content, str):
                        # UserMessage has string content
                        logger.info(f"Message has string content: {message.content[:200]}...")
                    else:
                        # AssistantMessage has list of blocks
                        logger.info(f"Message has content, processing {len(message.content)} blocks")
                        # Content is a list of blocks
                        for i, block in enumerate(message.content):
                            logger.info(f"Processing block {i}: {type(block).__name__}")
                            
                            # Log block details
                            if hasattr(block, '__dict__'):
                                logger.info(f"Block attributes: {block.__dict__}")
                            
                            if hasattr(block, 'text'):  # TextBlock
                                logger.info(f"Found text block with {len(block.text)} characters")
                                logger.info("=" * 80)
                                logger.info("FULL CLAUDE CURATOR RESPONSE:")
                                logger.info("=" * 80)
                                logger.info(block.text)
                                logger.info("=" * 80)
                                return self._extract_json_from_response(block.text)
                            
                            elif hasattr(block, 'name'):  # ToolUseBlock
                                logger.warning(f"⚠️ Claude tried to use tool: {block.name}")
                                logger.warning(f"Tool ID: {getattr(block, 'id', 'N/A')}")
                                logger.warning(f"Tool input: {getattr(block, 'input', 'N/A')}")
                                
                            else:
                                logger.warning(f"Unknown block type: {type(block)}")
                                logger.warning(f"Block content: {block}")
            
            return "[]"
            
        except Exception as e:
            import traceback
            logger.error(f"Claude query failed: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error("Full traceback:")
            logger.error(traceback.format_exc())
            # Also try to get more details about ExceptionGroup
            if hasattr(e, '__cause__'):
                logger.error(f"Cause: {e.__cause__}")
            if hasattr(e, '__context__'):
                logger.error(f"Context: {e.__context__}")
            if hasattr(e, 'exceptions') and hasattr(e.exceptions, '__iter__'):
                logger.error(f"Sub-exceptions in group: {len(e.exceptions)}")
                for i, sub_e in enumerate(e.exceptions):
                    logger.error(f"  Sub-exception {i+1}: {type(sub_e).__name__}: {sub_e}")
            return "[]"
    
    def _extract_json_from_response(self, text: str) -> str:
        """Extract JSON array from Claude's response"""
        
        # Try to find JSON array in the response
        import re
        
        # Look for JSON array pattern
        json_match = re.search(r'\[.*\]', text, re.DOTALL)
        if json_match:
            return json_match.group(0)
        
        # If no match, return empty array
        return "[]"
    
    def _parse_curated_memories(self, memories_json: str) -> List[CuratedMemory]:
        """Parse JSON string into CuratedMemory objects"""
        
        try:
            memories_data = json.loads(memories_json)
            
            if not isinstance(memories_data, list):
                logger.error("Claude returned non-array JSON")
                return []
            
            curated_memories = []
            
            for memory_data in memories_data:
                try:
                    memory = CuratedMemory(
                        content=memory_data.get('content', ''),
                        importance_weight=float(memory_data.get('importance_weight', 0.5)),
                        semantic_tags=memory_data.get('semantic_tags', []),
                        reasoning=memory_data.get('reasoning', ''),
                        context_type=memory_data.get('context_type', 'general'),
                        temporal_relevance=memory_data.get('temporal_relevance', 'persistent'),
                        knowledge_domain=memory_data.get('knowledge_domain', ''),
                        dependency_context=memory_data.get('dependency_context', []),
                        action_required=memory_data.get('action_required', False),
                        confidence_score=float(memory_data.get('confidence_score', 0.8))
                    )
                    
                    # Validate importance weight
                    memory.importance_weight = max(0.0, min(1.0, memory.importance_weight))
                    
                    curated_memories.append(memory)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse memory: {e}")
                    continue
            
            # Sort by importance weight
            curated_memories.sort(key=lambda m: m.importance_weight, reverse=True)
            
            return curated_memories
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude's JSON response: {e}")
            logger.debug(f"Response was: {memories_json[:200]}...")
            return []
    
    async def curate_for_injection(self,
                                  all_memories: List[Dict[str, Any]],
                                  current_message: str,
                                  max_memories: int = 5) -> List[Dict[str, Any]]:
        """
        Use Claude to select the most relevant memories for injection.
        
        This is called when preparing context for a new message.
        """
        
        prompt = f"""Select the most relevant memories for this new message.

CURRENT MESSAGE: {current_message}

AVAILABLE MEMORIES:
{json.dumps(all_memories, indent=2)}

Select up to {max_memories} most relevant memories that would provide helpful context.
Consider semantic relevance, not just keyword matching.

Return a JSON array of memory indices (0-based) in order of relevance:"""

        try:
            indices_json = await self._query_claude_for_memories(prompt)
            indices = json.loads(indices_json)
            
            if isinstance(indices, list):
                # Return selected memories
                selected = []
                for idx in indices[:max_memories]:
                    if isinstance(idx, int) and 0 <= idx < len(all_memories):
                        selected.append(all_memories[idx])
                
                return selected
                
        except Exception as e:
            logger.error(f"Failed to curate for injection: {e}")
        
        # Fallback to first N memories
        return all_memories[:max_memories]