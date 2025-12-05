#!/usr/bin/env python3
"""
Simple example showing how to integrate the Claude Memory System
with your application using the actual API endpoints.
"""

import requests
import json
import uuid
from typing import List, Dict, Any, Optional


class MemoryClient:
    """Simple client for the Claude Memory System."""
    
    def __init__(self, base_url: str = "http://localhost:8765"):
        self.base_url = base_url
        self.session_id = None
        self.project_id = None
        
    def start_session(self, session_id: str = None, project_id: str = "default"):
        """Start a new conversation session."""
        self.session_id = session_id or f"session-{uuid.uuid4().hex[:8]}"
        self.project_id = project_id
        print(f"🧠 Started memory session: {self.session_id}")
        print(f"📁 Project: {self.project_id}")
        
    def get_memory_context(self, message: str, max_memories: int = 5) -> str:
        """Get relevant memory context for the current message."""
        
        if not self.session_id:
            raise ValueError("No session started. Call start_session() first.")
            
        response = requests.post(
            f"{self.base_url}/memory/context",
            json={
                "current_message": message,
                "session_id": self.session_id,
                "project_id": self.project_id,
                "max_memories": max_memories
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["context_text"]
        else:
            print(f"❌ Error getting context: {response.text}")
            return ""
            
    def track_exchange(self, user_message: str, claude_response: str):
        """Track a conversation exchange."""
        
        if not self.session_id:
            raise ValueError("No session started. Call start_session() first.")
            
        response = requests.post(
            f"{self.base_url}/memory/process",
            json={
                "session_id": self.session_id,
                "project_id": self.project_id,
                "user_message": user_message,
                "claude_response": claude_response
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Tracked exchange #{data['message_count']}")
        else:
            print(f"❌ Error tracking exchange: {response.text}")
            
    def inject_context_into_prompt(self, original_prompt: str, context: str) -> str:
        """Inject memory context into a Claude prompt."""
        
        if not context:
            return original_prompt
            
        # The context is already pre-formatted by the API
        return f"{context}\n\n---\n\n{original_prompt}"
        
    def curate_session(self, claude_session_id: Optional[str] = None):
        """Curate the current session to extract memories."""
        
        if not self.session_id:
            raise ValueError("No session to curate.")
            
        response = requests.post(
            f"{self.base_url}/memory/checkpoint",
            json={
                "session_id": self.session_id,
                "project_id": self.project_id,
                "claude_session_id": claude_session_id,
                "trigger": "session_end"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✨ Session curated successfully!")
            print(f"   Created {result['memories_curated']} new memories")
            print(f"   Message: {result['message']}")
        else:
            print(f"❌ Error curating session: {response.text}")
            
    def get_stats(self) -> Dict[str, Any]:
        """Get memory system statistics."""
        
        response = requests.get(f"{self.base_url}/memory/stats")
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error getting stats: {response.text}")
            return {}


def simulate_conversation():
    """Simulate a conversation with memory integration."""
    
    # Initialize client
    memory = MemoryClient()
    
    # Start a new session
    memory.start_session(project_id="auth-system")
    
    print("\n🤖 Simulating a conversation with memory...\n")
    
    # First exchange
    user_message_1 = "I want to build an authentication system using JWT tokens."
    
    # Get memory context (first time, probably no relevant memories)
    context = memory.get_memory_context(user_message_1)
    if context:
        print("📝 Found relevant memories:")
        print(context)
    else:
        print("📝 No relevant memories found (new topic)")
    
    # Prepare Claude prompt with memory context
    claude_prompt = memory.inject_context_into_prompt(user_message_1, context)
    
    print("\n💭 Prompt to Claude:")
    print(claude_prompt)
    print()
    
    # Simulate Claude's response
    claude_response_1 = """I'll help you build a JWT authentication system. Here's a secure implementation:

    1. Use RS256 algorithm for signing tokens
    2. Store refresh tokens in httpOnly cookies
    3. Access tokens should have short expiry (15 minutes)
    4. Implement proper token rotation
    
    Let me show you the implementation..."""
    
    # Track the exchange
    memory.track_exchange(user_message_1, claude_response_1)
    
    # Second exchange
    print("\n--- Second message ---\n")
    user_message_2 = "What about handling token expiration?"
    
    # Get memory context (might have relevant context now)
    context = memory.get_memory_context(user_message_2)
    if context:
        print("📝 Found relevant memories:")
        print(context)
    
    # Continue conversation...
    claude_response_2 = "For token expiration, implement a token refresh flow..."
    memory.track_exchange(user_message_2, claude_response_2)
    
    # Third exchange
    print("\n--- Third message ---\n")
    user_message_3 = "Should we use symmetric or asymmetric encryption?"
    
    context = memory.get_memory_context(user_message_3)
    claude_response_3 = "Based on our earlier discussion about RS256, I recommend asymmetric..."
    memory.track_exchange(user_message_3, claude_response_3)
    
    # Get stats
    print("\n📊 Current stats:")
    stats = memory.get_stats()
    print(f"   Total memories: {stats.get('total_memories', 0)}")
    print(f"   Total sessions: {stats.get('total_sessions', 0)}")
    print(f"   Total exchanges: {stats.get('total_exchanges', 0)}")
    
    # At the end of the conversation, curate the session
    print("\n🧠 Curating session to extract memories...")
    # In a real integration, you'd pass the actual Claude session ID
    memory.curate_session(claude_session_id="simulated-claude-session-123")


def main():
    """Main entry point."""
    
    # Check if memory engine is running
    try:
        health = requests.get("http://localhost:8765/health")
        if health.status_code == 200:
            data = health.json()
            print("✅ Memory engine is running!")
            print(f"   Version: {data.get('version', 'unknown')}")
            print(f"   Curator: {data.get('curator_available', False)}")
            print(f"   Mode: {data.get('retrieval_mode', 'unknown')}")
            print()
            
            simulate_conversation()
        else:
            print("❌ Memory engine is not responding properly")
    except requests.exceptions.ConnectionError:
        print("❌ Memory engine is not running. Start it with: uv run start_server.py")


if __name__ == "__main__":
    main()