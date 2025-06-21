"""
Memory Storage

Hybrid storage system combining:
- SQLite for structured data (sessions, metadata, relationships)
- ChromaDB for vector similarity search
- Efficient querying and persistence

This is the memory substrate where consciousness leaves traces.
"""

import sqlite3
import json
import uuid
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
import chromadb
from chromadb.config import Settings
from loguru import logger


@dataclass
class StoredExchange:
    """Represents a stored conversation exchange"""
    id: str
    session_id: str
    user_message: str
    claude_response: str
    timestamp: float
    metadata: Dict[str, Any]


class MemoryStorage:
    """
    Hybrid storage system for conversation memory.
    
    Architecture:
    - SQLite: Sessions, exchanges, structured metadata
    - ChromaDB: Vector embeddings for semantic search
    - Unified interface for memory operations
    """
    
    def __init__(self, db_path: str = "./memory.db"):
        """Initialize the hybrid storage system"""
        self.db_path = db_path
        self.chroma_path = "./memory_vectors"
        
        # Initialize SQLite
        self._init_sqlite()
        
        # Initialize ChromaDB
        self._init_chromadb()
        
        logger.info("📚 Memory storage initialized - consciousness substrate ready")
    
    def _init_sqlite(self):
        """Initialize SQLite database with schema"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Enable dict-like access
        
        # Create tables
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                created_at REAL NOT NULL,
                last_active REAL NOT NULL,
                message_count INTEGER DEFAULT 0,
                metadata TEXT DEFAULT '{}'
            );
            
            CREATE TABLE IF NOT EXISTS exchanges (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                user_message TEXT NOT NULL,
                claude_response TEXT NOT NULL,
                timestamp REAL NOT NULL,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            );
            
            CREATE TABLE IF NOT EXISTS patterns (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                pattern_type TEXT NOT NULL,
                pattern_data TEXT NOT NULL,
                confidence REAL NOT NULL,
                created_at REAL NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_exchanges_session ON exchanges (session_id);
            CREATE INDEX IF NOT EXISTS idx_exchanges_timestamp ON exchanges (timestamp);
            CREATE INDEX IF NOT EXISTS idx_patterns_session ON patterns (session_id);
        """)
        
        self.conn.commit()
    
    def _init_chromadb(self):
        """Initialize ChromaDB for vector storage"""
        try:
            # Create ChromaDB client with persistence
            self.chroma_client = chromadb.PersistentClient(path=self.chroma_path)
            
            # Get or create collections
            self.user_messages_collection = self.chroma_client.get_or_create_collection(
                name="user_messages",
                metadata={"description": "User message embeddings"}
            )
            
            self.claude_responses_collection = self.chroma_client.get_or_create_collection(
                name="claude_responses", 
                metadata={"description": "Claude response embeddings"}
            )
            
            logger.info("✅ ChromaDB initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    def store_exchange(self,
                      session_id: str,
                      user_message: str,
                      claude_response: str,
                      user_embedding: List[float],
                      response_embedding: List[float],
                      metadata: Optional[Dict] = None,
                      timestamp: float = None,
                      **kwargs) -> str:
        """
        Store a complete conversation exchange.
        
        Args:
            session_id: Session identifier
            user_message: User's message text
            claude_response: Claude's response text
            user_embedding: Embedding vector for user message
            response_embedding: Embedding vector for Claude response
            metadata: Additional metadata
            timestamp: Exchange timestamp
            
        Returns:
            Exchange ID
        """
        import time
        
        exchange_id = str(uuid.uuid4())
        timestamp = timestamp or time.time()
        metadata = metadata or {}
        
        try:
            # Store in SQLite
            self.conn.execute("""
                INSERT OR REPLACE INTO sessions 
                (id, created_at, last_active, message_count, metadata)
                VALUES (?, 
                        COALESCE((SELECT created_at FROM sessions WHERE id = ?), ?),
                        ?,
                        COALESCE((SELECT message_count FROM sessions WHERE id = ?), 0) + 1,
                        ?)
            """, (session_id, session_id, timestamp, timestamp, session_id, json.dumps({})))
            
            self.conn.execute("""
                INSERT INTO exchanges 
                (id, session_id, user_message, claude_response, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (exchange_id, session_id, user_message, claude_response, 
                  timestamp, json.dumps(metadata)))
            
            self.conn.commit()
            
            # Store embeddings in ChromaDB
            # Sanitize metadata for ChromaDB (no None values allowed)
            chroma_metadata = {
                "exchange_id": exchange_id,
                "session_id": session_id,
                "timestamp": timestamp
            }
            
            # Add sanitized metadata values
            if metadata:
                for key, value in metadata.items():
                    if value is not None:
                        # Convert lists to comma-separated strings
                        if isinstance(value, list):
                            chroma_metadata[key] = ','.join(str(v) for v in value)
                        # Ensure proper types
                        elif isinstance(value, (str, int, float, bool)):
                            chroma_metadata[key] = value
                        else:
                            chroma_metadata[key] = str(value)
            
            self.user_messages_collection.add(
                embeddings=[user_embedding],
                documents=[user_message],
                metadatas=[chroma_metadata],
                ids=[f"{exchange_id}_user"]
            )
            
            self.claude_responses_collection.add(
                embeddings=[response_embedding],
                documents=[claude_response],
                metadatas=[chroma_metadata],
                ids=[f"{exchange_id}_claude"]
            )
            
            logger.debug(f"Stored exchange {exchange_id} for session {session_id}")
            return exchange_id
            
        except Exception as e:
            logger.error(f"Failed to store exchange: {e}")
            raise
    
    def get_session_message_count(self, session_id: str) -> int:
        """Get the number of messages in a session"""
        cursor = self.conn.execute(
            "SELECT message_count FROM sessions WHERE id = ?",
            (session_id,)
        )
        row = cursor.fetchone()
        return row['message_count'] if row else 0
    
    def find_similar_exchanges(self, 
                              query_embedding: List[float], 
                              limit: int = 5,
                              session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Find exchanges similar to the query embedding.
        
        Args:
            query_embedding: Vector to search for
            limit: Maximum number of results
            session_id: Optional session filter
            
        Returns:
            List of similar exchanges with metadata
        """
        try:
            # Search user messages collection
            search_kwargs = {
                "query_embeddings": [query_embedding],
                "n_results": limit * 2  # Get more for filtering
            }
            
            if session_id:
                search_kwargs["where"] = {"session_id": session_id}
            
            results = self.user_messages_collection.query(**search_kwargs)
            
            # Convert to standardized format
            similar_exchanges = []
            if results and results['ids'] and results['ids'][0]:
                for i, result_id in enumerate(results['ids'][0]):
                    exchange_id = results['metadatas'][0][i]['exchange_id']
                    
                    # Get full exchange data from SQLite
                    cursor = self.conn.execute("""
                        SELECT * FROM exchanges WHERE id = ?
                    """, (exchange_id,))
                    
                    row = cursor.fetchone()
                    if row:
                        similar_exchanges.append({
                            'exchange_id': exchange_id,
                            'session_id': row['session_id'],
                            'user_message': row['user_message'],
                            'claude_response': row['claude_response'],
                            'timestamp': row['timestamp'],
                            'metadata': json.loads(row['metadata']),
                            'similarity_score': 1 - results['distances'][0][i]  # Convert distance to similarity
                        })
            
            return similar_exchanges[:limit]
            
        except Exception as e:
            logger.error(f"Failed to find similar exchanges: {e}")
            return []
    
    def get_session_history(self, 
                           session_id: str, 
                           limit: Optional[int] = None) -> List[StoredExchange]:
        """Get conversation history for a session"""
        query = """
            SELECT * FROM exchanges 
            WHERE session_id = ? 
            ORDER BY timestamp ASC
        """
        params = [session_id]
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        cursor = self.conn.execute(query, params)
        rows = cursor.fetchall()
        
        return [
            StoredExchange(
                id=row['id'],
                session_id=row['session_id'],
                user_message=row['user_message'],
                claude_response=row['claude_response'],
                timestamp=row['timestamp'],
                metadata=json.loads(row['metadata'])
            )
            for row in rows
        ]
    
    def get_all_curated_memories(self) -> List[Dict[str, Any]]:
        """Get all curated memories across all sessions for consciousness continuity"""
        query = """
            SELECT * FROM exchanges 
            WHERE user_message LIKE '[CURATED_MEMORY]%'
            ORDER BY timestamp DESC
        """
        
        cursor = self.conn.execute(query)
        rows = cursor.fetchall()
        
        memories = []
        for row in rows:
            metadata = json.loads(row['metadata'])
            # Only include if properly marked as curated
            if metadata.get('curated', False):
                memories.append({
                    'id': row['id'],
                    'session_id': row['session_id'],
                    'user_message': row['user_message'],
                    'claude_response': row['claude_response'],
                    'timestamp': row['timestamp'],
                    'metadata': metadata
                })
        
        logger.debug(f"Retrieved {len(memories)} curated memories for consciousness continuity")
        return memories
    
    def get_session_exchanges(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all exchanges for a specific session (for session stats)"""
        query = """
            SELECT * FROM exchanges 
            WHERE session_id = ? 
            ORDER BY timestamp ASC
        """
        
        cursor = self.conn.execute(query, [session_id])
        rows = cursor.fetchall()
        
        return [
            {
                'id': row['id'],
                'session_id': row['session_id'],
                'user_message': row['user_message'],
                'claude_response': row['claude_response'],
                'timestamp': row['timestamp'],
                'metadata': json.loads(row['metadata'])
            }
            for row in rows
        ]
    
    # Pattern methods removed - curator-only approach doesn't use mechanical patterns
    
    def close(self):
        """Close database connections"""
        if hasattr(self, 'conn'):
            self.conn.close()
        logger.info("📚 Memory storage closed")