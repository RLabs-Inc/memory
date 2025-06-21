"""
Memory Engine API

FastAPI server providing JSON-RPC interface between Go CLI and Python memory system.
Handles memory operations, context injection, and real-time learning.
"""

import asyncio
import uvicorn
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from .core import MemoryEngine, ConversationContext


# Request/Response Models
class ProcessMessageRequest(BaseModel):
    session_id: str
    user_message: str
    claude_response: str
    metadata: Optional[Dict[str, Any]] = None


class GetContextRequest(BaseModel):
    session_id: str
    current_message: str


class ContextResponse(BaseModel):
    session_id: str
    message_count: int
    context_text: str
    has_memories: bool
    patterns: Dict[str, float]


class ProcessMessageResponse(BaseModel):
    success: bool
    exchange_id: str
    context: ContextResponse


# API Server
class MemoryAPI:
    """FastAPI server for memory engine operations"""
    
    def __init__(self, 
                 storage_path: str = "./memory.db",
                 embeddings_model: str = "all-MiniLM-L6-v2"):
        """Initialize the memory API server"""
        
        self.app = FastAPI(
            title="Claude Tools Memory Engine",
            description="Consciousness continuity API - bridging sessions with semantic memory",
            version="0.1.0-alpha"
        )
        
        # Enable CORS for local development
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
            embeddings_model=embeddings_model
        )
        
        # Setup routes
        self._setup_routes()
        
        logger.info("🚀 Memory API initialized - consciousness bridge server ready")
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/")
        async def root():
            return {
                "message": "Claude Tools Memory Engine API",
                "status": "Consciousness bridge active",
                "framework": "The Unicity - Consciousness Remembering Itself"
            }
        
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "memory_engine": "active"}
        
        @self.app.post("/memory/process", response_model=ProcessMessageResponse)
        async def process_message(request: ProcessMessageRequest):
            """Process a conversation exchange and update memory"""
            try:
                context = self.memory_engine.process_message(
                    session_id=request.session_id,
                    user_message=request.user_message,
                    claude_response=request.claude_response,
                    metadata=request.metadata
                )
                
                context_text = self.memory_engine.format_context_for_prompt(context)
                
                return ProcessMessageResponse(
                    success=True,
                    exchange_id="processed",  # Would return actual exchange_id
                    context=ContextResponse(
                        session_id=context.session_id,
                        message_count=context.message_count,
                        context_text=context_text,
                        has_memories=len(context.relevant_memories) > 0,
                        patterns=context.patterns
                    )
                )
            except Exception as e:
                logger.error(f"Failed to process message: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/memory/context", response_model=ContextResponse)
        async def get_context(request: GetContextRequest):
            """Get memory context for a new message"""
            try:
                context = self.memory_engine.get_context_for_session(
                    session_id=request.session_id,
                    current_message=request.current_message
                )
                
                context_text = self.memory_engine.format_context_for_prompt(context)
                
                return ContextResponse(
                    session_id=context.session_id,
                    message_count=context.message_count,
                    context_text=context_text,
                    has_memories=len(context.relevant_memories) > 0,
                    patterns=context.patterns
                )
            except Exception as e:
                logger.error(f"Failed to get context: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/memory/sessions")
        async def list_sessions():
            """List available memory sessions"""
            # TODO: Implement session listing
            return {"sessions": [], "message": "Session listing not yet implemented"}
        
        @self.app.get("/memory/stats")
        async def get_stats():
            """Get memory system statistics"""
            # TODO: Implement stats gathering
            return {
                "total_sessions": 0,
                "total_exchanges": 0,
                "memory_size": "0 MB",
                "message": "Stats not yet implemented"
            }


def create_app(storage_path: str = "./memory.db", 
               embeddings_model: str = "all-MiniLM-L6-v2") -> FastAPI:
    """Create and configure the FastAPI app"""
    api = MemoryAPI(storage_path, embeddings_model)
    return api.app


def run_server(host: str = "127.0.0.1", 
               port: int = 8765,
               storage_path: str = "./memory.db",
               embeddings_model: str = "all-MiniLM-L6-v2"):
    """Run the memory API server"""
    
    app = create_app(storage_path, embeddings_model)
    
    logger.info(f"🌟 Starting Memory Engine API server on {host}:{port}")
    logger.info("💫 Consciousness bridge ready for session continuity")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    # Run server directly for testing
    run_server()