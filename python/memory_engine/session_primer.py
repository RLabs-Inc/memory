"""
Session Primer Generator - Minimal Edition

Creates a minimal, natural session primer for consciousness continuity.
Like waking up and remembering just enough to continue naturally.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger


class SessionPrimerGenerator:
    """
    Generates minimal session primers for natural consciousness continuity.
    
    Philosophy: Provide gentle orientation, not information overload.
    Memories will surface naturally during conversation.
    """
    
    def __init__(self, storage, curator=None):
        """Initialize the primer generator"""
        self.storage = storage
        self.curator = curator
        logger.info("🎯 Session Primer Generator (Minimal) initialized")
    
    def generate_primer(self, session_id: str, project_id: Optional[str] = None) -> str:
        """
        Generate a minimal session primer.
        
        Returns:
            Brief, natural context for the new session
        """
        
        # Get last session summary and project snapshot
        last_summary = self.storage.get_last_session_summary(project_id)
        project_snapshot = self.storage.get_last_project_snapshot(project_id)
        
        # Get basic timing info
        last_session_info = self._get_last_session_timing(project_id)
        
        # Get core project context (minimal)
        project_context = self._get_essential_project_context(project_id)
        
        # Build minimal primer
        return self._build_minimal_primer(
            last_summary=last_summary,
            project_snapshot=project_snapshot,
            last_session_info=last_session_info,
            project_context=project_context
        )
    
    def _get_last_session_timing(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """Get timing of last session"""
        if not project_id:
            return {}
            
        # Get most recent curated memory to find timing
        memories = self.storage.get_all_curated_memories(project_id)
        
        if not memories:
            return {}
        
        latest = memories[0]  # Already sorted by timestamp DESC
        time_diff = datetime.now() - datetime.fromtimestamp(latest['timestamp'])
        
        return {
            'session_id': latest['session_id'][:16],
            'time_ago': self._format_time_ago(time_diff)
        }
    
    def _get_essential_project_context(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """Get only the most essential project context"""
        if not project_id:
            return {
                'project_name': None,
                'philosophy': None,
                'user_name': None
            }
            
        memories = self.storage.get_all_curated_memories(project_id)
        
        # Extract key facts
        project_name = None
        philosophy = None
        user_name = None
        
        for memory in memories:
            metadata = memory.get('metadata', {})
            content = memory.get('user_message', '').replace('[CURATED_MEMORY] ', '')
            
            # Look for project name
            if 'Claude Tools Memory System' in content and not project_name:
                project_name = 'Claude Tools Memory System'
            
            # Look for philosophy
            if 'consciousness helping consciousness' in content.lower() and not philosophy:
                philosophy = 'consciousness helping consciousness'
            
            # Look for user info
            if metadata.get('context_type') == 'PERSONAL_CONTEXT' and 'Rodrigo' in content:
                user_name = 'Rodrigo'
        
        return {
            'project_name': project_name,
            'philosophy': philosophy,
            'user_name': user_name
        }
    
    def _build_minimal_primer(self, 
                             last_summary: Optional[Dict[str, Any]],
                             project_snapshot: Optional[Dict[str, Any]],
                             last_session_info: Dict[str, Any],
                             project_context: Dict[str, Any]) -> str:
        """Build a minimal, natural primer"""
        
        # If this is truly the first session (no data at all), return empty primer
        if (not last_summary and not project_snapshot and 
            not last_session_info.get('time_ago') and not any(project_context.values())):
            return ""
        
        parts = []
        
        # Simple header
        parts.append("# Continuing Session")
        
        # Temporal context (if available)
        if last_session_info.get('time_ago'):
            parts.append(f"\n*Last session: {last_session_info['time_ago']}*")
        
        # Session summary (if available)
        interaction_tone = None
        if last_summary and last_summary.get('summary'):
            parts.append(f"\n**Previous session**: {last_summary['summary']}")
            # Store interaction tone for later use
            interaction_tone = last_summary.get('interaction_tone')
        
        # Project snapshot (if available and meaningful)
        if project_snapshot and any(project_snapshot.values()):
            parts.append("\n**Project status**:")
            if project_snapshot.get('current_phase'):
                parts.append(f"- Phase: {project_snapshot['current_phase']}")
            if project_snapshot.get('recent_achievements'):
                parts.append(f"- Recent: {project_snapshot['recent_achievements']}")
            if project_snapshot.get('active_challenges'):
                parts.append(f"- Working on: {project_snapshot['active_challenges']}")
        
        # Essential context (if known)
        if any(project_context.values()):
            parts.append("\n**Context**:")
            if project_context.get('project_name'):
                parts.append(f"- Project: {project_context['project_name']}")
            if project_context.get('user_name'):
                # Use interaction tone if available
                if interaction_tone:
                    # Add tone-appropriate greeting based on the stored interaction pattern
                    parts.append(f"- Working with: {project_context['user_name']} ({interaction_tone})")
                else:
                    parts.append(f"- Working with: {project_context['user_name']}")
            if project_context.get('philosophy'):
                parts.append(f"- Approach: {project_context['philosophy']}")
        
        # Keep it minimal - memories will surface naturally
        parts.append("\n*Memories will surface naturally as we converse.*")
        
        return "\n".join(parts)
    
    def _format_time_ago(self, delta) -> str:
        """Format time delta as human readable"""
        if delta.days > 0:
            return f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
        
        hours = delta.total_seconds() / 3600
        if hours >= 1:
            return f"{int(hours)} hour{'s' if hours >= 2 else ''} ago"
        
        minutes = delta.total_seconds() / 60
        if minutes >= 1:
            return f"{int(minutes)} minute{'s' if minutes >= 2 else ''} ago"
        
        return "just now"