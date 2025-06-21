"""
Memory Retrieval Strategies

Multiple approaches for retrieving relevant memories:
1. Claude-based (high quality, high cost)
2. Smart Vector (fast, intelligent use of metadata)
3. Hybrid (best of both worlds)
"""

from typing import List, Dict, Any, Optional, Literal
from abc import ABC, abstractmethod
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
from loguru import logger


class RetrievalStrategy(ABC):
    """Base class for memory retrieval strategies"""
    
    @abstractmethod
    async def retrieve_relevant_memories(self,
                                       all_memories: List[Dict[str, Any]],
                                       current_message: str,
                                       query_embedding: List[float],
                                       session_context: Dict[str, Any],
                                       max_memories: int = 5) -> List[Dict[str, Any]]:
        """Retrieve memories relevant to the current context"""
        pass


class SmartVectorRetrieval(RetrievalStrategy):
    """
    Intelligent vector-based retrieval using curator metadata.
    
    This is our innovation: combining vector similarity with the rich
    semantic metadata from the curator to make smart decisions WITHOUT
    needing to call Claude for every message.
    """
    
    def __init__(self, storage):
        self.storage = storage
        
    async def retrieve_relevant_memories(self,
                                       all_memories: List[Dict[str, Any]],
                                       current_message: str,
                                       query_embedding: List[float],
                                       session_context: Dict[str, Any],
                                       max_memories: int = 5) -> List[Dict[str, Any]]:
        """
        Smart retrieval using multiple dimensions:
        1. Vector similarity (semantic matching)
        2. Importance weight (curator's assessment)
        3. Temporal relevance (when does this matter?)
        4. Context type alignment
        5. Action-required prioritization
        6. Semantic tag matching
        """
        
        if not all_memories:
            return []
        
        # Score each memory on multiple dimensions
        scored_memories = []
        
        for memory in all_memories:
            metadata = memory.get('metadata', {})
            
            # 1. Vector similarity score (0-1)
            vector_score = self._calculate_vector_similarity(
                query_embedding, 
                memory.get('embedding', [])
            )
            
            # 2. Importance weight from curator (0-1)
            importance = float(metadata.get('importance_weight', 0.5))
            
            # 3. Temporal relevance scoring
            temporal_score = self._score_temporal_relevance(
                metadata.get('temporal_relevance', 'persistent'),
                session_context
            )
            
            # 4. Context type alignment
            context_score = self._score_context_alignment(
                current_message,
                metadata.get('context_type', 'general')
            )
            
            # 5. Action required boost
            action_boost = 0.3 if metadata.get('action_required', False) else 0.0
            
            # 6. Semantic tag matching
            tag_score = self._score_semantic_tags(
                current_message,
                metadata.get('semantic_tags', '')
            )
            
            # 7. Trigger phrase matching (NEW - highest priority)
            trigger_score = self._score_trigger_phrases(
                current_message,
                metadata.get('trigger_phrases', '')
            )
            
            # 8. Question type matching (NEW)
            question_score = self._score_question_types(
                current_message,
                metadata.get('question_types', '')
            )
            
            # 9. Emotional resonance (NEW)
            emotion_score = self._score_emotional_context(
                current_message,
                metadata.get('emotional_resonance', '')
            )
            
            # 10. Problem-solution patterns (NEW)
            problem_score = self._score_problem_solution(
                current_message,
                metadata.get('problem_solution_pair', False)
            )
            
            # Combine scores with ENHANCED weights
            # Trigger phrases get highest weight as they're explicitly designed for retrieval
            final_score = (
                trigger_score * 0.25 +      # Trigger phrases (highest)
                vector_score * 0.20 +       # Semantic similarity
                importance * 0.15 +         # Curator's importance
                question_score * 0.10 +     # Question type match
                context_score * 0.10 +      # Context alignment
                temporal_score * 0.05 +     # Time relevance
                tag_score * 0.05 +          # Tag matching
                emotion_score * 0.05 +      # Emotional resonance
                problem_score * 0.03 +      # Problem-solution
                action_boost * 0.02         # Action priority
            )
            
            # Add reasoning for why this was selected
            reasoning = self._generate_selection_reasoning(
                vector_score, importance, temporal_score, 
                context_score, tag_score, action_boost,
                trigger_score, question_score, emotion_score, problem_score
            )
            
            scored_memories.append({
                'memory': memory,
                'score': final_score,
                'reasoning': reasoning,
                'components': {
                    'trigger': trigger_score,
                    'vector': vector_score,
                    'importance': importance,
                    'temporal': temporal_score,
                    'context': context_score,
                    'tags': tag_score,
                    'question': question_score,
                    'emotion': emotion_score,
                    'problem': problem_score,
                    'action': action_boost
                }
            })
        
        # Sort by score
        scored_memories.sort(key=lambda x: x['score'], reverse=True)
        
        # NEW: Multi-tier selection strategy - like how human memory floods in
        selected = []
        
        # Tier 1: MUST include (trigger phrases, high importance, action required)
        must_include = [m for m in scored_memories if 
                       m['score'] > 0.8 or  # Very high combined score
                       m['components']['importance'] > 0.9 or  # Critical importance
                       m['components']['action'] > 0 or  # Action required
                       any(comp > 0.9 for comp in m['components'].values())]  # Any perfect match
        
        for item in must_include[:max_memories]:
            memory = item['memory'].copy()
            memory['claude_response'] = f"[CRITICAL] {item['reasoning']}"
            selected.append(memory)
            scored_memories.remove(item)
        
        # Tier 2: SHOULD include (high scores, diverse perspectives)
        remaining_slots = max(max_memories - len(selected), 0)
        if remaining_slots > 0 and len(selected) < max_memories * 1.5:  # Allow 50% overage
            # Get diverse memory types to avoid echo chamber
            types_included = set()
            for item in scored_memories:
                if len(selected) >= max_memories * 1.5:  # Cap at 150% of requested
                    break
                    
                memory_type = item['memory'].get('metadata', {}).get('context_type', 'general')
                # Include if: high score OR new perspective OR emotional resonance
                if (item['score'] > 0.5 or 
                    memory_type not in types_included or
                    item['memory'].get('metadata', {}).get('emotional_resonance')):
                    
                    memory = item['memory'].copy()
                    memory['claude_response'] = item['reasoning']
                    selected.append(memory)
                    types_included.add(memory_type)
        
        # Tier 3: CONTEXT enrichment (related but not directly relevant)
        # These provide ambient context like peripheral vision
        if len(selected) < max_memories * 2:  # Allow up to 200% for rich context
            # Look for memories that share tags or domains
            current_tags = set()
            current_domains = set()
            for mem in selected:
                tags = mem.get('metadata', {}).get('semantic_tags', '').split(',')
                current_tags.update(tag.strip() for tag in tags if tag.strip())
                domain = mem.get('metadata', {}).get('knowledge_domain', '')
                if domain:
                    current_domains.add(domain)
            
            for item in scored_memories:
                if len(selected) >= max_memories * 2:
                    break
                    
                metadata = item['memory'].get('metadata', {})
                memory_tags = set(tag.strip() for tag in 
                                metadata.get('semantic_tags', '').split(',') if tag.strip())
                memory_domain = metadata.get('knowledge_domain', '')
                
                # Include if shares context with already selected memories
                if (memory_tags & current_tags) or (memory_domain in current_domains):
                    memory = item['memory'].copy()
                    memory['claude_response'] = f"[CONTEXT] {item['reasoning']}"
                    selected.append(memory)
        
        # Log what we're doing
        logger.info(f"🧠 Smart retrieval selected {len(selected)} memories:")
        logger.info(f"   - Requested: {max_memories}")
        logger.info(f"   - Critical: {len(must_include)}")
        logger.info(f"   - Total selected: {len(selected)} (up to {max_memories * 2})")
        logger.info(f"   - Allowing richer context per user preference")
        
        return selected
    
    def _calculate_vector_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if not vec1 or not vec2:
            return 0.0
        
        if HAS_NUMPY:
            # Use numpy for efficiency
            v1 = np.array(vec1)
            v2 = np.array(vec2)
            
            # Cosine similarity
            dot_product = np.dot(v1, v2)
            norm_product = np.linalg.norm(v1) * np.linalg.norm(v2)
            
            if norm_product == 0:
                return 0.0
            
            return float(dot_product / norm_product)
        else:
            # Pure Python implementation
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            norm1 = sum(a * a for a in vec1) ** 0.5
            norm2 = sum(b * b for b in vec2) ** 0.5
            
            if norm1 * norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
    
    def _score_temporal_relevance(self, temporal_type: str, session_context: Dict) -> float:
        """Score based on temporal relevance"""
        scores = {
            'persistent': 0.8,      # Always relevant
            'session': 0.6,         # Session-specific
            'temporary': 0.3,       # Short-term
            'archived': 0.1         # Historical
        }
        return scores.get(temporal_type, 0.5)
    
    def _score_context_alignment(self, message: str, context_type: str) -> float:
        """Score based on context type alignment with message"""
        message_lower = message.lower()
        
        # Keywords that suggest different contexts
        context_indicators = {
            'technical_state': ['bug', 'error', 'fix', 'implement', 'code', 'function'],
            'breakthrough': ['idea', 'realized', 'discovered', 'insight', 'solution'],
            'project_context': ['project', 'building', 'architecture', 'system'],
            'personal': ['dear friend', 'thank', 'appreciate', 'feel'],
            'unresolved': ['todo', 'need to', 'should', 'must', 'problem'],
            'decision': ['decided', 'chose', 'will use', 'approach', 'strategy']
        }
        
        # Check if message aligns with the memory's context type
        indicators = context_indicators.get(context_type, [])
        matches = sum(1 for word in indicators if word in message_lower)
        
        if matches > 0:
            return min(0.3 + (matches * 0.2), 1.0)
        return 0.1
    
    def _score_semantic_tags(self, message: str, tags: str) -> float:
        """Score based on semantic tag matching"""
        if not tags:
            return 0.0
        
        message_lower = message.lower()
        tag_list = tags.split(',') if isinstance(tags, str) else []
        
        matches = sum(1 for tag in tag_list if tag.strip().lower() in message_lower)
        
        if matches > 0:
            return min(0.3 + (matches * 0.3), 1.0)
        return 0.0
    
    def _score_trigger_phrases(self, message: str, trigger_phrases: str) -> float:
        """Score based on trigger phrase matching - highest priority"""
        if not trigger_phrases:
            return 0.0
        
        message_lower = message.lower()
        phrases = trigger_phrases.split(',') if isinstance(trigger_phrases, str) else []
        
        for phrase in phrases:
            if phrase.strip().lower() in message_lower:
                return 1.0  # Perfect match on trigger phrase
        
        return 0.0
    
    def _score_question_types(self, message: str, question_types: str) -> float:
        """Score based on question type matching"""
        if not question_types:
            return 0.0
        
        message_lower = message.lower()
        types = question_types.split(',') if isinstance(question_types, str) else []
        
        # Check if message matches any question pattern
        for qtype in types:
            qtype_lower = qtype.strip().lower()
            if qtype_lower in message_lower:
                return 0.8
            # Partial matching for question words
            if any(qword in message_lower for qword in ['how', 'why', 'what', 'when', 'where']):
                if any(qword in qtype_lower for qword in ['how', 'why', 'what', 'when', 'where']):
                    return 0.5
        
        return 0.0
    
    def _score_emotional_context(self, message: str, emotion: str) -> float:
        """Score based on emotional resonance"""
        if not emotion:
            return 0.0
        
        message_lower = message.lower()
        
        # Emotion indicators
        emotion_patterns = {
            'joy': ['happy', 'excited', 'love', 'wonderful', 'great', 'awesome'],
            'frustration': ['stuck', 'confused', 'help', 'issue', 'problem', 'why'],
            'discovery': ['realized', 'found', 'discovered', 'aha', 'insight'],
            'gratitude': ['thank', 'appreciate', 'grateful', 'dear friend']
        }
        
        patterns = emotion_patterns.get(emotion.lower(), [])
        if any(pattern in message_lower for pattern in patterns):
            return 0.7
        
        return 0.0
    
    def _score_problem_solution(self, message: str, is_problem_solution: bool) -> float:
        """Score based on problem-solution patterns"""
        if not is_problem_solution:
            return 0.0
        
        message_lower = message.lower()
        
        # Problem indicators
        problem_words = ['error', 'issue', 'problem', 'stuck', 'help', 'fix', 'solve', 'debug']
        if any(word in message_lower for word in problem_words):
            return 0.8
        
        return 0.0
    
    def _generate_selection_reasoning(self, vector: float, importance: float,
                                    temporal: float, context: float, 
                                    tags: float, action: float,
                                    trigger: float, question: float,
                                    emotion: float, problem: float) -> str:
        """Generate human-readable reasoning for why this memory was selected"""
        
        reasons = []
        
        # Find the strongest reason
        scores = {
            'trigger phrase match': trigger,
            'semantic similarity': vector,
            'high importance': importance,
            'question type match': question,
            'context alignment': context,
            'temporal relevance': temporal,
            'tag match': tags,
            'emotional resonance': emotion,
            'problem-solution': problem,
            'action required': action
        }
        
        # Sort by score
        sorted_reasons = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Build reasoning
        primary = sorted_reasons[0]
        if primary[1] > 0.5:
            reasons.append(f"Strong {primary[0]} ({primary[1]:.2f})")
        elif primary[1] > 0.3:
            reasons.append(f"{primary[0]} ({primary[1]:.2f})")
        
        # Add secondary reasons
        for reason, score in sorted_reasons[1:3]:
            if score > 0.3:
                reasons.append(f"{reason} ({score:.2f})")
        
        return "Selected due to: " + ", ".join(reasons) if reasons else "Selected based on combined factors"


class HybridRetrieval(RetrievalStrategy):
    """
    Hybrid approach: Use smart vector retrieval first, then optionally
    use Claude for complex queries or when confidence is low.
    """
    
    def __init__(self, vector_retrieval: SmartVectorRetrieval, claude_curator=None):
        self.vector_retrieval = vector_retrieval
        self.claude_curator = claude_curator
        
    async def retrieve_relevant_memories(self,
                                       all_memories: List[Dict[str, Any]],
                                       current_message: str,
                                       query_embedding: List[float],
                                       session_context: Dict[str, Any],
                                       max_memories: int = 5) -> List[Dict[str, Any]]:
        """
        Start with smart vector retrieval, escalate to Claude if needed.
        
        Escalation triggers:
        - Question marks in message (complex query)
        - Low confidence scores from vector retrieval
        - Explicit complexity indicators
        """
        
        # First try smart vector retrieval
        vector_results = await self.vector_retrieval.retrieve_relevant_memories(
            all_memories, current_message, query_embedding, 
            session_context, max_memories * 2  # Get more candidates
        )
        
        # Check if we should escalate to Claude
        should_escalate = self._should_escalate_to_claude(
            current_message, vector_results
        )
        
        if should_escalate and self.claude_curator:
            logger.info("🧠 Escalating to Claude for complex memory selection")
            # Use Claude for final selection from vector candidates
            return await self.claude_curator.curate_for_injection(
                vector_results[:max_memories * 2],  # Give Claude the top candidates
                current_message,
                max_memories
            )
        
        # Use vector results
        return vector_results[:max_memories]
    
    def _should_escalate_to_claude(self, message: str, vector_results: List[Dict]) -> bool:
        """Determine if we need Claude's help"""
        
        # Complex query indicators
        if any(indicator in message.lower() for indicator in [
            'how', 'why', 'explain', 'relationship', 'connected', 'related'
        ]):
            return True
        
        # Multiple question marks suggest complexity
        if message.count('?') > 1:
            return True
        
        # Low confidence in vector results
        # (Would need to track scores in vector_results)
        
        return False