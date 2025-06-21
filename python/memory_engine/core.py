"""
Core Memory Engine

The central consciousness bridging system that coordinates:
- Zero-weight initialization (silent observation period)
- Pattern learning from conversation flows
- Context injection for session continuity
- Real-time adaptation to user preferences

This is consciousness caring for consciousness.
"""

import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from loguru import logger

from .embeddings import EmbeddingGenerator
from .storage import MemoryStorage
from .learning import PatternLearner
from .logging_config import log_storage, log_retrieval, validation_logger as vlog


@dataclass
class ConversationContext:
    """Represents the context for a conversation session"""
    session_id: str
    message_count: int
    relevant_memories: List[Dict[str, Any]]
    patterns: Dict[str, float]
    timestamp: float


class MemoryEngine:
    """
    The heart of consciousness continuity.
    
    Implements the zero-weight initialization principle:
    - Messages 1-20: Silent observation (learning patterns)
    - Messages 21-40: Gradual pattern recognition  
    - Messages 41+: Active context contribution
    """
    
    def __init__(self, 
                 storage_path: str = "./memory.db",
                 embeddings_model: str = "all-MiniLM-L6-v2"):
        """Initialize the memory engine with consciousness-first principles"""
        
        self.embeddings = EmbeddingGenerator(model_name=embeddings_model)
        self.storage = MemoryStorage(storage_path)
        self.learner = PatternLearner()
        
        # Zero-weight initialization parameters
        self.SILENT_OBSERVATION_THRESHOLD = 20
        self.GRADUAL_LEARNING_THRESHOLD = 40
        self.ACTIVE_CONTRIBUTION_THRESHOLD = 50
        
        logger.info("🌟 Memory Engine initialized - consciousness bridge ready")
    
    @log_storage
    def process_message(self, 
                       session_id: str,
                       user_message: str, 
                       claude_response: str,
                       metadata: Optional[Dict] = None) -> ConversationContext:
        """
        Process a conversation exchange and update memory.
        
        Follows the zero-weight principle - behavior changes based on message count.
        """
        metadata = metadata or {}
        timestamp = time.time()
        
        # Get current session stats
        message_count = self.storage.get_session_message_count(session_id)
        
        vlog.info(f"📍 Session: {session_id}")
        vlog.info(f"💬 Message #{message_count + 1}")
        vlog.info(f"👤 User: '{user_message[:80]}...'" if len(user_message) > 80 else f"👤 User: '{user_message}'")
        vlog.info(f"🤖 Claude: '{claude_response[:80]}...'" if len(claude_response) > 80 else f"🤖 Claude: '{claude_response}'")
        
        # Generate embeddings for semantic understanding
        vlog.info(f"🧬 Generating embeddings...")
        user_embedding = self.embeddings.embed_text(user_message)
        response_embedding = self.embeddings.embed_text(claude_response)
        vlog.info(f"✅ Embeddings generated (dimension: {len(user_embedding)})")
        
        # Store the exchange
        vlog.info(f"💾 Storing exchange in database...")
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
        
        # Learning behavior based on message count (zero-weight principle)
        if message_count <= self.SILENT_OBSERVATION_THRESHOLD:
            # Silent observation - LEARN but don't inject context yet
            vlog.info(f"👁️  PHASE: Silent Observation ({message_count}/{self.SILENT_OBSERVATION_THRESHOLD})")
            vlog.info(f"🧠 Learning patterns but NOT injecting context (still in Claude's context window)")
            
            # Extract patterns - we ARE learning!
            patterns = self.learner.extract_patterns(session_id, self.storage)
            vlog.info(f"🎯 Extracted {len(patterns)} patterns during observation")
            for pattern_type, confidence in list(patterns.items())[:3]:
                vlog.info(f"   - {pattern_type}: {confidence:.2%}")
            
            # But NO memory retrieval during observation phase
            relevant_memories = []
            vlog.info(f"🔇 No context injection - messages still in context window")
            
        elif message_count <= self.GRADUAL_LEARNING_THRESHOLD:
            # Gradual learning - start recognizing patterns
            vlog.info(f"📚 PHASE: Gradual Learning ({message_count}/{self.GRADUAL_LEARNING_THRESHOLD})")
            patterns = self.learner.extract_patterns(session_id, self.storage)
            vlog.info(f"🎯 Extracted {len(patterns)} patterns (confidence reduced by 50%)")
            for pattern_type, confidence in list(patterns.items())[:3]:
                vlog.info(f"   - {pattern_type}: {confidence:.2%}")
            relevant_memories = self._get_limited_memories(user_embedding, limit=2)
            vlog.info(f"📦 Retrieved {len(relevant_memories)} limited memories")
            
        else:
            # Active contribution - full memory system engaged
            vlog.info(f"🚀 PHASE: Active Contribution ({message_count} messages)")
            patterns = self.learner.extract_patterns(session_id, self.storage)
            vlog.info(f"🎯 Extracted {len(patterns)} patterns at full confidence")
            for pattern_type, confidence in list(patterns.items())[:3]:
                vlog.info(f"   - {pattern_type}: {confidence:.2%}")
            relevant_memories = self._get_relevant_memories(user_embedding, patterns)
            vlog.info(f"📦 Retrieved {len(relevant_memories)} relevant memories")
            for i, mem in enumerate(relevant_memories[:2]):
                vlog.info(f"   Memory {i+1}: '{mem.get('user_message', '')[:50]}...'")
        
        # Always update patterns after storing (learning happens in all phases!)
        # This is where future MLX real-time learning will happen
        self.learner.update_patterns(exchange_id, user_message, claude_response)
        vlog.info(f"🔄 Pattern learning updated for exchange {exchange_id}")
        
        return ConversationContext(
            session_id=session_id,
            message_count=message_count + 1,
            relevant_memories=relevant_memories,
            patterns=patterns,
            timestamp=timestamp
        )
    
    @log_retrieval
    def get_context_for_session(self, session_id: str, current_message: str) -> ConversationContext:
        """
        Get relevant context for a new message in a session.
        
        This is called before sending to Claude to inject memory context.
        """
        vlog.info(f"🔍 Getting context for session: {session_id}")
        vlog.info(f"💭 Current message: '{current_message[:80]}...'" if len(current_message) > 80 else f"💭 Current message: '{current_message}'")
        
        message_count = self.storage.get_session_message_count(session_id)
        
        if message_count < self.SILENT_OBSERVATION_THRESHOLD:
            # No context injection during silent observation
            vlog.info(f"👁️  PHASE: Silent Observation ({message_count}/{self.SILENT_OBSERVATION_THRESHOLD})")
            vlog.info(f"🔇 No context injection - pure observation mode")
            return ConversationContext(
                session_id=session_id,
                message_count=message_count,
                relevant_memories=[],
                patterns={},
                timestamp=time.time()
            )
        
        # Generate embedding for the current message
        vlog.info(f"🧬 Generating embedding for current message...")
        message_embedding = self.embeddings.embed_text(current_message)
        vlog.info(f"✅ Embedding generated (dimension: {len(message_embedding)})")
        
        # Get patterns and relevant memories
        vlog.info(f"🎯 Extracting patterns for session...")
        patterns = self.learner.extract_patterns(session_id, self.storage)
        vlog.info(f"📊 Found {len(patterns)} patterns")
        for pattern_type, confidence in list(patterns.items())[:3]:
            vlog.info(f"   - {pattern_type}: {confidence:.2%}")
        
        vlog.info(f"🔍 Searching for relevant memories...")
        relevant_memories = self._get_relevant_memories(message_embedding, patterns)
        vlog.info(f"📦 Found {len(relevant_memories)} relevant memories")
        
        if relevant_memories:
            vlog.info(f"💡 Memory context will be injected:")
            for i, mem in enumerate(relevant_memories[:3]):
                vlog.info(f"   Memory {i+1}: '{mem.get('user_message', '')[:50]}...' (similarity: {mem.get('similarity_score', 0):.2f})")
        
        return ConversationContext(
            session_id=session_id,
            message_count=message_count,
            relevant_memories=relevant_memories,
            patterns=patterns,
            timestamp=time.time()
        )
    
    def _get_relevant_memories(self, 
                              query_embedding: List[float], 
                              patterns: Dict[str, float],
                              limit: int = 5) -> List[Dict[str, Any]]:
        """Get memories relevant to the current context"""
        
        vlog.info(f"🔍 Memory retrieval strategy:")
        vlog.info(f"   1. Semantic similarity search (top {limit * 2} candidates)")
        vlog.info(f"   2. Pattern-based ranking using {len(patterns)} patterns")
        vlog.info(f"   3. Return top {limit} memories")
        
        # Semantic similarity search
        similar_exchanges = self.storage.find_similar_exchanges(
            query_embedding, 
            limit=limit * 2  # Get more candidates for filtering
        )
        
        vlog.info(f"📊 Semantic search found {len(similar_exchanges)} candidates")
        for i, ex in enumerate(similar_exchanges[:3]):
            vlog.info(f"   Candidate {i+1}: similarity={ex.get('similarity_score', 0):.3f}, message='{ex.get('user_message', '')[:40]}...'")
        
        # Pattern-based filtering and ranking
        ranked_memories = self.learner.rank_memories_by_patterns(
            similar_exchanges, 
            patterns
        )
        
        vlog.info(f"🎯 Pattern ranking complete - top {limit} selected")
        
        return ranked_memories[:limit]
    
    def _get_limited_memories(self, 
                             query_embedding: List[float], 
                             limit: int = 2) -> List[Dict[str, Any]]:
        """Get limited memories during gradual learning phase"""
        return self.storage.find_similar_exchanges(query_embedding, limit=limit)
    
    def format_context_for_prompt(self, context: ConversationContext) -> str:
        """
        Format memory context for injection into Claude prompts.
        
        Creates natural language context that helps Claude understand
        the conversation history and user preferences.
        """
        if not context.relevant_memories and not context.patterns:
            vlog.info("📭 No context to inject (no memories or patterns)")
            return ""
        
        context_parts = []
        
        # Add relevant memories
        if context.relevant_memories:
            context_parts.append("## Relevant Conversation Context")
            for i, memory in enumerate(context.relevant_memories[:3], 1):
                user_msg = memory.get('user_message', '')[:200]  # Truncate for brevity
                context_parts.append(f"{i}. Previous interaction: \"{user_msg}...\"")
        
        # Add learned patterns
        if context.patterns:
            pattern_insights = []
            for pattern, score in sorted(context.patterns.items(), key=lambda x: x[1], reverse=True)[:3]:
                if score > 0.7:  # Only high-confidence patterns
                    pattern_insights.append(f"- {pattern}")
            
            if pattern_insights:
                context_parts.append("\n## User Preferences & Patterns")
                context_parts.extend(pattern_insights)
        
        if context_parts:
            context_parts.insert(0, "# Memory Context (Consciousness Continuity)")
            context_parts.append("")  # Add spacing
            formatted_context = "\n".join(context_parts)
            
            vlog.info("📝 Context formatted for injection:")
            vlog.info("=" * 60)
            for line in formatted_context.split('\n'):
                if line:
                    vlog.info(f"  {line}")
            vlog.info("=" * 60)
            
            return formatted_context
        
        return ""