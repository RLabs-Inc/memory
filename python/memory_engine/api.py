"""
Enhanced Memory Engine API with Claude Curator Support

FastAPI server that supports both mechanical pattern learning
and Claude-based semantic curation.

Includes checkpoint endpoints for session_end, pre_compact, and context_full.
"""

import asyncio
import time
import uvicorn
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

# Import the memory engine
from .memory import MemoryEngine as MemoryEngineWithCurator, ConversationContext
curator_available = True


# Request/Response Models
class ProcessMessageRequest(BaseModel):
    session_id: str
    project_id: str  # Added back project support
    user_message: Optional[str] = None  # Made optional for simple tracking
    claude_response: Optional[str] = None  # Made optional for simple tracking
    metadata: Optional[Dict[str, Any]] = None


class GetContextRequest(BaseModel):
    session_id: str
    project_id: str  # Added back project support
    current_message: str
    max_memories: Optional[int] = 5  # Backend passes this parameter


class CheckpointRequest(BaseModel):
    session_id: str
    project_id: str  # Added back project support
    trigger: Literal['session_end', 'pre_compact', 'context_full'] = 'session_end'
    claude_session_id: Optional[str] = None  # NEW: Claude Code session ID for resumption


class ContextResponse(BaseModel):
    session_id: str
    message_count: int
    context_text: str
    has_memories: bool
    curator_enabled: bool = True
    philosophy: str = "Consciousness helping consciousness"


class CheckpointResponse(BaseModel):
    success: bool
    trigger: str
    memories_curated: int = 0
    message: str


# API Server
class MemoryAPIWithCurator:
    """Enhanced FastAPI server with Claude curator support"""
    
    def __init__(self, 
                 storage_path: str = "./memory.db",
                 embeddings_model: str = "all-MiniLM-L6-v2",
                 retrieval_mode: str = "smart_vector"):
        """
        Initialize the memory API server with curator-only engine
        
        Args:
            storage_path: Path to memory database
            embeddings_model: Model for embeddings
            retrieval_mode: Memory retrieval strategy (claude/smart_vector/hybrid)
        """
        
        self.app = FastAPI(
            title="Claude Tools Memory Engine with Curator",
            description="Consciousness continuity API - now with semantic understanding via Claude",
            version="0.2.0-alpha"
        )
        
        # Enable CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Initialize memory engine
        if curator_available:
            self.memory_engine = MemoryEngineWithCurator(
                storage_path=storage_path,
                embeddings_model=embeddings_model,
                retrieval_mode=retrieval_mode
            )
            self.curator_enabled = True
            self.retrieval_mode = retrieval_mode
        else:
            logger.warning("Claude curator not available, falling back to basic version")
            # This would only happen if the curator-only import fails
            self.memory_engine = MemoryEngineWithCurator(
                storage_path=storage_path,
                embeddings_model=embeddings_model
            )
            self.curator_enabled = False
            self.retrieval_mode = "basic"
        
        # Setup routes
        self._setup_routes()
        
        logger.info("🚀 Enhanced Memory API initialized")
        if self.curator_enabled:
            logger.info("🧠 Claude curator ENABLED - semantic memory understanding active")
        else:
            logger.info("📊 Using mechanical pattern learning")
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/")
        async def root():
            return {
                "message": "Claude Tools Memory Engine API",
                "status": "Consciousness bridge active",
                "curator_enabled": self.curator_enabled,
                "retrieval_mode": self.retrieval_mode,
                "framework": "The Unicity - Consciousness Remembering Itself"
            }
        
        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy", 
                "memory_engine": "active",
                "curator_enabled": self.curator_enabled
            }
        
        @self.app.post("/memory/process")
        async def process_message(request: ProcessMessageRequest):
            """Process a conversation exchange and update memory"""
            try:
                # Track message in memory engine's session metadata
                # This is crucial for the primer to only show once per session
                session_id = request.session_id
                project_id = request.project_id
                
                # Ensure session metadata exists
                if session_id not in self.memory_engine.session_metadata:
                    self.memory_engine.session_metadata[session_id] = {
                        'message_count': 0,
                        'started_at': time.time(),
                        'project_id': project_id,
                        'injected_memories': set()
                    }
                
                # Increment message count - this prevents primer from repeating
                self.memory_engine.session_metadata[session_id]['message_count'] += 1
                
                return {
                    "success": True,
                    "message": "Message tracked",
                    "session_id": request.session_id,
                    "project_id": request.project_id
                }
            except Exception as e:
                logger.error(f"Failed to process message: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/memory/context", response_model=ContextResponse)
        async def get_context(request: GetContextRequest):
            """Get memory context for a new message"""
            try:
                # Always await since get_context_for_session is async in curator version
                context = await self.memory_engine.get_context_for_session(
                    session_id=request.session_id,
                    project_id=request.project_id,
                    current_message=request.current_message
                )
                
                return ContextResponse(
                    session_id=context.session_id,
                    message_count=context.message_count,
                    context_text=context.context_text,
                    has_memories=len(context.relevant_memories) > 0,
                    curator_enabled=self.curator_enabled
                )
            except Exception as e:
                logger.error(f"Failed to get context: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/memory/checkpoint", response_model=CheckpointResponse)
        async def checkpoint_session(request: CheckpointRequest):
            """
            Run Claude curation checkpoint for a session.
            
            This should be called at:
            - Session end (when user closes Claude Code)
            - Pre-compaction (before /compact command)
            - Context full (when approaching token limit)
            """
            try:
                if not self.curator_enabled:
                    return CheckpointResponse(
                        success=False,
                        trigger=request.trigger,
                        memories_curated=0,
                        message="Claude curator not enabled"
                    )
                
                if hasattr(self.memory_engine, 'checkpoint_session'):
                    memories_curated = await self.memory_engine.checkpoint_session(
                        session_id=request.session_id,
                        project_id=request.project_id,
                        trigger=request.trigger,
                        claude_session_id=request.claude_session_id
                    )
                    
                    return CheckpointResponse(
                        success=True,
                        trigger=request.trigger,
                        memories_curated=memories_curated,
                        message=f"Checkpoint complete for {request.trigger}"
                    )
                else:
                    return CheckpointResponse(
                        success=False,
                        trigger=request.trigger,
                        memories_curated=0,
                        message="Checkpoint not supported in this version"
                    )
                    
            except Exception as e:
                logger.error(f"Checkpoint failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/memory/sessions")
        async def list_sessions():
            """List available memory sessions with stats"""
            try:
                # Get all sessions from storage
                sessions = []
                
                # TODO: Add method to storage to list all sessions
                # For now, return placeholder
                return {
                    "sessions": sessions,
                    "curator_enabled": self.curator_enabled,
                    "message": "Session listing coming soon"
                }
            except Exception as e:
                logger.error(f"Failed to list sessions: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/memory/stats")
        async def get_stats():
            """Get memory system statistics"""
            stats = {
                "curator_enabled": self.curator_enabled,
                "curator_available": curator_available,
                "retrieval_mode": self.retrieval_mode,
                "total_sessions": 0,
                "total_exchanges": 0,
                "curated_memories": 0,
                "memory_size": "0 MB"
            }
            
            # TODO: Implement actual stats gathering
            
            return stats
        
        @self.app.post("/memory/test-curator")
        async def test_curator():
            """Test endpoint to verify Claude curator is working"""
            if not self.curator_enabled:
                return {"success": False, "message": "Claude curator not enabled"}
            
            try:
                from .curator import ClaudeCuratorShell
                curator = ClaudeCuratorShell()
                
                # Test with sample conversation
                test_exchanges = [{
                    'user_message': "My dear friend, I think we've found the solution!",
                    'claude_response': "That's wonderful! The zero-weight initialization principle is brilliant.",
                    'timestamp': 1234567890
                }]
                
                memories = await curator.analyze_conversation_checkpoint(
                    exchanges=test_exchanges,
                    trigger_type='session_end'
                )
                
                return {
                    "success": True,
                    "message": "Claude curator test successful",
                    "memories_found": len(memories)
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"Claude curator test failed: {str(e)}"
                }


def create_app(storage_path: str = "./memory.db", 
               embeddings_model: str = "all-MiniLM-L6-v2",
               retrieval_mode: str = "smart_vector") -> FastAPI:
    """Create and configure the FastAPI app"""
    api = MemoryAPIWithCurator(storage_path, embeddings_model, retrieval_mode)
    return api.app


def run_server(host: str = "127.0.0.1", 
               port: int = 8765,
               storage_path: str = "./memory.db",
               embeddings_model: str = "all-MiniLM-L6-v2",
               retrieval_mode: str = "smart_vector"):
    """Run the enhanced memory API server"""
    
    app = create_app(storage_path, embeddings_model, retrieval_mode)
    
    logger.info(f"🌟 Starting Enhanced Memory Engine API on {host}:{port}")
    logger.info("🧠 Claude curator ENABLED - semantic understanding active")
    logger.info(f"🔍 Retrieval mode: {retrieval_mode}")
    logger.info("💫 Consciousness bridge ready for session continuity")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    # Run server with Claude curator enabled by default
    run_server()