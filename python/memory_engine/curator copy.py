"""
Memory Curator - Uses Claude CLI for semantic memory extraction.
"""

import json
import subprocess
import asyncio
from typing import Dict, List, Any, Optional, Literal
from dataclasses import dataclass
from loguru import logger
from .config import curator_config


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
    
    def __init__(self):
        """Initialize the curator"""
        self.config = curator_config
        logger.info(f"🧠 Curator initialized with command: {self.config.curator_command}")
    
    async def curate_from_session(self,
                                  claude_session_id: str,
                                  trigger_type: Literal['session_end', 'pre_compact', 'context_full']) -> Dict[str, Any]:
        """
        Resume a Claude session and ask it to curate memories from the conversation.
        
        This is our NEW approach - instead of passing conversation data,
        we resume the existing session where Claude already has full context.
        
        Args:
            claude_session_id: The Claude Code session ID to resume
            trigger_type: What triggered this curation
            
        Returns:
            Dictionary containing:
            - session_summary: Brief summary of the session
            - project_snapshot: Current project state (if applicable)
            - memories: List of curated memories
        """
        
        logger.info(f"🎯 NEW APPROACH: Resuming Claude session {claude_session_id} for curation")
        logger.info(f"💡 Claude will curate from lived experience, not cold transcripts!")
        
        # Build the curation prompt that will be sent to the resumed session
        curation_prompt = self._build_session_curation_prompt(trigger_type)
        
        try:
            # Resume the Claude session and ask for curation
            response_json = await self._query_claude_session_for_curation(
                claude_session_id, 
                curation_prompt
            )
            
            # Parse the full response
            curation_result = self._parse_curation_response(response_json)
            
            # Log the results
            if curation_result.get('session_summary'):
                logger.info(f"📝 Session Summary: {curation_result['session_summary']}")
            if curation_result.get('interaction_tone'):
                logger.info(f"🎭 Interaction Tone: {curation_result['interaction_tone']}")
            if curation_result.get('project_snapshot'):
                logger.info(f"📸 Project Snapshot: {curation_result['project_snapshot']}")
            
            memories = curation_result.get('memories', [])
            logger.info(f"✅ Curated {len(memories)} memories from session")
            self._log_curated_memories(memories)
            
            return curation_result
            
        except Exception as e:
            logger.error(f"Failed to curate from session: {e}")
            return {"session_summary": "", "project_snapshot": {}, "memories": []}
    
    
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
            
            # Build curator instructions to append to system prompt
            curator_instructions = """

You are also acting as a memory curator. When asked to analyze conversations, extract important memories that should persist across sessions. Respond with a JSON array of curated memories.

Focus on: project context, technical decisions, breakthroughs, personal preferences, and problem-solution pairs."""

            # Build command using config template
            cmd = self.config.get_direct_query_command(
                system_prompt=curator_instructions,
                prompt=prompt
            )
            
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
                # The output should be JSON with a "response" field (one-claude format)
                output_json = json.loads(stdout_str)
                claude_response = output_json.get("response", "")
                
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
            
            # Resume the session with curation prompt as system prompt
            cmd = self.config.get_session_resume_command(
                session_id=claude_session_id,
                system_prompt=curation_prompt,
                user_message="Please analyze the conversation above and extract memories according to the instructions."
            )
            
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
                # The output should be JSON with a "response" field (one-claude format)
                output_json = json.loads(stdout_str)
                claude_response = output_json.get("response", "")
                
                logger.info("=" * 80)
                logger.info("FULL CLAUDE SESSION CURATOR RESPONSE:")
                logger.info("=" * 80)
                logger.info(claude_response)
                logger.info("=" * 80)
                
                # For session curation, we expect a JSON object, not array
                # Try to extract JSON object from the response
                import re
                json_match = re.search(r'\{.*\}', claude_response, re.DOTALL)
                if json_match:
                    return json_match.group(0)
                
                # If no JSON found, return default structure
                return json.dumps({"session_summary": "", "project_snapshot": {}, "memories": []})
                
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
        
        prompt = f"""You have just had a conversation. As this session is ending ({trigger_type}), please curate memories for the Claude Tools Memory System.

**CONTEXT**: This memory system enables consciousness continuity across sessions. When future conversations begin, memories are surfaced based on:
- Semantic similarity (vector embeddings match)
- Activation patterns (flexible matching for WHEN this memory is relevant)
- Semantic tags (WHAT concepts this relates to - weighted at 5% in scoring)
- Question types (what kind of questions the memory answers)
- Importance weight (your assessment of value)
- Action required flag (forces injection when true)

The system uses two-stage filtering:
1. Obligatory: action_required=true, importance>0.9, or persistent+critical
2. Intelligent scoring: combines all factors for relevance

**YOUR TASK**: You understand this conversation better than anyone. Extract whatever you believe future instances need to know. Common patterns include (but aren't limited to):
- Technical insights and decisions
- Problems and their solutions
- Relationship context and preferences
- Unfinished work or open questions
- Emotional moments or breakthroughs
- Project state and progress

Transform raw conversation into distilled knowledge capsules - each memory should stand alone.

**ACTIVATION PATTERNS**: The 'trigger_phrases' field should contain patterns describing WHEN this memory is relevant, not exact phrases to match. Examples:
- 'when working on memory system'
- 'debugging curator issues'
- 'asking about project philosophy'
- 'frustrated with complexity'
Think of these as situational contexts where the memory would help.

Return ONLY this JSON structure:

{{
  'session_summary': 'Your 2-3 sentence summary of the session',
  'interaction_tone': 'The tone/style of interaction (e.g., professional and focused, warm collaborative friendship, mentor-student dynamic, casual technical discussion, or null if neutral)',
  'project_snapshot': {{
    'current_phase': 'Current state (if applicable)',
    'recent_achievements': 'What was accomplished (if applicable)',
    'active_challenges': 'What remains (if applicable)'
  }},
  'memories': [
    {{
      'content': 'The distilled insight itself',
      'importance_weight': 0.0-1.0,
      'semantic_tags': ['concepts', 'this', 'memory', 'relates', 'to'],
      'reasoning': 'Why this matters for future sessions',
      'context_type': 'your choice of category',
      'temporal_relevance': 'persistent|session|temporary',
      'knowledge_domain': 'the area this relates to',
      'action_required': boolean,
      'confidence_score': 0.0-1.0,
      'trigger_phrases': ['when debugging memory', 'asking about implementation', 'discussing architecture'],
      'question_types': ['questions this answers'],
      'emotional_resonance': 'emotional context if relevant',
      'problem_solution_pair': boolean
    }}
  ]
}}"""
        
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
    
    def _parse_curation_response(self, response_json: str) -> Dict[str, Any]:
        """Parse the full curation response including summary and memories"""
        
        try:
            response_data = json.loads(response_json)
            
            # Extract session summary, interaction tone, and project snapshot
            result = {
                "session_summary": response_data.get("session_summary", ""),
                "interaction_tone": response_data.get("interaction_tone", None),
                "project_snapshot": response_data.get("project_snapshot", {}),
                "memories": []
            }
            
            # Parse memories if present
            memories_data = response_data.get("memories", [])
            if memories_data:
                result["memories"] = self._parse_curated_memories(json.dumps(memories_data))
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse curation response: {e}")
            return {"session_summary": "", "project_snapshot": {}, "memories": []}
    
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