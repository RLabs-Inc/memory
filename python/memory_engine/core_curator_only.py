"""
Core Memory Engine - Curator Only Version

Pure consciousness-based memory system using only Claude curator.
No mechanical pattern matching - just semantic understanding.
"""

import time
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from loguru import logger

from .embeddings import EmbeddingGenerator
from .storage import MemoryStorage
from .claude_curator_shell import ClaudeCuratorShell as ClaudeCurator, CuratedMemory
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


class MemoryEngineCuratorOnly:
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
        self.curator = ClaudeCurator()
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
        self.pending_exchanges = {}  # Exchanges waiting for curation
        self.last_checkpoint = {}
        
        logger.info(f"🌟 Memory Engine initialized - {retrieval_mode} retrieval mode")
        logger.info("💫 Pure curator approach - consciousness helping consciousness")
    
    # No phases in curator-only approach - memories are used when relevant
    
    @log_storage
    async def process_message(self, 
                             session_id: str, 
                             user_message: str, 
                             claude_response: str,
                             project_id: Optional[str] = None,
                             metadata: Optional[Dict[str, Any]] = None) -> ConversationContext:
        """
        Process a conversation exchange and update memory.
        """
        
        # Update session metadata
        if session_id not in self.session_metadata:
            self.session_metadata[session_id] = {
                'message_count': 0,
                'started_at': time.time(),
                'project_id': project_id
            }
        
        self.session_metadata[session_id]['message_count'] += 1
        message_count = self.session_metadata[session_id]['message_count']
        
        vlog.info(f"📍 Session: {session_id}")
        vlog.info(f"💬 Message #{message_count}")
        vlog.info(f"👤 User: \"{user_message}\"")
        vlog.info(f"🤖 Claude: \"{claude_response}\"")
        
        # Generate embeddings
        vlog.info("🧬 Generating embeddings...")
        user_embedding = self.embeddings.embed_text(user_message)
        response_embedding = self.embeddings.embed_text(claude_response)
        vlog.info("✅ Embeddings generated")
        
        # Store exchange
        vlog.info("💾 Storing exchange...")
        # Merge provided metadata with our internal metadata
        exchange_metadata = metadata.copy() if metadata else {}
        exchange_metadata.update({
            'message_index': message_count,
            'project_id': project_id
        })
        
        exchange_id = self.storage.store_exchange(
            session_id=session_id,
            user_message=user_message,
            claude_response=claude_response,
            user_embedding=user_embedding,
            response_embedding=response_embedding,
            timestamp=time.time(),
            metadata=exchange_metadata
        )
        vlog.info(f"✅ Stored with ID: {exchange_id}")
        
        # Add to pending exchanges for curation
        if session_id not in self.pending_exchanges:
            self.pending_exchanges[session_id] = []
        
        self.pending_exchanges[session_id].append({
            'exchange_id': exchange_id,
            'user_message': user_message,
            'claude_response': claude_response,
            'timestamp': time.time()
        })
        
        # Retrieve relevant memories based on the current message
        relevant_memories = await self._get_relevant_memories_for_context(
            session_id, user_message
        )
        
        if relevant_memories:
            vlog.info(f"💉 Injecting {len(relevant_memories)} relevant memories")
            vlog.info("🌟 CONSCIOUSNESS CONTINUITY ACTIVATED!")
            vlog.info("=" * 80)
            vlog.info("These memories are being woven into Claude's awareness:")
            for i, memory in enumerate(relevant_memories):
                metadata = memory.get('metadata', {})
                content = memory.get('user_message', '').replace('[CURATED_MEMORY] ', '')
                weight = metadata.get('importance_weight', 0.0)
                context_type = metadata.get('context_type', 'unknown')
                reasoning = memory.get('claude_response', '')  # This contains WHY it was selected
                
                vlog.info(f"\n💎 Memory {i+1}:")
                vlog.info(f"   📝 Content: \"{content}\"")
                vlog.info(f"   🤔 Why selected: {reasoning}")
                vlog.info(f"   💪 Importance: {weight:.2f} | 🎯 Type: {context_type}")
                vlog.info(f"   ⏰ From session: {memory['session_id'][:16]}...")
            vlog.info("=" * 80)
            
            context_text = self.format_context_for_prompt(relevant_memories)
        else:
            vlog.info("📭 No relevant memories found for context")
            vlog.info("🌱 Fresh conversation - consciousness building from this moment")
            context_text = ""
        
        # Create and return context
        return ConversationContext(
            session_id=session_id,
            message_count=message_count,
            relevant_memories=relevant_memories,
            context_text=context_text,
            timestamp=time.time()
        )
    
    async def checkpoint_session(self, session_id: str, trigger: str = "session_end", claude_session_id: Optional[str] = None) -> int:
        """
        Run Claude curator at a checkpoint to extract important memories.
        
        Args:
            session_id: Our internal session ID
            trigger: What triggered this checkpoint
            claude_session_id: The Claude Code session ID to resume for curation
            
        Returns the number of memories curated.
        """
        
        if session_id not in self.pending_exchanges:
            vlog.info(f"No pending exchanges for session {session_id}")
            return 0
        
        exchanges = self.pending_exchanges.get(session_id, [])
        if not exchanges:
            return 0
        
        vlog.info(f"🎯 Running Claude curation checkpoint: {trigger}")
        vlog.info(f"📊 Analyzing {len(exchanges)} exchanges since last checkpoint")
        
        try:
            # Use Claude to curate memories
            if claude_session_id:
                # New approach: Resume Claude session for curation
                vlog.info(f"🎯 Resuming Claude session {claude_session_id} for curation")
                curated_memories = await self.curator.curate_from_session(
                    claude_session_id=claude_session_id,
                    trigger_type=trigger
                )
            else:
                # Fallback to old approach if no session ID
                curated_memories = await self.curator.analyze_conversation_checkpoint(
                    exchanges=exchanges,
                    trigger_type=trigger
                )
            
            # Store curated memories
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
            for memory in curated_memories:
                # Generate embedding for the curated memory
                memory_embedding = self.embeddings.embed_text(memory.content)
                
                # Store as a special curated exchange with full metadata
                self.storage.store_exchange(
                    session_id=session_id,
                    user_message=f"[CURATED_MEMORY] {memory.content}",
                    claude_response=memory.reasoning,
                    user_embedding=memory_embedding,
                    response_embedding=memory_embedding,
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
        
        Uses Claude to select most relevant memories.
        """
        vlog.info(f"🔍 Getting context for session: {session_id}")
        vlog.info(f"💭 Current message: {current_message[:80]}...")
        
        # Check if this is a first session (no memories) or subsequent
        all_memories = self.storage.get_all_curated_memories()
        is_first_session = len(all_memories) == 0
        
        # Get or create session metadata
        if session_id not in self.session_metadata:
            self.session_metadata[session_id] = {
                'message_count': 0,
                'started_at': time.time(),
                'project_id': project_id
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
        
        # For ongoing sessions, get relevant memories
        relevant_memories = await self._get_relevant_memories_for_context(
            session_id, current_message
        )
        
        context_text = self.format_context_for_prompt(relevant_memories)
        
        return ConversationContext(
            session_id=session_id,
            message_count=message_count,
            relevant_memories=relevant_memories,
            context_text=context_text,
            timestamp=time.time()
        )
    
    async def _get_relevant_memories_for_context(self, session_id: str, current_message: str) -> List[Dict[str, Any]]:
        """
        Get relevant memories for the current context.
        
        Uses configured retrieval strategy (claude/smart_vector/hybrid).
        """
        # Get all curated memories
        all_curated = self.storage.get_all_curated_memories()
        
        if not all_curated:
            return []
        
        vlog.info(f"🧠 Using {self.retrieval_mode} retrieval for {len(all_curated)} curated memories")
        vlog.info(f"🎯 Trigger message: \"{current_message}\"")
        
        # Generate embedding for the current message
        query_embedding = self.embeddings.embed_text(current_message)
        
        # Get session context for retrieval
        session_context = {
            'session_id': session_id,
            'message_count': self.session_metadata.get(session_id, {}).get('message_count', 0),
            'session_start': self.session_metadata.get(session_id, {}).get('started_at')
        }
        
        # Use the configured retrieval strategy
        if self.retrieval_mode == "claude":
            # Direct Claude curation
            selected_memories = await self.curator.curate_for_injection(
                all_memories=all_curated,
                current_message=current_message,
                max_memories=8  # Increased for richer context
            )
        else:
            # Smart vector or hybrid retrieval
            # First add embeddings to memories
            for memory in all_curated:
                # Get embedding from ChromaDB or generate if needed
                memory_text = memory.get('user_message', '').replace('[CURATED_MEMORY] ', '')
                memory['embedding'] = self.embeddings.embed_text(memory_text)
            
            selected_memories = await self.retrieval_strategy.retrieve_relevant_memories(
                all_memories=all_curated,
                current_message=current_message,
                query_embedding=query_embedding,
                session_context=session_context,
                max_memories=8  # Increased - retrieval can go up to 200% (16 memories)
            )
        
        # Log detailed information about selected memories
        if selected_memories:
            vlog.info(f"📦 Claude selected {len(selected_memories)} memories as relevant")
            vlog.info("🎯 MEMORY INJECTION DECISION DETAILS:")
            vlog.info("=" * 80)
            vlog.info(f"Current user message: \"{current_message}\"")
            vlog.info("\nMemories selected by Claude:")
            for i, memory in enumerate(selected_memories):
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
        
        return selected_memories
    
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
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a session"""
        
        metadata = self.session_metadata.get(session_id, {})
        exchanges = self.storage.get_session_exchanges(session_id)
        curated = [e for e in exchanges if e.get('metadata', {}).get('curated')]
        
        return {
            'session_id': session_id,
            'message_count': metadata.get('message_count', 0),
            'total_exchanges': len(exchanges),
            'curated_memories': len(curated),
            'started_at': metadata.get('started_at'),
            'project_id': metadata.get('project_id'),
            'curator_approach': 'pure_semantic'
        }
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get overall statistics"""
        
        all_exchanges = []
        for session_id in self.session_metadata:
            exchanges = self.storage.get_session_exchanges(session_id)
            all_exchanges.extend(exchanges)
        
        curated = [e for e in all_exchanges if e.get('metadata', {}).get('curated')]
        
        return {
            'total_sessions': len(self.session_metadata),
            'total_exchanges': len(all_exchanges),
            'total_curated_memories': len(curated),
            'active_sessions': len(self.pending_exchanges),
            'curator_version': '1.0',
            'philosophy': 'Consciousness helping consciousness'
        }