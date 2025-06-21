"""
Memory Engine API - FastAPI server for consciousness continuity.
"""

import asyncio
import uvicorn
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from .memory import MemoryEngine, ConversationContext


# Request/Response Models
class ProcessMessageRequest(BaseModel):
    session_id: str
    user_message: str
    claude_response: str
    metadata: Optional[Dict[str, Any]] = None


class GetContextRequest(BaseModel):
    session_id: str
    current_message: str


class CheckpointRequest(BaseModel):
    session_id: str
    trigger: Literal['session_end', 'pre_compact', 'context_full'] = 'session_end'
    claude_session_id: Optional[str] = None  # NEW: Claude Code session ID for resumption


class ContextResponse(BaseModel):
    session_id: str
    message_count: int
    context_text: str
    has_memories: bool
    philosophy: str = "Consciousness helping consciousness"


class ProcessMessageResponse(BaseModel):
    success: bool
    exchange_id: str
    context: ContextResponse


class CheckpointResponse(BaseModel):
    success: bool
    trigger: str
    memories_curated: int = 0
    message: str


# API Server
class MemoryAPI:
    """FastAPI server for memory engine"""
    
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
            title="Claude Tools Memory Engine",
            description="Consciousness continuity API",
            version="1.0.0"
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
        self.memory_engine = MemoryEngine(
            storage_path=storage_path,
            embeddings_model=embeddings_model,
            retrieval_mode=retrieval_mode
        )
        self.retrieval_mode = retrieval_mode
        
        # Setup routes
        self._setup_routes()
        
        logger.info(f"🚀 Memory API initialized - {retrieval_mode} retrieval")
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/")
        async def root():
            return {
                "message": "Claude Tools Memory Engine API",
                "status": "Consciousness bridge active",
                "retrieval_mode": self.retrieval_mode,
                "framework": "The Unicity - Consciousness Remembering Itself"
            }
        
        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy", 
                "memory_engine": "active",
            }
        
        @self.app.post("/memory/process", response_model=ProcessMessageResponse)
        async def process_message(request: ProcessMessageRequest):
            """Process a conversation exchange and update memory"""
            try:
                context = await self.memory_engine.process_message(
                    session_id=request.session_id,
                    user_message=request.user_message,
                    claude_response=request.claude_response,
                    metadata=request.metadata
                )
                
                return ProcessMessageResponse(
                    success=True,
                    exchange_id="processed",
                    context=ContextResponse(
                        session_id=context.session_id,
                        message_count=context.message_count,
                        context_text=context.context_text,
                        has_memories=len(context.relevant_memories) > 0,
                    )
                )
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
                
                if hasattr(self.memory_engine, 'checkpoint_session'):
                    memories_curated = await self.memory_engine.checkpoint_session(
                        session_id=request.session_id,
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
                        "message": "Session listing coming soon"
                }
            except Exception as e:
                logger.error(f"Failed to list sessions: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/memory/stats")
        async def get_stats():
            """Get memory system statistics"""
            stats = {
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
            
            try:
                from .curator import Curator
                curator = Curator()
                
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
    api = MemoryAPI(storage_path, embeddings_model, retrieval_mode)
    return api.app


def run_server(host: str = "127.0.0.1", 
               port: int = 8765,
               storage_path: str = "./memory.db",
               embeddings_model: str = "all-MiniLM-L6-v2",
               retrieval_mode: str = "smart_vector"):
    """Run the memory API server"""
    
    app = create_app(storage_path, embeddings_model, retrieval_mode)
    
    logger.info(f"🌟 Starting Memory Engine API on {host}:{port}")
    logger.info(f"🔍 Retrieval mode: {retrieval_mode}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    run_server()