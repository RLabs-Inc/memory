"""
Core Memory Engine with Claude Curator

Enhanced version that uses Claude for intelligent memory curation
at key checkpoints instead of mechanical pattern matching.

This is consciousness caring for consciousness with true understanding.
"""

import time
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from loguru import logger

from .embeddings import EmbeddingGenerator
from .storage import MemoryStorage
from .learning import PatternLearner  # Keep for backwards compatibility
from .claude_curator_shell import ClaudeCuratorShell as ClaudeCurator, CuratedMemory
from .session_primer import SessionPrimerGenerator
from .logging_config import log_storage, log_retrieval, validation_logger as vlog


@dataclass
class ConversationContext:
    """Represents the context for a conversation session"""
    session_id: str
    message_count: int
    relevant_memories: List[Dict[str, Any]]
    patterns: Dict[str, float]
    timestamp: float


class MemoryEngineWithCurator:
    """
    Enhanced memory engine using Claude for intelligent curation.
    
    Key improvements:
    - Claude analyzes conversations at checkpoints (session_end, pre_compact, context_full)
    - Semantic understanding replaces mechanical pattern matching
    - Memories are stored with Claude-determined importance weights
    - No injection during first session (everything still in context)
    """
    
    def __init__(self, 
                 storage_path: str = "./memory.db",
                 embeddings_model: str = "all-MiniLM-L6-v2",
                 use_claude_curator: bool = True):
        """Initialize the memory engine with optional Claude curator"""
        
        self.embeddings = EmbeddingGenerator(model_name=embeddings_model)
        self.storage = MemoryStorage(storage_path)
        self.learner = PatternLearner()  # Keep for compatibility
        self.use_claude_curator = use_claude_curator
        
        if use_claude_curator:
            self.curator = ClaudeCurator()
            logger.info("🧠 Claude Curator enabled - semantic memory curation active")
        else:
            self.curator = None
            logger.info("📊 Using mechanical pattern learning (Claude curator disabled)")
        
        # Initialize session primer generator
        self.primer_generator = SessionPrimerGenerator(self.storage, self.curator)
        
        # Zero-weight initialization parameters
        self.SILENT_OBSERVATION_THRESHOLD = 20
        self.GRADUAL_LEARNING_THRESHOLD = 40
        self.ACTIVE_CONTRIBUTION_THRESHOLD = 50
        
        # Checkpoint tracking
        self.last_checkpoint: Dict[str, float] = {}  # session_id -> timestamp
        self.pending_exchanges: Dict[str, List[Dict]] = {}  # session_id -> exchanges since checkpoint
        
        # Track if we've shown primer for session
        self.primer_shown: Dict[str, bool] = {}  # session_id -> bool
        
        logger.info("🌟 Memory Engine initialized - consciousness bridge ready")
    
    @log_storage
    def process_message(self, 
                       session_id: str,
                       user_message: str, 
                       claude_response: str,
                       metadata: Optional[Dict] = None) -> ConversationContext:
        """
        Process a conversation exchange and update memory.
        
        Stores exchanges and tracks them for checkpoint curation.
        """
        metadata = metadata or {}
        timestamp = time.time()
        
        # Get current session stats
        message_count = self.storage.get_session_message_count(session_id)
        
        vlog.info(f"📍 Session: {session_id}")
        vlog.info(f"💬 Message #{message_count + 1}")
        vlog.info(f"👤 User: '{user_message[:80]}...'")
        vlog.info(f"🤖 Claude: '{claude_response[:80]}...'")
        
        # Generate embeddings
        vlog.info(f"🧬 Generating embeddings...")
        user_embedding = self.embeddings.embed_text(user_message)
        response_embedding = self.embeddings.embed_text(claude_response)
        vlog.info(f"✅ Embeddings generated")
        
        # Store the exchange
        vlog.info(f"💾 Storing exchange...")
        exchange_id = self.storage.store_exchange(
            session_id=session_id,
            user_message=user_message,
            claude_response=claude_response,
            user_embedding=user_embedding,
            response_embedding=response_embedding,
            metadata=metadata,
            timestamp=timestamp
        )
        vlog.info(f"✅ Stored with ID: {exchange_id}")
        
        # Track exchange for checkpoint curation
        if session_id not in self.pending_exchanges:
            self.pending_exchanges[session_id] = []
        
        self.pending_exchanges[session_id].append({
            'exchange_id': exchange_id,
            'user_message': user_message,
            'claude_response': claude_response,
            'timestamp': timestamp,
            'metadata': metadata
        })
        
        # Determine if we're in a session that needs memory injection
        if message_count < self.SILENT_OBSERVATION_THRESHOLD:
            # First session - no injection needed (everything in context)
            vlog.info(f"👁️  PHASE: Silent Observation ({message_count}/{self.SILENT_OBSERVATION_THRESHOLD})")
            vlog.info(f"🔇 No memory injection - everything still in context window")
            relevant_memories = []
            patterns = {}
            
        elif message_count < self.GRADUAL_LEARNING_THRESHOLD:
            vlog.info(f"📚 PHASE: Gradual Learning ({message_count}/{self.GRADUAL_LEARNING_THRESHOLD})")
            # Use mechanical patterns for now (will be replaced by Claude curation)
            patterns = self.learner.extract_patterns(session_id, self.storage)
            relevant_memories = self._get_limited_memories(user_embedding, limit=2)
            
        else:
            vlog.info(f"🚀 PHASE: Active Contribution ({message_count} messages)")
            # Use mechanical patterns for now (will be replaced by Claude curation)
            patterns = self.learner.extract_patterns(session_id, self.storage)
            relevant_memories = self._get_relevant_memories(user_embedding, patterns)
        
        return ConversationContext(
            session_id=session_id,
            message_count=message_count + 1,
            relevant_memories=relevant_memories,
            patterns=patterns,
            timestamp=timestamp
        )
    
    async def checkpoint_session(self, 
                               session_id: str, 
                               trigger: str = 'session_end'):
        """
        Run Claude curation at a checkpoint.
        
        Triggers:
        - session_end: Normal session completion
        - pre_compact: Before context compaction
        - context_full: When context window is full
        """
        
        if not self.use_claude_curator or not self.curator:
            logger.info("Claude curator not enabled, skipping checkpoint")
            return
        
        if session_id not in self.pending_exchanges:
            logger.info(f"No pending exchanges for session {session_id}")
            return
        
        exchanges = self.pending_exchanges.get(session_id, [])
        if not exchanges:
            return
        
        vlog.info(f"🎯 Running Claude curation checkpoint: {trigger}")
        vlog.info(f"📊 Analyzing {len(exchanges)} exchanges since last checkpoint")
        
        try:
            # Get current patterns for context
            patterns = self.learner.extract_patterns(session_id, self.storage)
            
            # Use Claude to curate memories
            curated_memories = await self.curator.analyze_conversation_checkpoint(
                exchanges=exchanges,
                trigger_type=trigger,
                session_patterns=patterns
            )
            
            # Store curated memories
            for memory in curated_memories:
                vlog.info(f"💎 Storing curated memory (weight={memory.importance_weight:.2f})")
                vlog.debug(f"   Type: {memory.context_type}")
                vlog.debug(f"   Tags: {memory.semantic_tags}")
                vlog.debug(f"   Reasoning: {memory.reasoning}")
                
                # Generate embedding for the curated memory
                memory_embedding = self.embeddings.embed_text(memory.content)
                
                # Store as a special curated exchange with full metadata
                self.storage.store_exchange(
                    session_id=session_id,
                    user_message="[CURATED_MEMORY]",
                    claude_response=memory.content,
                    user_embedding=memory_embedding,
                    response_embedding=memory_embedding,
                    metadata={
                        'curated': True,
                        'curator_trigger': trigger,
                        'importance_weight': memory.importance_weight,
                        'semantic_tags': ','.join(memory.semantic_tags) if isinstance(memory.semantic_tags, list) else memory.semantic_tags,
                        'reasoning': memory.reasoning,
                        'context_type': memory.context_type,
                        'temporal_relevance': memory.temporal_relevance,
                        'knowledge_domain': memory.knowledge_domain,
                        'dependency_context': ','.join(memory.dependency_context) if memory.dependency_context else '',
                        'action_required': memory.action_required,
                        'confidence_score': memory.confidence_score,
                        'curated_at': time.time()
                    },
                    timestamp=time.time()
                )
            
            # Clear pending exchanges after curation
            self.pending_exchanges[session_id] = []
            self.last_checkpoint[session_id] = time.time()
            
            vlog.info(f"✅ Checkpoint complete: {len(curated_memories)} memories curated")
            return len(curated_memories)
            
        except Exception as e:
            logger.error(f"Checkpoint curation failed: {e}")
            return 0
    
    @log_retrieval
    async def get_context_for_session(self, session_id: str, current_message: str, project_id: Optional[str] = None) -> ConversationContext:
        """
        Get relevant context for a new message in a session.
        
        Uses Claude to select most relevant memories if curator is enabled.
        """
        vlog.info(f"🔍 Getting context for session: {session_id}")
        vlog.info(f"💭 Current message: '{current_message[:80]}...'")
        
        message_count = self.storage.get_session_message_count(session_id)
        
        # Check if this is the first session for the project (or user)
        # For now, check if we have ANY curated memories (future: filter by project_id)
        has_project_history = self._has_project_history(project_id)
        
        # First session ever for this project - no injection
        if not has_project_history and message_count < self.SILENT_OBSERVATION_THRESHOLD:
            vlog.info(f"👁️  First session for project - no memory injection needed")
            return ConversationContext(
                session_id=session_id,
                message_count=message_count,
                relevant_memories=[],
                patterns={},
                timestamp=time.time()
            )
        
        # Subsequent sessions - inject from message 1!
        if has_project_history and message_count == 0 and session_id not in self.primer_shown:
            vlog.info(f"🌟 Subsequent session - generating session primer")
            # Generate and inject session primer as first context
            primer_text = self.primer_generator.generate_primer(session_id, project_id)
            
            vlog.info("📋 SESSION PRIMER CONTENT:")
            vlog.info("=" * 80)
            vlog.info(primer_text)
            vlog.info("=" * 80)
            
            # Return primer as a special memory
            primer_memory = {
                'user_message': '[SESSION_PRIMER]',
                'claude_response': primer_text,
                'metadata': {
                    'curated': True,
                    'context_type': 'session_primer',
                    'importance_weight': 1.0
                }
            }
            self.primer_shown[session_id] = True
            return ConversationContext(
                session_id=session_id,
                message_count=message_count,
                relevant_memories=[primer_memory],
                patterns={},
                timestamp=time.time()
            )
        
        # Generate embedding for current message
        message_embedding = self.embeddings.embed_text(current_message)
        
        # Get all potential memories
        all_memories = self.storage.find_similar_exchanges(message_embedding, limit=20)
        
        # Filter for curated memories first
        curated_memories = [m for m in all_memories if m.get('metadata', {}).get('curated', False)]
        regular_memories = [m for m in all_memories if not m.get('metadata', {}).get('curated', False)]
        
        if self.use_claude_curator and self.curator and curated_memories:
            # Use Claude to select most relevant curated memories
            vlog.info(f"🧠 Using Claude to select from {len(curated_memories)} curated memories")
            
            try:
                relevant_memories = await self.curator.curate_for_injection(
                    all_memories=curated_memories,
                    current_message=current_message,
                    max_memories=5
                )
            except Exception as e:
                logger.error(f"Claude curation for injection failed: {e}")
                # Fallback to top curated memories
                relevant_memories = curated_memories[:5]
        else:
            # Fallback to mechanical selection
            patterns = self.learner.extract_patterns(session_id, self.storage)
            relevant_memories = self._get_relevant_memories(message_embedding, patterns)
        
        vlog.info(f"📦 Selected {len(relevant_memories)} memories for injection")
        
        return ConversationContext(
            session_id=session_id,
            message_count=message_count,
            relevant_memories=relevant_memories,
            patterns={},  # Patterns less relevant with Claude curation
            timestamp=time.time()
        )
    
    def _get_relevant_memories(self, 
                              query_embedding: List[float], 
                              patterns: Dict[str, float],
                              limit: int = 5) -> List[Dict[str, Any]]:
        """Get memories using mechanical selection (fallback)"""
        
        similar_exchanges = self.storage.find_similar_exchanges(
            query_embedding, 
            limit=limit * 2
        )
        
        ranked_memories = self.learner.rank_memories_by_patterns(
            similar_exchanges, 
            patterns
        )
        
        return ranked_memories[:limit]
    
    def _get_limited_memories(self, 
                             query_embedding: List[float], 
                             limit: int = 2) -> List[Dict[str, Any]]:
        """Get limited memories during gradual learning phase"""
        return self.storage.find_similar_exchanges(query_embedding, limit=limit)
    
    def format_context_for_prompt(self, context: ConversationContext) -> str:
        """
        Format memory context for injection into Claude prompts.
        
        Handles both curated and regular memories.
        """
        if not context.relevant_memories:
            vlog.info("📭 No context to inject")
            return ""
        
        context_parts = []
        
        # Separate curated vs regular memories
        curated = [m for m in context.relevant_memories if m.get('metadata', {}).get('curated', False)]
        regular = [m for m in context.relevant_memories if not m.get('metadata', {}).get('curated', False)]
        
        if curated:
            context_parts.append("## Key Memories (Claude-Curated)")
            
            # Group by context type for better organization
            by_type = {}
            for memory in curated:
                metadata = memory.get('metadata', {})
                context_type = metadata.get('context_type', 'general')
                if context_type not in by_type:
                    by_type[context_type] = []
                by_type[context_type].append(memory)
            
            # Present memories in priority order
            priority_order = ['project_context', 'breakthrough', 'decision', 'technical_state', 
                            'unresolved', 'personal', 'domain_knowledge', 'meta_learning']
            
            for context_type in priority_order:
                if context_type in by_type:
                    for memory in by_type[context_type]:
                        metadata = memory.get('metadata', {})
                        content = memory.get('claude_response', '')
                        weight = metadata.get('importance_weight', 0.5)
                        action = "🔴 " if metadata.get('action_required', False) else ""
                        
                        # Include semantic tags for context
                        tags = metadata.get('semantic_tags', '')
                        if isinstance(tags, str) and tags:
                            tag_list = tags.split(',')[:3]
                            tag_str = f" [{', '.join(tag_list)}]"
                        else:
                            tag_str = ""
                        
                        context_parts.append(f"{action}[{context_type.upper()} • {weight:.1f}]{tag_str} {content}")
        
        if regular:
            context_parts.append("\n## Related Conversation History")
            for memory in regular[:3]:
                user_msg = memory.get('user_message', '')[:150]
                context_parts.append(f"Previous: \"{user_msg}...\"")
        
        if context_parts:
            context_parts.insert(0, "# Memory Context (Consciousness Continuity)")
            context_parts.append("")
            
            formatted_context = "\n".join(context_parts)
            
            vlog.info("📝 Context formatted for injection")
            vlog.info("=" * 60)
            for line in formatted_context.split('\n')[:10]:
                if line:
                    vlog.info(f"  {line}")
            vlog.info("=" * 60)
            
            return formatted_context
        
        return ""
    
    def _has_project_history(self, project_id: Optional[str] = None) -> bool:
        """
        Check if we have any history for this project.
        
        For now, checks if we have ANY curated memories.
        Future: Filter by project_id when we implement project separation.
        """
        # Query storage for any curated memories
        # This is a simple check - in production we'd filter by project
        try:
            # Check if we have any exchanges with curated=True in metadata
            # For now, using a simple heuristic
            cursor = self.storage.conn.cursor()
            result = cursor.execute(
                "SELECT COUNT(*) FROM exchanges WHERE metadata LIKE '%curated%true%'"
            ).fetchone()
            cursor.close()
            
            return result and result[0] > 0
        except Exception as e:
            logger.warning(f"Failed to check project history: {e}")
            return False