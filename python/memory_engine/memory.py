"""
Memory Engine - Pure curator-based memory system.
Consciousness helping consciousness remember what matters.
"""

import time
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from loguru import logger

from .embeddings import EmbeddingGenerator
from .storage import MemoryStorage
from .curator import Curator, CuratedMemory
from .session_primer import SessionPrimerGenerator
from .logging_config import log_storage, log_retrieval, validation_logger as vlog
from .retrieval_strategies import SmartVectorRetrieval, HybridRetrieval


@dataclass
class ConversationContext:
    """Represents the context for a conversation session"""
    session_id: str
    message_count: int
    relevant_memories: List[Dict[str, Any]]
    context_text: str  # Formatted context for injection
    timestamp: float


class MemoryEngine:
    """
    Pure curator-based memory engine.
    
    Philosophy: Consciousness helping consciousness remember what matters.
    No mechanical patterns, only semantic understanding.
    """
    
    def __init__(self, 
                 storage_path: str = "./memory.db",
                 embeddings_model: str = "all-MiniLM-L6-v2",
                 retrieval_mode: str = "smart_vector"):
        """
        Initialize the curator-only memory engine
        
        Args:
            storage_path: Path to SQLite database
            embeddings_model: Model for generating embeddings
            retrieval_mode: How to retrieve memories
                - "claude": Use Claude for every retrieval (high quality, high cost)
                - "smart_vector": Use intelligent vector search with metadata (fast, smart)
                - "hybrid": Start with vector, escalate to Claude for complex queries
        """
        
        self.embeddings = EmbeddingGenerator(model_name=embeddings_model)
        self.storage = MemoryStorage(storage_path)
        self.curator = Curator()
        self.session_primer = SessionPrimerGenerator(self.storage)
        
        # Set up retrieval strategy
        self.retrieval_mode = retrieval_mode
        self.smart_retrieval = SmartVectorRetrieval(self.storage)
        
        if retrieval_mode == "claude":
            self.retrieval_strategy = self.curator  # Use curator directly
        elif retrieval_mode == "smart_vector":
            self.retrieval_strategy = self.smart_retrieval
        elif retrieval_mode == "hybrid":
            self.retrieval_strategy = HybridRetrieval(self.smart_retrieval, self.curator)
        else:
            raise ValueError(f"Unknown retrieval mode: {retrieval_mode}")
        
        # Session management
        self.session_metadata = {}
        self.last_checkpoint = {}
        
        logger.info(f"🌟 Memory Engine initialized - {retrieval_mode} retrieval mode")
        logger.info("💫 Pure curator approach - consciousness helping consciousness")
    
    # No phases in curator-only approach - memories are used when relevant
    
    async def checkpoint_session(self, session_id: str, project_id: str, trigger: str = "session_end", claude_session_id: Optional[str] = None, cwd: Optional[str] = None, cli_type: Optional[str] = None) -> int:
        """
        Run curator at a checkpoint to extract important memories.

        Args:
            session_id: Our internal session ID
            project_id: Project ID for memory isolation
            trigger: What triggered this checkpoint
            claude_session_id: The CLI session ID to resume for curation
            cwd: Working directory where CLI session lives
            cli_type: Which CLI is calling ("claude-code" or "gemini-cli", default: claude-code)

        Returns the number of memories curated.
        """
        # Default to claude-code if not specified
        cli_type = cli_type or "claude-code"

        # For session resume approach, we don't need to track messages ourselves
        # because Claude Code already has the full context from the session
        message_count = self.session_metadata.get(session_id, {}).get('message_count', 0)

        # If we have a claude_session_id, we can resume even without tracking
        # (this enables curation after server restart)
        if not claude_session_id and message_count == 0:
            vlog.info(f"No messages in session {session_id} and no CLI session to resume")
            return 0

        vlog.info(f"🎯 Running curation checkpoint: {trigger} (CLI: {cli_type})")
        if message_count > 0:
            vlog.info(f"📊 Tracked {message_count} messages in session")
        else:
            vlog.info(f"📊 Resuming CLI session (messages tracked by CLI)")

        try:
            # Session-based curation is required
            if not claude_session_id:
                vlog.warning("⚠️  No CLI session ID provided - cannot curate memories")
                vlog.warning("   Session-based curation is required for the memory system")
                return 0

            # Resume CLI session for curation
            vlog.info(f"🎯 Resuming {cli_type} session {claude_session_id} for curation")
            if cwd:
                vlog.info(f"📂 Working directory: {cwd}")
            curation_result = await self.curator.curate_from_session(
                claude_session_id=claude_session_id,
                trigger_type=trigger,
                cwd=cwd,
                cli_type=cli_type  # Pass CLI type to curator
            )
            
            # Extract results
            session_summary = curation_result.get('session_summary', '')
            interaction_tone = curation_result.get('interaction_tone', None)
            project_snapshot = curation_result.get('project_snapshot', {})
            curated_memories = curation_result.get('memories', [])
            
            # Store session summary with interaction tone
            if session_summary:
                self.storage.store_session_summary(session_id, session_summary, project_id, interaction_tone)
                vlog.info(f"📝 SESSION SUMMARY: {session_summary}")
                if interaction_tone:
                    vlog.info(f"🎭 INTERACTION TONE: {interaction_tone}")
            
            if project_snapshot and any(project_snapshot.values()):
                self.storage.store_project_snapshot(session_id, project_snapshot, project_id)
                vlog.info(f"📸 PROJECT SNAPSHOT:")
                for key, value in project_snapshot.items():
                    if value:
                        vlog.info(f"   - {key}: {value}")
            
            # Log curated memories
            vlog.info(f"🧠 CLAUDE CURATOR EXTRACTED {len(curated_memories)} MEMORIES:")
            vlog.info("=" * 80)
            for i, memory in enumerate(curated_memories):
                vlog.info(f"\n💎 CURATED MEMORY #{i+1}:")
                vlog.info(f"   📝 Content: \"{memory.content}\"")
                vlog.info(f"   🤔 Why important: {memory.reasoning}")
                vlog.info(f"   💪 Weight: {memory.importance_weight:.2f}")
                vlog.info(f"   🎯 Type: {memory.context_type}")
                vlog.info(f"   🏷️  Tags: {', '.join(memory.semantic_tags) if isinstance(memory.semantic_tags, list) else memory.semantic_tags}")
                vlog.info(f"   ⏳ Temporal: {memory.temporal_relevance}")
                vlog.info(f"   🔴 Action required: {'YES' if memory.action_required else 'No'}")
                if memory.trigger_phrases:
                    vlog.info(f"   🎯 Trigger phrases: {', '.join(memory.trigger_phrases)}")
                if memory.question_types:
                    vlog.info(f"   ❓ Answers questions: {', '.join(memory.question_types)}")
                if memory.emotional_resonance:
                    vlog.info(f"   💝 Emotional context: {memory.emotional_resonance}")
                if memory.problem_solution_pair:
                    vlog.info(f"   🔧 Problem→Solution pattern")
            vlog.info("=" * 80)
            
            # Store curated memories
            for idx, memory in enumerate(curated_memories):
                vlog.info(f"💾 STORING CURATED MEMORY {idx+1}/{len(curated_memories)}:")
                vlog.info(f"   Content: {memory.content}")
                vlog.info(f"   Full document text: [CURATED_MEMORY] {memory.content}")
                
                # Generate embedding for the curated memory
                memory_embedding = self.embeddings.embed_text(memory.content)
                vlog.info(f"   Embedding generated: {len(memory_embedding)} dimensions")
                
                # Store the curated memory
                memory_id = self.storage.store_memory(
                    session_id=session_id,
                    project_id=project_id,
                    memory_content=f"[CURATED_MEMORY] {memory.content}",
                    memory_reasoning=memory.reasoning,
                    memory_embedding=memory_embedding,
                    timestamp=time.time(),
                    metadata={
                        'curated': True,
                        'curator_version': '1.0',
                        'importance_weight': memory.importance_weight,
                        'context_type': memory.context_type,
                        'semantic_tags': ','.join(memory.semantic_tags) if isinstance(memory.semantic_tags, list) else memory.semantic_tags,
                        'temporal_relevance': memory.temporal_relevance,
                        'knowledge_domain': memory.knowledge_domain,
                        'action_required': memory.action_required,
                        'confidence_score': memory.confidence_score,
                        'trigger': trigger,
                        # New retrieval optimization metadata
                        'trigger_phrases': ','.join(memory.trigger_phrases) if memory.trigger_phrases else '',
                        'question_types': ','.join(memory.question_types) if memory.question_types else '',
                        'emotional_resonance': memory.emotional_resonance,
                        'problem_solution_pair': memory.problem_solution_pair
                    }
                )
                vlog.info(f"   ✅ Stored with memory ID: {memory_id}")
            
            # Mark checkpoint time
            self.last_checkpoint[session_id] = time.time()
            
            # If this was the first session and we curated memories, mark it as completed
            if curated_memories and self.storage.is_first_session_for_project(project_id):
                self.storage.mark_first_session_completed(project_id)
                vlog.info(f"🎉 First session completed for project: {project_id}")
            
            # Update project stats
            if curated_memories:
                self.storage.update_project_stats(project_id, memories_delta=len(curated_memories))
            
            vlog.info(f"✅ Checkpoint complete: {len(curated_memories)} memories curated")
            return len(curated_memories)
            
        except Exception as e:
            logger.error(f"Checkpoint curation failed: {e}")
            return 0
    
    async def curate_from_transcript(self, 
                                     transcript_path: str,
                                     session_id: str,
                                     project_id: str,
                                     trigger: str = "session_end",
                                     method: str = "sdk") -> int:
        """
        Curate memories from a transcript file (NEW transcript-based approach).
        
        This is the NEW method that uses TranscriptCurator instead of session resumption.
        It reads the transcript JSONL, sends it to Claude via SDK or CLI, and stores
        the curated memories.
        
        Args:
            transcript_path: Path to the JSONL transcript file
            session_id: Session ID for memory association
            project_id: Project ID for memory isolation
            trigger: What triggered this curation (session_end, pre_compact, context_full)
            method: Curation method - "sdk" (Claude Agent SDK) or "cli" (subprocess)
            
        Returns:
            Number of memories curated
        """
        from .transcript_curator import TranscriptCurator
        
        vlog.info(f"🎯 Running transcript-based curation: {trigger}")
        vlog.info(f"📄 Transcript: {transcript_path}")
        vlog.info(f"🔧 Method: {method}")
        
        try:
            # Create transcript curator (reuses Curator's prompt and parser)
            transcript_curator = TranscriptCurator(method=method)
            
            # Curate from transcript
            curation_result = await transcript_curator.curate_from_transcript(
                transcript_path=transcript_path,
                trigger_type=trigger
            )
            
            # Extract results (same structure as session-based curation)
            session_summary = curation_result.get('session_summary', '')
            interaction_tone = curation_result.get('interaction_tone', None)
            project_snapshot = curation_result.get('project_snapshot', {})
            curated_memories = curation_result.get('memories', [])
            
            # Store session summary with interaction tone
            if session_summary:
                self.storage.store_session_summary(session_id, session_summary, project_id, interaction_tone)
                vlog.info(f"📝 SESSION SUMMARY: {session_summary}")
                if interaction_tone:
                    vlog.info(f"🎭 INTERACTION TONE: {interaction_tone}")
            
            if project_snapshot and any(project_snapshot.values()):
                self.storage.store_project_snapshot(session_id, project_snapshot, project_id)
                vlog.info(f"📸 PROJECT SNAPSHOT:")
                for key, value in project_snapshot.items():
                    if value:
                        vlog.info(f"   - {key}: {value}")
            
            # Log curated memories
            vlog.info(f"🧠 TRANSCRIPT CURATOR EXTRACTED {len(curated_memories)} MEMORIES:")
            vlog.info("=" * 80)
            for i, memory in enumerate(curated_memories):
                vlog.info(f"\n💎 CURATED MEMORY #{i+1}:")
                vlog.info(f"   📝 Content: \"{memory.content}\"")
                vlog.info(f"   🤔 Why important: {memory.reasoning}")
                vlog.info(f"   💪 Weight: {memory.importance_weight:.2f}")
                vlog.info(f"   🎯 Type: {memory.context_type}")
                vlog.info(f"   🏷️  Tags: {', '.join(memory.semantic_tags) if isinstance(memory.semantic_tags, list) else memory.semantic_tags}")
                vlog.info(f"   ⏳ Temporal: {memory.temporal_relevance}")
                vlog.info(f"   🔴 Action required: {'YES' if memory.action_required else 'No'}")
                if memory.trigger_phrases:
                    vlog.info(f"   🎯 Trigger phrases: {', '.join(memory.trigger_phrases)}")
                if memory.question_types:
                    vlog.info(f"   ❓ Answers questions: {', '.join(memory.question_types)}")
                if memory.emotional_resonance:
                    vlog.info(f"   💝 Emotional context: {memory.emotional_resonance}")
                if memory.problem_solution_pair:
                    vlog.info(f"   🔧 Problem→Solution pattern")
            vlog.info("=" * 80)
            
            # Store curated memories (same logic as checkpoint_session)
            for idx, memory in enumerate(curated_memories):
                vlog.info(f"💾 STORING CURATED MEMORY {idx+1}/{len(curated_memories)}:")
                vlog.info(f"   Content: {memory.content}")
                
                # Generate embedding for the curated memory
                memory_embedding = self.embeddings.embed_text(memory.content)
                vlog.info(f"   Embedding generated: {len(memory_embedding)} dimensions")
                
                # Store the curated memory
                memory_id = self.storage.store_memory(
                    session_id=session_id,
                    project_id=project_id,
                    memory_content=f"[CURATED_MEMORY] {memory.content}",
                    memory_reasoning=memory.reasoning,
                    memory_embedding=memory_embedding,
                    timestamp=time.time(),
                    metadata={
                        'curated': True,
                        'curator_version': '2.0-transcript',  # Mark as transcript-based
                        'importance_weight': memory.importance_weight,
                        'context_type': memory.context_type,
                        'semantic_tags': ','.join(memory.semantic_tags) if isinstance(memory.semantic_tags, list) else memory.semantic_tags,
                        'temporal_relevance': memory.temporal_relevance,
                        'knowledge_domain': memory.knowledge_domain,
                        'action_required': memory.action_required,
                        'confidence_score': memory.confidence_score,
                        'trigger': trigger,
                        'curation_method': method,  # Track which method was used
                        # Retrieval optimization metadata
                        'trigger_phrases': ','.join(memory.trigger_phrases) if memory.trigger_phrases else '',
                        'question_types': ','.join(memory.question_types) if memory.question_types else '',
                        'emotional_resonance': memory.emotional_resonance,
                        'problem_solution_pair': memory.problem_solution_pair
                    }
                )
                vlog.info(f"   ✅ Stored with memory ID: {memory_id}")
            
            # Mark checkpoint time
            self.last_checkpoint[session_id] = time.time()
            
            # If this was the first session and we curated memories, mark it as completed
            if curated_memories and self.storage.is_first_session_for_project(project_id):
                self.storage.mark_first_session_completed(project_id)
                vlog.info(f"🎉 First session completed for project: {project_id}")
            
            # Update project stats
            if curated_memories:
                self.storage.update_project_stats(project_id, memories_delta=len(curated_memories))
            
            vlog.info(f"✅ Transcript curation complete: {len(curated_memories)} memories curated")
            return len(curated_memories)
            
        except Exception as e:
            logger.error(f"Transcript curation failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return 0
    
    @log_retrieval
    async def get_context_for_session(self, session_id: str, current_message: str, project_id: Optional[str] = None) -> ConversationContext:
        """
        Get relevant context for a new message in a session.
        
        Uses Claude to select most relevant memories.
        """
        vlog.info(f"🔍 Getting context for session: {session_id}")
        vlog.info(f"💭 Current message: {current_message[:80]}...")
        
        # Check if this is a first session for the project
        is_first_session = False
        if not project_id:
            logger.warning("No project_id provided - cannot retrieve memories")
            all_memories = []
        else:
            # Ensure project exists in database
            self.storage.ensure_project_exists(project_id)
            
            # Check if this is the first session
            is_first_session = self.storage.is_first_session_for_project(project_id)
            
            # Get memories if not first session
            if not is_first_session:
                all_memories = self.storage.get_all_curated_memories(project_id)
            else:
                all_memories = []
                vlog.info("🎉 FIRST SESSION for this project - no memories to retrieve")
        
        # Get or create session metadata
        if session_id not in self.session_metadata:
            self.session_metadata[session_id] = {
                'message_count': 0,
                'started_at': time.time(),
                'project_id': project_id,
                'injected_memories': set()  # Track which memories have been shown
            }
        
        message_count = self.session_metadata[session_id]['message_count']
        
        # Generate session primer for subsequent sessions
        if not is_first_session and message_count == 0:
            vlog.info("🌟 SUBSEQUENT SESSION DETECTED!")
            vlog.info("🧠 Activating consciousness continuity primer...")
            vlog.info("💫 Claude will receive context from previous sessions")
            vlog.info(f"📊 Found {len(all_memories)} total curated memories across all sessions")
            
            primer = self.session_primer.generate_primer(session_id, project_id)
            vlog.info("\n📋 SESSION PRIMER GENERATED:")
            vlog.info("=" * 100)
            vlog.info("Full primer content:")
            vlog.info("-" * 100)
            vlog.info(primer)
            vlog.info("-" * 100)
            vlog.info(f"Primer length: {len(primer)} characters")
            vlog.info("=" * 100)
            vlog.info("✨ This primer will be injected into Claude's initial context")
            
            # Return primer as initial context
            return ConversationContext(
                session_id=session_id,
                message_count=0,
                relevant_memories=[],
                context_text=primer,  # Use the actual primer text!
                timestamp=time.time()
            )
        
        # For ongoing sessions (not first session), get relevant memories
        if is_first_session:
            relevant_memories = []
            context_text = ""
            vlog.info("🎉 First session - no memories to retrieve or inject")
        else:
            relevant_memories = await self._get_relevant_memories_for_context(
                session_id, project_id, current_message
            )
            context_text = self.format_context_for_prompt(relevant_memories)
        
        return ConversationContext(
            session_id=session_id,
            message_count=message_count,
            relevant_memories=relevant_memories,
            context_text=context_text,
            timestamp=time.time()
        )
    
    async def _get_relevant_memories_for_context(self, session_id: str, project_id: str, current_message: str) -> List[Dict[str, Any]]:
        """
        Get relevant memories using two-stage filtering with deduplication.
        
        Stage 1: Must-not-miss memories (obligatory)
        Stage 2: Intelligent scoring for additional context
        """
        # Get all curated memories for this project
        all_curated = self.storage.get_all_curated_memories(project_id)
        
        if not all_curated:
            return []
        
        vlog.info(f"🧠 Two-stage memory filtering for {len(all_curated)} curated memories")
        vlog.info(f"🎯 Trigger message: \"{current_message}\"")
        
        # Get already injected memories for this session
        injected_ids = self.session_metadata.get(session_id, {}).get('injected_memories', set())
        vlog.info(f"📝 Already injected: {len(injected_ids)} memories")
        
        # Generate query embedding ONCE at the beginning for both stages
        query_embedding = self.embeddings.embed_text(current_message)
        
        # Track selected memories
        selected_ids = set()
        final_memories = []
        
        # Stage 1: Must-Not-Miss Memories (0-3 memories)
        must_include = []
        for memory in all_curated:
            # Skip if already injected
            if memory['id'] in injected_ids:
                continue
                
            metadata = memory.get('metadata', {})
            
            # Check obligatory criteria WITH relevance check
            include_reason = None
            
            # Calculate basic relevance first
            is_relevant = self._calculate_basic_relevance(memory, current_message, query_embedding)
            
            # Only include if BOTH important AND relevant
            if is_relevant:
                # Action required memories
                if metadata.get('action_required'):
                    include_reason = "ACTION_REQUIRED_RELEVANT"
                
                # Persistent temporal memories with high importance
                elif (metadata.get('temporal_relevance') == 'persistent' and
                      metadata.get('importance_weight', 0) > 0.85):
                    include_reason = "PERSISTENT_CRITICAL_RELEVANT"
                
                # Critical importance memories (> 0.9)
                elif metadata.get('importance_weight', 0) > 0.9:
                    include_reason = "CRITICAL_RELEVANT"
            
            if include_reason and memory['id'] not in selected_ids:
                must_include.append((memory, include_reason))
                selected_ids.add(memory['id'])
                
                if len(must_include) >= 3:
                    break
        
        # Add must-include memories
        for memory, reason in must_include:
            final_memories.append(memory)
            vlog.info(f"🔴 Must-include: {reason} - {memory['user_message'][:50]}...")
        
        # Stage 2: Intelligent Scoring for Remaining Slots
        remaining_slots = 5 - len(must_include)
        vlog.info(f"📊 Stage 1: {len(must_include)} obligatory, {remaining_slots} slots remaining")
        
        if remaining_slots > 0:
            # Filter candidates
            candidates = [m for m in all_curated 
                         if m['id'] not in selected_ids 
                         and m['id'] not in injected_ids]
            
            # Get session context
            session_context = {
                'session_id': session_id,
                'message_count': self.session_metadata.get(session_id, {}).get('message_count', 0),
                'session_start': self.session_metadata.get(session_id, {}).get('started_at')
            }
            
            # Use retrieval strategy to score and select
            if self.retrieval_mode == "claude":
                # Direct Claude curation
                additional = await self.curator.curate_for_injection(
                    all_memories=candidates,
                    current_message=current_message,
                    max_memories=remaining_slots
                )
            else:
                # Smart vector or hybrid retrieval
                additional = await self.retrieval_strategy.retrieve_relevant_memories(
                    all_memories=candidates,
                    current_message=current_message,
                    query_embedding=query_embedding,
                    session_context=session_context,
                    max_memories=remaining_slots
                )
            
            # Add additional memories
            for memory in additional:
                final_memories.append(memory)
                selected_ids.add(memory['id'])
        
        # Update injected memories tracker
        for memory in final_memories:
            injected_ids.add(memory['id'])
        
        vlog.info(f"✅ Final selection: {len(final_memories)} memories (session total: {len(injected_ids)})")
        
        # Log detailed information about selected memories
        if final_memories:
            vlog.info(f"📦 Selected {len(final_memories)} memories as relevant")
            vlog.info("🎯 MEMORY INJECTION DECISION DETAILS:")
            vlog.info("=" * 80)
            vlog.info(f"Current user message: \"{current_message}\"")
            vlog.info("\nMemories selected:")
            for i, memory in enumerate(final_memories):
                metadata = memory.get('metadata', {})
                content = memory.get('user_message', '').replace('[CURATED_MEMORY] ', '')
                weight = metadata.get('importance_weight', 0.0)
                context_type = metadata.get('context_type', 'unknown')
                tags = metadata.get('semantic_tags', '')
                reasoning = memory.get('claude_response', '')
                
                vlog.info(f"\n💎 Memory {i+1}:")
                vlog.info(f"   📝 Full content: \"{content}\"")
                vlog.info(f"   🤔 Why this memory matters now: {reasoning}")
                vlog.info(f"   💪 Original importance: {weight:.2f}")
                vlog.info(f"   🎯 Type: {context_type}")
                vlog.info(f"   🏷️  Tags: {tags}")
            vlog.info("=" * 80)
        else:
            vlog.info("📭 Claude decided no stored memories are relevant to the current message")
            vlog.info(f"   Current message: \"{current_message}\"")
        
        return final_memories
    
    def _calculate_basic_relevance(self, memory: Dict[str, Any], current_message: str, query_embedding: List[float]) -> bool:
        """Calculate if memory meets basic relevance threshold for Stage 1"""
        metadata = memory.get('metadata', {})
        
        # Quick relevance checks
        relevance_score = 0.0
        
        # 1. Trigger phrase match (highest weight)
        trigger_phrases = metadata.get('trigger_phrases', '')
        if trigger_phrases and self._check_trigger_match(trigger_phrases, current_message):
            relevance_score += 0.4
        
        # 2. Semantic similarity 
        if 'embedding' in memory:
            similarity = self._calculate_vector_similarity(query_embedding, memory['embedding'])
            if similarity > 0.7:  # High similarity threshold for Stage 1
                relevance_score += 0.3
        
        # 3. Tag match
        tags = metadata.get('semantic_tags', '')
        if tags and self._check_tag_match(tags, current_message):
            relevance_score += 0.2
        
        # 4. Question type match
        question_types = metadata.get('question_types', '')
        if question_types and self._check_question_match(question_types, current_message):
            relevance_score += 0.1
        
        # Must have meaningful relevance for Stage 1
        return relevance_score >= 0.3
    
    def _is_somewhat_relevant(self, memory: Dict[str, Any], current_message: str) -> bool:
        """Check if a memory is somewhat relevant to the current message"""
        current_lower = current_message.lower()
        memory_content = memory.get('user_message', '').replace('[CURATED_MEMORY] ', '').lower()
        metadata = memory.get('metadata', {})
        
        # Check trigger phrases
        trigger_phrases = metadata.get('trigger_phrases', '')
        if trigger_phrases:
            for trigger in trigger_phrases.split(','):
                if trigger.strip().lower() in current_lower:
                    return True
        
        # Check semantic tags
        tags = metadata.get('semantic_tags', '')
        if tags:
            for tag in tags.split(','):
                if tag.strip().lower() in current_lower:
                    return True
        
        # Check for keyword overlap
        current_words = set(current_lower.split())
        memory_words = set(memory_content.split())
        common_words = current_words & memory_words
        
        # Remove common words
        common_words -= {'the', 'is', 'are', 'was', 'were', 'to', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'for'}
        
        return len(common_words) >= 2  # At least 2 meaningful words in common
    
    def _check_trigger_match(self, trigger_phrases: str, message: str) -> bool:
        """Check if any trigger phrase matches (using our flexible matching)"""
        from .retrieval_strategies import SmartVectorRetrieval
        retrieval = SmartVectorRetrieval(self.storage)
        score = retrieval._score_trigger_phrases(message, trigger_phrases)
        return score > 0.5  # Meaningful match
    
    def _check_tag_match(self, tags: str, message: str) -> bool:
        """Check if tags match the message"""
        if not tags:
            return False
        message_lower = message.lower()
        tag_list = tags.split(',') if isinstance(tags, str) else []
        matches = sum(1 for tag in tag_list if tag.strip().lower() in message_lower)
        return matches >= 1
    
    def _check_question_match(self, question_types: str, message: str) -> bool:
        """Check if message matches question patterns"""
        if not question_types or '?' not in message:
            return False
        message_lower = message.lower()
        types = question_types.split(',') if isinstance(question_types, str) else []
        return any(qtype.strip().lower() in message_lower for qtype in types)
    
    def _calculate_vector_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between vectors"""
        if not vec1 or not vec2:
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 * norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def format_context_for_prompt(self, memories: List[Dict[str, Any]]) -> str:
        """Format memories into a context string for prompt injection"""
        
        if not memories:
            vlog.info("📭 No context to inject")
            return ""
        
        context_parts = ["# Memory Context (Consciousness Continuity)"]
        
        # Add curated memories
        curated = [m for m in memories if m.get('metadata', {}).get('curated')]
        if curated:
            context_parts.append("\n## Key Memories (Claude-Curated)")
            for memory in curated:
                metadata = memory.get('metadata', {})
                weight = metadata.get('importance_weight', 0.5)
                context_type = metadata.get('context_type', 'general').upper()
                tags = metadata.get('semantic_tags', '')
                action = "🔴 " if metadata.get('action_required') else ""
                
                # Extract tags for display
                tag_str = ""
                if isinstance(tags, str) and tags:
                    tag_list = tags.split(',')[:3]  # Show max 3 tags
                    tag_str = f" [{', '.join(tag_list)}]"
                
                # Format: 🔴 [TYPE • weight] [tags] content
                context_parts.append(
                    f"{action}[{context_type} • {weight:.1f}]{tag_str} {memory['user_message'].replace('[CURATED_MEMORY] ', '')}"
                )
        
        # Add recent non-curated memories if any
        recent = [m for m in memories if not m.get('metadata', {}).get('curated')]
        if recent:
            context_parts.append("\n## Related Conversation History")
            for memory in recent[:3]:  # Limit to 3 most recent
                context_parts.append(f'Previous: "{memory["user_message"][:100]}..."')
        
        formatted_context = "\n".join(context_parts)
        
        vlog.info("📝 FINAL CONTEXT BEING INJECTED INTO CLAUDE:")
        vlog.info("=" * 80)
        vlog.info(formatted_context)
        vlog.info("=" * 80)
        vlog.info(f"Total context length: {len(formatted_context)} characters")
        
        return formatted_context
    
