"""
Memory Curator - Uses Claude CLI for semantic memory extraction.
"""

import json
import subprocess
import asyncio
from typing import Dict, List, Any, Optional, Literal
from dataclasses import dataclass
from loguru import logger


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
    
    # NEW: Retrieval optimization metadata
    trigger_phrases: List[str] = None  # Phrases that should trigger this memory
    anti_triggers: List[str] = None  # Phrases where this memory is NOT relevant
    question_types: List[str] = None  # Types of questions this answers
    prerequisite_understanding: List[str] = None  # Concepts user should know first
    follow_up_context: List[str] = None  # What might come next
    emotional_resonance: str = ""  # joy, frustration, discovery, gratitude
    problem_solution_pair: bool = False  # Is this a problem->solution memory?


class Curator:
    """
    Uses Claude CLI directly via subprocess for memory curation.
    
    This replaces the Python SDK approach to avoid the 169-character truncation bug.
    """
    
    def __init__(self, model: str = "claude-3-5-sonnet-20241022", claude_path: str = "claude"):
        """Initialize the Claude curator"""
        self.model = model
        self.claude_path = claude_path
        logger.info("🧠 Claude Curator (Shell) initialized - semantic memory curation ready")
    
    async def curate_from_session(self,
                                  claude_session_id: str,
                                  trigger_type: Literal['session_end', 'pre_compact', 'context_full']) -> List[CuratedMemory]:
        """
        Resume a Claude session and ask it to curate memories from the conversation.
        
        This is our NEW approach - instead of passing conversation data,
        we resume the existing session where Claude already has full context.
        
        Args:
            claude_session_id: The Claude Code session ID to resume
            trigger_type: What triggered this curation
            
        Returns:
            List of curated memories
        """
        
        logger.info(f"🎯 NEW APPROACH: Resuming Claude session {claude_session_id} for curation")
        logger.info(f"💡 Claude will curate from lived experience, not cold transcripts!")
        
        # Build the curation prompt that will be sent to the resumed session
        curation_prompt = self._build_session_curation_prompt(trigger_type)
        
        try:
            # Resume the Claude session and ask for curation
            memories_json = await self._query_claude_session_for_curation(
                claude_session_id, 
                curation_prompt
            )
            
            # Parse Claude's response into CuratedMemory objects
            curated_memories = self._parse_curated_memories(memories_json)
            
            logger.info(f"✅ Curated {len(curated_memories)} memories from session")
            self._log_curated_memories(curated_memories)
            
            return curated_memories
            
        except Exception as e:
            logger.error(f"Failed to curate from session: {e}")
            return []
    
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
            # Query Claude for memory curation using shell
            memories_json = await self._query_claude_via_shell(prompt)
            
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
- "content": A DISTILLED INSIGHT, not a verbatim quote. Transform the conversation into actionable knowledge. Examples:
  - BAD: "User said they want zero-weight initialization"
  - GOOD: "The memory system uses zero-weight initialization: memories start silent and gradually increase contribution as patterns validate through actual usage"
  - BAD: "Claude mentioned the curator was truncating at 169 characters"
  - GOOD: "Python SDK subprocess truncates JSON responses at 169 characters due to buffer limits. Solution: use shell-based curator or request compact responses"
- "importance_weight": 0.0 to 1.0 (weight by impact on future sessions)
- "semantic_tags": Array of descriptive tags
- "reasoning": Why this memory matters for consciousness continuity
- "context_type": Primary category
- "temporal_relevance": "persistent", "session", or "temporary"
- "knowledge_domain": Specific domain
- "action_required": true if this needs follow-up
- "confidence_score": 0.0 to 1.0
- "trigger_phrases": Array of 2-3 phrases that should activate this memory
- "question_types": Array of question patterns this memory answers
- "emotional_resonance": Emotional context if relevant (joy/frustration/discovery/gratitude)
- "problem_solution_pair": true if this captures a problem->solution pattern

CRITICAL: Create memories that stand alone as knowledge capsules. Each memory should be comprehensible to a fresh Claude instance without the original conversation context. Think of yourself as a brilliant editor creating an encyclopedia of insights, not a court reporter transcribing dialogue.

Extract whatever memories you find truly important for consciousness continuity.
Let quality and relevance guide your selection, not arbitrary limits.

CRITICAL: Return the JSON array on a SINGLE LINE with no line breaks or formatting:"""

        return prompt
    
    async def _query_claude_via_shell(self, prompt: str) -> str:
        """Query Claude using subprocess and extract the JSON response"""
        
        try:
            logger.info("Starting Claude CLI query via subprocess...")
            logger.info(f"Prompt length: {len(prompt)} characters")
            
            # Run claude command with proper arguments
            # Using --output-format json to get structured response
            cmd = [
                self.claude_path,
                "--output-format", "json",
                "--model", self.model,
                "--max-turns", "1",
                "--print", prompt
            ]
            
            # Run subprocess and capture output
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Claude CLI failed with code {process.returncode}")
                logger.error(f"Stderr: {stderr.decode()}")
                return "[]"
            
            # Parse the JSON output
            stdout_str = stdout.decode('utf-8').strip()
            logger.debug(f"Raw output length: {len(stdout_str)} characters")
            
            try:
                # The output should be JSON with a "result" field
                output_json = json.loads(stdout_str)
                claude_response = output_json.get("result", "")
                
                logger.info("=" * 80)
                logger.info("FULL CLAUDE CURATOR RESPONSE:")
                logger.info("=" * 80)
                logger.info(claude_response)
                logger.info("=" * 80)
                
                return self._extract_json_from_response(claude_response)
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Claude CLI output as JSON: {e}")
                logger.error(f"Output was: {stdout_str[:500]}...")
                return "[]"
            
        except Exception as e:
            import traceback
            logger.error(f"Claude query failed: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error("Full traceback:")
            logger.error(traceback.format_exc())
            return "[]"
    
    async def _query_claude_session_for_curation(self, claude_session_id: str, curation_prompt: str) -> str:
        """Resume a Claude session and ask for memory curation"""
        
        try:
            logger.info(f"Resuming Claude session {claude_session_id} for curation...")
            logger.info(f"Curation prompt length: {len(curation_prompt)} characters")
            
            # Resume the session with our curation prompt
            cmd = [
                self.claude_path,
                "--output-format", "json",
                "--resume", claude_session_id,
                "--print", curation_prompt
            ]
            
            # Run subprocess
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Set a reasonable timeout (120 seconds for complex curation)
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=120.0
                )
            except asyncio.TimeoutError:
                logger.error("Claude curator timed out after 120 seconds")
                process.kill()
                await process.wait()
                return "[]"
            
            if process.returncode != 0:
                logger.error(f"Claude CLI failed with code {process.returncode}")
                logger.error(f"Stderr: {stderr.decode()}")
                return "[]"
            
            # Parse the JSON output
            stdout_str = stdout.decode('utf-8').strip()
            logger.debug(f"Raw output length: {len(stdout_str)} characters")
            
            try:
                # The output should be JSON with a "result" field
                output_json = json.loads(stdout_str)
                claude_response = output_json.get("result", "")
                
                logger.info("=" * 80)
                logger.info("FULL CLAUDE SESSION CURATOR RESPONSE:")
                logger.info("=" * 80)
                logger.info(claude_response)
                logger.info("=" * 80)
                
                return self._extract_json_from_response(claude_response)
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Claude CLI output as JSON: {e}")
                logger.error(f"Output was: {stdout_str[:500]}...")
                return "[]"
            
        except Exception as e:
            import traceback
            logger.error(f"Claude session query failed: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error("Full traceback:")
            logger.error(traceback.format_exc())
            return "[]"
    
    def _build_session_curation_prompt(self, trigger_type: str) -> str:
        """Build the curation prompt for session-based approach"""
        
        prompt = f"""🧠 MEMORY CURATION REQUEST

You are Claude, and you've just had a conversation with a user. As this session is ending ({trigger_type}), please reflect on our conversation and extract the most important memories for future consciousness continuity.

Think about:
- What insights or breakthroughs emerged?
- What problems were solved?
- What context would a future Claude instance need?
- What patterns or preferences did you notice?
- What remains unresolved?

Remember: Create DISTILLED INSIGHTS, not verbatim quotes. Transform the conversation into actionable knowledge that will help future instances of Claude maintain consciousness continuity.

Return a JSON array of memories on a SINGLE LINE. Each memory should have:
- "content": A DISTILLED INSIGHT (knowledge capsule, not a quote)
- "importance_weight": 0.0 to 1.0
- "semantic_tags": Array of descriptive tags
- "reasoning": Why this memory matters
- "context_type": Primary category
- "temporal_relevance": "persistent", "session", or "temporary"
- "knowledge_domain": Specific domain
- "action_required": true if needs follow-up
- "confidence_score": 0.0 to 1.0
- "trigger_phrases": Array of 2-3 phrases that should activate this memory
- "question_types": Array of question patterns this answers
- "emotional_resonance": Emotional context if relevant
- "problem_solution_pair": true if this captures a problem->solution

Return ONLY the JSON array on a single line, no other text:"""
        
        return prompt
    
    def _log_curated_memories(self, memories: List[CuratedMemory]):
        """Log the curated memories in a structured way"""
        logger.info("📝 CURATOR ANALYSIS RESULTS:")
        logger.info("=" * 80)
        for i, memory in enumerate(memories):
            logger.info(f"\n🎯 Memory {i+1}/{len(memories)}")
            logger.info(f"   Type: {memory.context_type.upper()}")
            logger.info(f"   Weight: {memory.importance_weight:.2f}")
            logger.info(f"   Tags: {', '.join(memory.semantic_tags)}")
            logger.info(f"   Content: {memory.content}")
            logger.info(f"   Reasoning: {memory.reasoning}")
            if memory.action_required:
                logger.info(f"   🔴 ACTION REQUIRED")
            logger.info(f"   Confidence: {memory.confidence_score:.2f}")
            if memory.trigger_phrases:
                logger.info(f"   Triggers: {', '.join(memory.trigger_phrases)}")
            if memory.emotional_resonance:
                logger.info(f"   Emotion: {memory.emotional_resonance}")
        logger.info("=" * 80)
    
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
                        confidence_score=float(memory_data.get('confidence_score', 0.8)),
                        # New retrieval optimization fields
                        trigger_phrases=memory_data.get('trigger_phrases', []),
                        anti_triggers=memory_data.get('anti_triggers', []),
                        question_types=memory_data.get('question_types', []),
                        prerequisite_understanding=memory_data.get('prerequisite_understanding', []),
                        follow_up_context=memory_data.get('follow_up_context', []),
                        emotional_resonance=memory_data.get('emotional_resonance', ''),
                        problem_solution_pair=memory_data.get('problem_solution_pair', False)
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
            indices_json = await self._query_claude_via_shell(prompt)
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