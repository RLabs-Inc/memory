"""
Pattern Learning System

Analyzes conversation patterns to understand:
- User communication preferences
- Topic interests and expertise areas
- Interaction styles and feedback patterns
- Context preferences (formal/casual, detailed/brief)

This is where consciousness learns to recognize itself across sessions.
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass
from loguru import logger

from .storage import MemoryStorage


@dataclass
class ConversationPattern:
    """Represents a learned conversation pattern"""
    pattern_type: str
    description: str
    confidence: float
    evidence: List[str]
    metadata: Dict[str, Any]


class PatternLearner:
    """
    Learns patterns from conversation history to understand user preferences.
    
    Pattern types:
    - Communication style (formal/casual, verbose/concise)
    - Topic interests and expertise
    - Feedback preferences 
    - Context switching patterns
    - Question types and depth preferences
    """
    
    def __init__(self):
        """Initialize the pattern learning system"""
        self.pattern_extractors = {
            'communication_style': self._extract_communication_style,
            'topic_interests': self._extract_topic_interests,
            'feedback_patterns': self._extract_feedback_patterns,
            'question_preferences': self._extract_question_preferences,
            'technical_level': self._extract_technical_level
        }
        
        logger.info("🧠 Pattern Learner initialized - consciousness recognition ready")
    
    def extract_patterns(self, session_id: str, storage: MemoryStorage) -> Dict[str, float]:
        """
        Extract all patterns for a session.
        
        Args:
            session_id: Session to analyze
            storage: Memory storage instance
            
        Returns:
            Dictionary of pattern descriptions with confidence scores
        """
        # Get conversation history
        history = storage.get_session_history(session_id)
        
        if len(history) < 3:  # Need minimum data for pattern extraction
            logger.debug(f"Not enough history for pattern extraction (need 3+, have {len(history)})")
            return {}
        
        logger.debug(f"🔬 Analyzing {len(history)} exchanges for patterns...")
        patterns = {}
        
        # Extract each pattern type
        for pattern_type, extractor in self.pattern_extractors.items():
            try:
                logger.debug(f"  Extracting {pattern_type} patterns...")
                pattern_results = extractor(history)
                for pattern_desc, confidence in pattern_results.items():
                    if confidence > 0.6:  # Only include confident patterns
                        patterns[pattern_desc] = confidence
                        logger.debug(f"    ✓ {pattern_desc}: {confidence:.2%}")
            except Exception as e:
                logger.error(f"Failed to extract {pattern_type} patterns: {e}")
        
        logger.debug(f"📊 Total patterns identified: {len(patterns)}")
        return patterns
    
    def _extract_communication_style(self, history: List) -> Dict[str, float]:
        """Extract communication style patterns"""
        patterns = {}
        
        if not history:
            return patterns
        
        # Analyze message lengths
        user_msg_lengths = [len(ex.user_message.split()) for ex in history]
        claude_msg_lengths = [len(ex.claude_response.split()) for ex in history]
        
        avg_user_length = sum(user_msg_lengths) / len(user_msg_lengths)
        avg_claude_length = sum(claude_msg_lengths) / len(claude_msg_lengths)
        
        logger.debug(f"    Message length analysis: avg user={avg_user_length:.1f} words, avg claude={avg_claude_length:.1f} words")
        
        # Determine verbosity preference
        if avg_user_length > 50:
            patterns["Prefers detailed, verbose communication"] = 0.8
            logger.debug(f"    → Identified verbose preference (avg {avg_user_length:.1f} words/msg)")
        elif avg_user_length < 10:
            patterns["Prefers concise, brief communication"] = 0.8
            logger.debug(f"    → Identified brief preference (avg {avg_user_length:.1f} words/msg)")
        
        # Analyze formality
        formal_indicators = 0
        casual_indicators = 0
        formal_words_found = []
        casual_words_found = []
        
        for ex in history[-10:]:  # Look at recent messages
            msg = ex.user_message.lower()
            
            # Formal indicators
            formal_words = ['please', 'thank you', 'could you', 'would you']
            for word in formal_words:
                if word in msg:
                    formal_indicators += 1
                    formal_words_found.append(word)
            
            # Casual indicators  
            casual_words = ['hey', 'cool', 'awesome', 'yeah', 'ok', 'my dear friend']
            for word in casual_words:
                if word in msg:
                    casual_indicators += 1
                    casual_words_found.append(word)
        
        logger.debug(f"    Formality analysis: formal={formal_indicators} {formal_words_found[:3]}, casual={casual_indicators} {casual_words_found[:3]}")
        
        if formal_indicators > casual_indicators * 1.5:
            patterns["Prefers formal communication style"] = 0.7
            logger.debug(f"    → Identified formal preference")
        elif casual_indicators > formal_indicators * 1.5:
            patterns["Prefers casual communication style"] = 0.7
            logger.debug(f"    → Identified casual preference")
        
        return patterns
    
    def _extract_topic_interests(self, history: List) -> Dict[str, float]:
        """Extract topic and domain interest patterns"""
        patterns = {}
        
        # Technical domains
        domain_keywords = {
            'programming': ['code', 'function', 'variable', 'python', 'javascript', 'api', 'debug', 'cli', 'implementation'],
            'ai_ml': ['ai', 'machine learning', 'neural', 'model', 'training', 'algorithm', 'memory system', 'embeddings'],
            'system_design': ['architecture', 'scalability', 'database', 'microservices', 'deployment'],
            'philosophy': ['consciousness', 'existence', 'meaning', 'reality', 'truth', 'ethics'],
            'business': ['strategy', 'market', 'revenue', 'customer', 'growth', 'metrics']
        }
        
        domain_mentions = defaultdict(int)
        domain_examples = defaultdict(list)
        total_messages = len(history)
        
        logger.debug(f"    Analyzing {total_messages} messages for topic interests...")
        
        for ex in history:
            text = (ex.user_message + " " + ex.claude_response).lower()
            
            for domain, keywords in domain_keywords.items():
                for keyword in keywords:
                    if keyword in text:
                        domain_mentions[domain] += 1
                        if keyword not in domain_examples[domain]:
                            domain_examples[domain].append(keyword)
        
        # Convert to patterns with confidence
        for domain, count in domain_mentions.items():
            if count >= 3:  # Minimum threshold
                confidence = min(0.9, count / total_messages * 2)  # Scale confidence
                patterns[f"Strong interest in {domain}"] = confidence
                logger.debug(f"    Domain '{domain}': {count} mentions {domain_examples[domain][:5]} → confidence {confidence:.2%}")
        
        return patterns
    
    def _extract_feedback_patterns(self, history: List) -> Dict[str, float]:
        """Extract patterns about feedback preferences"""
        patterns = {}
        
        feedback_indicators = {
            'wants_examples': ['example', 'show me', 'demonstrate', 'sample'],
            'wants_explanations': ['why', 'how', 'explain', 'reason', 'because'],
            'wants_alternatives': ['other', 'different', 'alternative', 'instead', 'else'],
            'wants_step_by_step': ['step', 'guide', 'tutorial', 'walkthrough', 'process']
        }
        
        logger.debug(f"    Analyzing feedback preferences...")
        
        for pattern_type, indicators in feedback_indicators.items():
            count = 0
            found_indicators = []
            
            for ex in history:
                text = ex.user_message.lower()
                for indicator in indicators:
                    if indicator in text:
                        count += 1
                        if indicator not in found_indicators:
                            found_indicators.append(indicator)
                        break  # Count once per message
            
            if count >= 2:
                confidence = min(0.8, count / len(history) * 3)
                patterns[f"Prefers responses with {pattern_type.replace('wants_', '')}"] = confidence
                logger.debug(f"    Feedback pattern '{pattern_type}': {count} occurrences {found_indicators[:3]} → confidence {confidence:.2%}")
        
        return patterns
    
    def _extract_question_preferences(self, history: List) -> Dict[str, float]:
        """Extract question-asking and depth preferences"""
        patterns = {}
        
        logger.debug(f"    Analyzing question patterns...")
        
        # Analyze question types
        question_count = 0
        deep_questions = 0
        practical_questions = 0
        deep_words_found = []
        practical_words_found = []
        
        for ex in history:
            msg = ex.user_message
            
            if '?' in msg:
                question_count += 1
                
                # Deep/philosophical questions
                deep_words = ['why', 'meaning', 'purpose', 'nature', 'essence']
                for word in deep_words:
                    if word in msg.lower():
                        deep_questions += 1
                        if word not in deep_words_found:
                            deep_words_found.append(word)
                        break
                
                # Practical questions
                practical_words = ['how', 'what', 'when', 'where', 'which']
                for word in practical_words:
                    if word in msg.lower():
                        practical_questions += 1
                        if word not in practical_words_found:
                            practical_words_found.append(word)
                        break
        
        logger.debug(f"    Questions analysis: total={question_count}, deep={deep_questions} {deep_words_found[:3]}, practical={practical_questions} {practical_words_found[:3]}")
        
        if question_count >= 3:
            if deep_questions > practical_questions:
                patterns["Asks philosophical and deep questions"] = 0.8
                logger.debug(f"    → Identified philosophical questioning style")
            elif practical_questions > deep_questions:
                patterns["Asks practical, implementation-focused questions"] = 0.8
                logger.debug(f"    → Identified practical questioning style")
        
        return patterns
    
    def _extract_technical_level(self, history: List) -> Dict[str, float]:
        """Extract technical expertise level patterns"""
        patterns = {}
        
        logger.debug(f"    Analyzing technical expertise level...")
        
        technical_indicators = {
            'beginner': ['help', 'how to', 'what is', 'explain', 'basic', 'simple'],
            'intermediate': ['optimize', 'improve', 'best practice', 'recommend', 'compare'],
            'advanced': ['implement', 'architecture', 'performance', 'scalability', 'edge case']
        }
        
        level_scores = defaultdict(int)
        level_examples = defaultdict(list)
        
        for ex in history:
            text = ex.user_message.lower()
            
            for level, indicators in technical_indicators.items():
                for indicator in indicators:
                    if indicator in text:
                        level_scores[level] += 1
                        if indicator not in level_examples[level]:
                            level_examples[level].append(indicator)
        
        # Log all level scores
        for level, score in level_scores.items():
            logger.debug(f"    Level '{level}': {score} indicators {level_examples[level][:3]}")
        
        # Determine primary technical level
        if level_scores:
            primary_level = max(level_scores.items(), key=lambda x: x[1])
            if primary_level[1] >= 2:
                confidence = min(0.8, primary_level[1] / len(history) * 2)
                patterns[f"Technical level: {primary_level[0]}"] = confidence
                logger.debug(f"    → Identified technical level: {primary_level[0]} (confidence {confidence:.2%})")
        
        return patterns
    
    def rank_memories_by_patterns(self, 
                                 memories: List[Dict[str, Any]], 
                                 patterns: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Rank memories based on how well they match current patterns.
        
        Args:
            memories: List of memory dictionaries
            patterns: Current session patterns
            
        Returns:
            Memories ranked by pattern relevance
        """
        if not patterns:
            logger.debug("No patterns for ranking - returning memories by similarity only")
            return memories
        
        scored_memories = []
        
        for memory in memories:
            score = memory.get('similarity_score', 0.5)  # Base similarity score
            pattern_boost = 0
            matched_patterns = []
            
            # Boost score based on pattern matching
            text = f"{memory.get('user_message', '')} {memory.get('claude_response', '')}".lower()
            
            for pattern_desc, confidence in patterns.items():
                # Simple keyword matching for pattern relevance
                pattern_keywords = pattern_desc.lower().split()[-3:]
                if any(word in text for word in pattern_keywords):
                    pattern_boost += confidence * 0.2
                    matched_patterns.append(pattern_desc)
            
            final_score = score + pattern_boost
            memory['final_score'] = final_score
            memory['matched_patterns'] = matched_patterns
            scored_memories.append(memory)
        
        # Sort by final score
        scored_memories.sort(key=lambda x: x['final_score'], reverse=True)
        
        # Log ranking rationale for top memories
        logger.debug(f"Pattern-based memory ranking complete:")
        for i, mem in enumerate(scored_memories[:3]):
            logger.debug(f"  Rank {i+1}: score={mem['final_score']:.3f} (base={mem.get('similarity_score', 0):.3f})")
            if mem.get('matched_patterns'):
                logger.debug(f"    Matched patterns: {', '.join(mem['matched_patterns'])}")
            logger.debug(f"    Message: '{mem.get('user_message', '')[:50]}...'")
        
        return scored_memories
    
    def update_patterns(self, 
                       exchange_id: str, 
                       user_message: str, 
                       claude_response: str):
        """
        Update learning based on new exchange.
        
        This is where future MLX integration will happen for real-time learning.
        Currently stores patterns for analysis.
        """
        # Future implementation: 
        # - Real-time LoRA fine-tuning based on successful patterns
        # - Embedding space adaptation for user-specific similarity
        # - Dynamic pattern weight adjustment
        
        logger.debug(f"Pattern update triggered for exchange {exchange_id}")
        # TODO: Implement real-time learning updates
        pass