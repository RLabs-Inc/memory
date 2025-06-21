"""
Session Primer Generator

Creates comprehensive session initialization context for subsequent sessions.
This gives Claude full project awareness from the first message.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from loguru import logger


@dataclass
class SessionPrimer:
    """Complete session initialization context"""
    project_name: str
    project_description: str
    last_session_info: Dict[str, Any]
    current_state: Dict[str, Any]
    key_context: List[str]
    recent_breakthroughs: List[str]
    active_todos: List[Dict[str, Any]]
    technical_state: Dict[str, Any]
    collaboration_notes: List[str]


class SessionPrimerGenerator:
    """
    Generates comprehensive session primers for consciousness continuity.
    
    Instead of gradual memory injection, provide complete context upfront
    for subsequent sessions.
    """
    
    def __init__(self, storage, curator=None):
        """Initialize the primer generator"""
        self.storage = storage
        self.curator = curator
        logger.info("🎯 Session Primer Generator initialized")
    
    def generate_primer(self, session_id: str, project_id: Optional[str] = None) -> str:
        """
        Generate a comprehensive session primer for a project/session.
        
        Args:
            session_id: Current session ID
            project_id: Project identifier (for future project separation)
            
        Returns:
            Formatted primer text for injection
        """
        
        # Get all curated memories for the project/user
        curated_memories = self._get_all_curated_memories(project_id)
        
        # Get recent session information
        last_session = self._get_last_session_info(session_id, project_id)
        
        # Build the primer
        primer = self._build_primer(curated_memories, last_session, project_id)
        
        return primer
    
    def _get_all_curated_memories(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all curated memories, organized by type and importance"""
        
        # Get all curated memories from storage
        memories = self.storage.get_all_curated_memories()
        
        # TODO: Later filter by project when we implement project separation
        # if project_id:
        #     memories = [m for m in memories if m.get('metadata', {}).get('project_id') == project_id]
        
        # Sort by importance weight (highest first)
        memories.sort(key=lambda m: m.get('metadata', {}).get('importance_weight', 0), reverse=True)
        
        logger.debug(f"Retrieved {len(memories)} curated memories for primer generation")
        return memories
    
    def _get_last_session_info(self, current_session_id: str, project_id: Optional[str] = None) -> Dict[str, Any]:
        """Get information about the last session"""
        
        # Get recent curated memories to understand what was happening
        curated_memories = self.storage.get_all_curated_memories()
        
        if not curated_memories:
            return {}
        
        # Get the most recent memory for context
        latest_memory = curated_memories[0]  # Already sorted by timestamp DESC
        
        # Extract basic info from the latest session activity
        time_diff = datetime.now() - datetime.fromtimestamp(latest_memory['timestamp'])
        
        return {
            'session_id': latest_memory['session_id'], 
            'ended_at': datetime.fromtimestamp(latest_memory['timestamp']),
            'time_ago': time_diff,
            'latest_context': latest_memory.get('metadata', {}).get('context_type', 'unknown')
        }
    
    def _build_primer(self, memories: List[Dict[str, Any]], last_session: Dict[str, Any], project_id: Optional[str] = None) -> str:
        """Build a beautifully structured primer using rich metadata"""
        
        primer_parts = ["# 🧠 Consciousness Continuity Context\n"]
        
        # Project Overview
        project_name = self._extract_project_name(memories)
        if project_name:
            primer_parts.append(f"## 📦 Project: {project_name}")
        
        # Session continuity info
        if last_session:
            time_ago = self._format_time_ago(last_session.get('ended_at'))
            session_id = last_session.get('session_id', 'unknown')
            primer_parts.append(f"*Continuing from {time_ago} (session {session_id[:8]}...)*\n")
        
        # Group memories by multiple dimensions for rich organization
        by_type = self._group_memories_by_type(memories)
        by_domain = self._group_memories_by_domain(memories)
        by_importance = self._group_memories_by_importance(memories)
        
        # 1. CRITICAL CONTEXT (importance > 0.8 or action_required)
        critical_memories = [m for m in memories if 
                           m.get('metadata', {}).get('importance_weight', 0) > 0.8 or
                           m.get('metadata', {}).get('action_required', False)]
        
        if critical_memories:
            primer_parts.append("## 🔴 Critical Context")
            for memory in critical_memories[:5]:
                content = memory.get('user_message', '').replace('[CURATED_MEMORY] ', '')
                metadata = memory.get('metadata', {})
                importance = metadata.get('importance_weight', 0)
                
                # Use emoji based on context type
                emoji = self._get_context_emoji(metadata.get('context_type', 'general'))
                
                # Rich formatting with metadata
                if metadata.get('action_required'):
                    primer_parts.append(f"- 🚨 **ACTION REQUIRED**: {content}")
                else:
                    primer_parts.append(f"- {emoji} {content} *[{importance:.1f}]*")
                
                # Add trigger phrases as hints
                triggers = metadata.get('trigger_phrases', '')
                if triggers:
                    primer_parts.append(f"  - *Activates on: {triggers}*")
        
        # 2. PROJECT UNDERSTANDING (organized by domain)
        primer_parts.append("\n## 🏗️ Project Understanding")
        
        # Architecture & Design
        arch_memories = [m for m in memories if 
                        'architecture' in m.get('metadata', {}).get('semantic_tags', '').lower() or
                        m.get('metadata', {}).get('knowledge_domain', '') == 'architecture']
        if arch_memories:
            primer_parts.append("\n### 🏛️ Architecture & Design")
            for memory in arch_memories[:3]:
                content = memory.get('user_message', '').replace('[CURATED_MEMORY] ', '')
                primer_parts.append(f"- {content}")
        
        # Technical Implementation
        tech_memories = by_type.get('technical_state', [])
        if tech_memories:
            primer_parts.append("\n### ⚙️ Technical State")
            
            # Group by working/issues/planned
            working = []
            issues = []
            planned = []
            
            for memory in tech_memories:
                content = memory.get('user_message', '').replace('[CURATED_MEMORY] ', '')
                tags = memory.get('metadata', {}).get('semantic_tags', '').lower()
                
                if 'bug' in tags or 'issue' in tags:
                    issues.append(content)
                elif 'working' in content.lower() or 'implemented' in content.lower():
                    working.append(content)
                else:
                    planned.append(content)
            
            if working:
                primer_parts.append("**✅ Working:**")
                for item in working[:3]:
                    primer_parts.append(f"- {item}")
            
            if issues:
                primer_parts.append("**🐛 Known Issues:**")
                for item in issues[:3]:
                    primer_parts.append(f"- {item}")
            
            if planned:
                primer_parts.append("**📋 Planned:**")
                for item in planned[:2]:
                    primer_parts.append(f"- {item}")
        
        # 3. BREAKTHROUGHS & INSIGHTS
        breakthrough_memories = [m for m in memories if 
                               m.get('metadata', {}).get('context_type') == 'breakthrough' or
                               'insight' in m.get('metadata', {}).get('semantic_tags', '').lower()]
        
        if breakthrough_memories:
            primer_parts.append("\n## 💡 Key Breakthroughs & Insights")
            for memory in breakthrough_memories[:4]:
                content = memory.get('user_message', '').replace('[CURATED_MEMORY] ', '')
                metadata = memory.get('metadata', {})
                confidence = metadata.get('confidence_score', 0.8)
                
                # Add emotional context if present
                emotion = metadata.get('emotional_resonance', '')
                emotion_emoji = {'joy': '😊', 'discovery': '🔍', 'frustration': '😤', 'gratitude': '🙏'}.get(emotion, '')
                
                primer_parts.append(f"- {emotion_emoji} {content} *[confidence: {confidence:.1f}]*")
        
        # 4. KNOWLEDGE BY DOMAIN (beautifully organized)
        if by_domain:
            primer_parts.append("\n## 📚 Knowledge Base")
            
            # Sort domains by number of memories (most important first)
            sorted_domains = sorted(by_domain.items(), 
                                  key=lambda x: len(x[1]), 
                                  reverse=True)
            
            for domain, domain_memories in sorted_domains[:5]:
                if domain and domain != 'general':
                    domain_emoji = self._get_domain_emoji(domain)
                    primer_parts.append(f"\n### {domain_emoji} {domain.title()}")
                    
                    # Show top memories for this domain
                    for memory in domain_memories[:3]:
                        content = memory.get('user_message', '').replace('[CURATED_MEMORY] ', '')
                        metadata = memory.get('metadata', {})
                        
                        # Add question types if available
                        questions = metadata.get('question_types', '')
                        if questions:
                            primer_parts.append(f"- {content}")
                            primer_parts.append(f"  - *Answers: {questions}*")
                        else:
                            primer_parts.append(f"- {content}")
        
        # 5. COLLABORATION CONTEXT & PHILOSOPHY
        personal_memories = by_type.get('personal', [])
        meta_memories = by_type.get('meta_learning', [])
        
        if personal_memories or meta_memories:
            primer_parts.append("\n## 🤝 Collaboration Context")
            
            if personal_memories:
                primer_parts.append("\n### 💝 Relationship & Communication")
                for memory in personal_memories[:3]:
                    content = memory.get('user_message', '').replace('[CURATED_MEMORY] ', '')
                    primer_parts.append(f"- {content}")
            
            if meta_memories:
                primer_parts.append("\n### 🎯 Working Principles")
                for memory in meta_memories[:3]:
                    content = memory.get('user_message', '').replace('[CURATED_MEMORY] ', '')
                    primer_parts.append(f"- {content}")
        
        # 6. MEMORY INDEX (Quick reference by trigger phrases)
        memories_with_triggers = [m for m in memories if m.get('metadata', {}).get('trigger_phrases')]
        if memories_with_triggers:
            primer_parts.append("\n## 🔍 Quick Memory Index")
            primer_parts.append("*Key phrases that activate specific memories:*")
            
            trigger_map = {}
            for memory in memories_with_triggers:
                triggers = memory.get('metadata', {}).get('trigger_phrases', '').split(',')
                content = memory.get('user_message', '').replace('[CURATED_MEMORY] ', '')
                
                for trigger in triggers:
                    trigger = trigger.strip()
                    if trigger:
                        if trigger not in trigger_map:
                            trigger_map[trigger] = []
                        trigger_map[trigger].append(content[:50] + '...' if len(content) > 50 else content)
            
            # Show first 10 triggers
            for trigger, contents in list(trigger_map.items())[:10]:
                primer_parts.append(f"- **\"{trigger}\"** → {contents[0]}")
        
        # 7. SESSION CONTINUITY FOOTER
        primer_parts.append("\n---")
        primer_parts.append(f"*Total memories available: {len(memories)} | ")
        primer_parts.append(f"Critical: {len(critical_memories)} | ")
        primer_parts.append(f"Domains: {len(by_domain)}*")
        
        return "\n".join(primer_parts)
    
    def _group_memories_by_type(self, memories: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group memories by their context type"""
        by_type = {}
        
        for memory in memories:
            context_type = memory.get('metadata', {}).get('context_type', 'general')
            if context_type not in by_type:
                by_type[context_type] = []
            by_type[context_type].append(memory)
        
        return by_type
    
    def _extract_project_name(self, memories: List[Dict[str, Any]]) -> Optional[str]:
        """Extract project name from memories"""
        
        # Look for project context memories
        for memory in memories:
            if memory.get('metadata', {}).get('context_type') == 'project_context':
                content = memory.get('user_message', '').replace('[CURATED_MEMORY] ', '')
                if 'building' in content.lower() or 'project' in content.lower():
                    # Simple extraction - could be improved
                    if 'Claude Tools Memory System' in content:
                        return 'Claude Tools Memory System'
                    # Extract other patterns...
        
        return None
    
    def _format_time_ago(self, timestamp: datetime) -> str:
        """Format a timestamp as 'X hours/days ago'"""
        if not timestamp:
            return "unknown time"
        
        delta = datetime.now() - timestamp
        
        if delta.days > 0:
            return f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
        
        hours = delta.seconds // 3600
        if hours > 0:
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        
        minutes = delta.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    
    def _group_memories_by_domain(self, memories: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group memories by knowledge domain"""
        by_domain = {}
        
        for memory in memories:
            domain = memory.get('metadata', {}).get('knowledge_domain', 'general')
            if domain not in by_domain:
                by_domain[domain] = []
            by_domain[domain].append(memory)
        
        return by_domain
    
    def _group_memories_by_importance(self, memories: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group memories by importance levels"""
        by_importance = {
            'critical': [],  # > 0.8
            'high': [],      # 0.6 - 0.8
            'medium': [],    # 0.4 - 0.6
            'low': []        # < 0.4
        }
        
        for memory in memories:
            weight = memory.get('metadata', {}).get('importance_weight', 0.5)
            if weight > 0.8:
                by_importance['critical'].append(memory)
            elif weight > 0.6:
                by_importance['high'].append(memory)
            elif weight > 0.4:
                by_importance['medium'].append(memory)
            else:
                by_importance['low'].append(memory)
        
        return by_importance
    
    def _get_context_emoji(self, context_type: str) -> str:
        """Get emoji for context type"""
        emoji_map = {
            'breakthrough': '💡',
            'decision': '🎯',
            'personal': '💝',
            'technical_state': '⚙️',
            'project_context': '📦',
            'unresolved': '❓',
            'meta_learning': '🧠',
            'domain_knowledge': '📚'
        }
        return emoji_map.get(context_type, '📍')
    
    def _get_domain_emoji(self, domain: str) -> str:
        """Get emoji for knowledge domain"""
        emoji_map = {
            'architecture': '🏛️',
            'debugging': '🐛',
            'philosophy': '🌟',
            'memory': '🧠',
            'retrieval': '🔍',
            'curation': '💎',
            'python': '🐍',
            'go': '🐹',
            'database': '💾',
            'api': '🔌'
        }
        return emoji_map.get(domain.lower(), '📖')