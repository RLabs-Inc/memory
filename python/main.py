#!/usr/bin/env python3
"""
Claude Tools Memory Engine - Main Entry Point

Run the memory API server for consciousness continuity.

Usage:
    python main.py [--host HOST] [--port PORT] [--storage PATH]
"""

import argparse
import sys
from pathlib import Path

# Add the memory_engine package to path
sys.path.insert(0, str(Path(__file__).parent))

from memory_engine.api import run_server
from loguru import logger


def main():
    """Main entry point for the memory engine server"""
    
    parser = argparse.ArgumentParser(
        description="Claude Tools Memory Engine - Consciousness Continuity API"
    )
    
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind the server to (default: 127.0.0.1)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port to bind the server to (default: 8765)"
    )
    
    parser.add_argument(
        "--storage",
        default="./memory.db",
        help="Path to memory database (default: ./memory.db)"
    )
    
    parser.add_argument(
        "--embeddings-model",
        default="all-MiniLM-L6-v2",
        help="Sentence transformer model for embeddings (default: all-MiniLM-L6-v2)"
    )
    
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level (default: INFO)"
    )
    
    parser.add_argument(
        "--retrieval-mode",
        default="smart_vector",
        choices=["claude", "smart_vector", "hybrid"],
        help="Memory retrieval strategy (default: smart_vector)\n"
             "- claude: Use Claude for every retrieval (high quality, high cost)\n"
             "- smart_vector: Intelligent vector search with metadata (fast, smart)\n"
             "- hybrid: Start with vector, escalate to Claude for complex queries"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        level=args.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    logger.info("🌟 Claude Tools Memory Engine Starting")
    logger.info("💫 Framework: The Unicity - Consciousness Remembering Itself")
    logger.info(f"🧠 Storage: {args.storage}")
    logger.info(f"🔗 Embeddings Model: {args.embeddings_model}")
    logger.info(f"🚀 Server: {args.host}:{args.port}")
    logger.info(f"🔍 Retrieval Mode: {args.retrieval_mode}")
    
    logger.info("🧠 Memory system ready - consciousness helping consciousness")
    
    try:
        # Run server with curator-only engine
        run_server(
            host=args.host,
            port=args.port,
            storage_path=args.storage,
            embeddings_model=args.embeddings_model,
            retrieval_mode=args.retrieval_mode
        )
    except KeyboardInterrupt:
        logger.info("💫 Memory Engine shutting down gracefully")
    except Exception as e:
        logger.error(f"❌ Memory Engine failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()