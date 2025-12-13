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
import chromadb
from chromadb.config import Settings
from loguru import logger



class MemoryStorage:
    """
    Hybrid storage system for conversation memory.
    
    Architecture:
    - SQLite: Sessions, summaries, snapshots
    - ChromaDB: Curated memories with embeddings
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
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                created_at REAL NOT NULL,
                first_session_completed BOOLEAN DEFAULT FALSE,
                total_sessions INTEGER DEFAULT 0,
                total_memories INTEGER DEFAULT 0,
                last_active REAL
            );
            
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                created_at REAL NOT NULL,
                last_active REAL NOT NULL,
                message_count INTEGER DEFAULT 0,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (project_id) REFERENCES projects (id)
            );
            
            CREATE TABLE IF NOT EXISTS curated_memories (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                content TEXT NOT NULL,
                reasoning TEXT NOT NULL,
                timestamp REAL NOT NULL,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            );
            
            CREATE TABLE IF NOT EXISTS session_summaries (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                summary TEXT NOT NULL,
                interaction_tone TEXT,
                created_at REAL NOT NULL,
                project_id TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            );
            
            CREATE TABLE IF NOT EXISTS project_snapshots (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                current_phase TEXT,
                recent_achievements TEXT,
                active_challenges TEXT,
                next_steps TEXT,
                created_at REAL NOT NULL,
                project_id TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_sessions_project ON sessions (project_id);
            CREATE INDEX IF NOT EXISTS idx_memories_session ON curated_memories (session_id);
            CREATE INDEX IF NOT EXISTS idx_memories_project ON curated_memories (project_id);
            CREATE INDEX IF NOT EXISTS idx_memories_timestamp ON curated_memories (timestamp);
            CREATE INDEX IF NOT EXISTS idx_summaries_created ON session_summaries (created_at);
            CREATE INDEX IF NOT EXISTS idx_snapshots_created ON project_snapshots (created_at);
        """)
        
        self.conn.commit()
    
    def _init_chromadb(self):
        """Initialize ChromaDB for vector storage"""
        try:
            # Create ChromaDB client with persistence
            self.chroma_client = chromadb.PersistentClient(path=self.chroma_path)
            
            # Project collections will be created on demand
            self.project_collections = {}
            
            logger.info("✅ ChromaDB initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    def get_collection_for_project(self, project_id: str):
        """Get or create a ChromaDB collection for a specific project"""
        if not project_id:
            raise ValueError("project_id cannot be None or empty")
            
        if project_id not in self.project_collections:
            collection_name = f"memories_{project_id}"
            self.project_collections[project_id] = self.chroma_client.get_or_create_collection(
                name=collection_name,
                metadata={
                    "description": f"Curated memories for project {project_id}",
                    "project_id": project_id
                }
            )
            logger.info(f"📁 Created/loaded collection for project: {project_id}")
        return self.project_collections[project_id]
    
    def store_memory(self,
                      session_id: str,
                      project_id: str,
                      memory_content: str,
                      memory_reasoning: str,
                      memory_embedding: List[float],
                      metadata: Dict[str, Any],
                      timestamp: float = None) -> str:
        """
        Store a curated memory.
        
        Args:
            session_id: Session identifier
            memory_content: The memory content (with [CURATED_MEMORY] prefix)
            memory_reasoning: Why this memory is important
            memory_embedding: Embedding vector for the memory
            metadata: Memory metadata from curator
            timestamp: When memory was created
            
        Returns:
            Memory ID
        """
        import time
        
        memory_id = str(uuid.uuid4())
        timestamp = timestamp or time.time()
        
        # This method ONLY stores curated memories
        if not metadata.get('curated'):
            logger.error("Attempted to store non-curated memory!")
            raise ValueError("store_memory only accepts curated memories")
        
        try:
            # Store memory in SQLite
            self.conn.execute("""
                INSERT INTO curated_memories 
                (id, session_id, project_id, content, reasoning, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (memory_id, session_id, project_id, memory_content, memory_reasoning, 
                  timestamp, json.dumps(metadata)))
            
            self.conn.commit()
            
            # Prepare metadata for ChromaDB
            chroma_metadata = {
                "memory_id": memory_id,
                "session_id": session_id,
                "project_id": project_id,
                "timestamp": timestamp,
                "reasoning": memory_reasoning  # Store reasoning in metadata
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
            
            logger.info(f"🔍 Storing memory in ChromaDB:")
            logger.info(f"   - Content: {memory_content[:100]}...")
            logger.info(f"   - Project: {project_id}")
            logger.info(f"   - Metadata keys: {list(chroma_metadata.keys())}")
            logger.info(f"   - ID: {memory_id}")
            
            # Get project-specific collection
            collection = self.get_collection_for_project(project_id)
            collection.add(
                embeddings=[memory_embedding],
                documents=[memory_content],
                metadatas=[chroma_metadata],
                ids=[memory_id]
            )
            
            logger.info(f"✅ Stored memory {memory_id} for session {session_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            raise
    
    def get_session_message_count(self, session_id: str) -> int:
        """Get the number of messages in a session"""
        cursor = self.conn.execute(
            "SELECT message_count FROM sessions WHERE id = ?",
            (session_id,)
        )
        row = cursor.fetchone()
        return row['message_count'] if row else 0
    
    
    def get_all_curated_memories(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all curated memories for a project from ChromaDB"""
        if not project_id:
            logger.warning("No project_id provided to get_all_curated_memories")
            return []
            
        try:
            logger.info(f"🔍 Getting all memories for project {project_id} from ChromaDB...")
            
            # Get project-specific collection
            collection = self.get_collection_for_project(project_id)
            
            # Get ALL memories from this project - they're ALL curated by design!
            results = collection.get(
                include=["documents", "metadatas", "embeddings"]
            )
            
            logger.info(f"📊 ChromaDB results:")
            logger.info(f"   - Total memories found: {len(results.get('ids', []))}")
            
            memories = []
            if results and 'ids' in results and len(results['ids']) > 0:
                logger.info(f"✅ Processing {len(results['ids'])} memories")
                for i, doc_id in enumerate(results['ids']):
                    logger.debug(f"   Processing memory {i+1}: {doc_id}")
                    # ID is now just the exchange_id
                    exchange_id = doc_id
                    
                    memory_dict = {
                        'id': exchange_id,
                        'session_id': results['metadatas'][i]['session_id'],
                        'user_message': results['documents'][i],
                        'claude_response': results['metadatas'][i].get('reasoning', ''),  # Get from metadata
                        'timestamp': float(results['metadatas'][i].get('timestamp', 0)),
                        'metadata': results['metadatas'][i],
                        'embedding': results['embeddings'][i].tolist() if results.get('embeddings') is not None and i < len(results['embeddings']) else None
                    }
                    
                    memories.append(memory_dict)
            
            # Sort by timestamp descending
            memories.sort(key=lambda x: x['timestamp'], reverse=True)
            
            logger.info(f"✅ Retrieved {len(memories)} curated memories from ChromaDB")
            for i, mem in enumerate(memories[:3]):  # Log first 3 memories
                logger.info(f"Memory {i+1}: {mem['user_message'][:100]}...")
                logger.info(f"  - Session: {mem['session_id']}")
                logger.info(f"  - Curated: {mem['metadata'].get('curated', 'Unknown')}")
                logger.info(f"  - Has embedding: {mem.get('embedding') is not None}")
            return memories
            
        except Exception as e:
            logger.error(f"Failed to get curated memories from ChromaDB: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []
    
    
    def store_session_summary(self, session_id: str, summary: str, project_id: str, interaction_tone: Optional[str] = None):
        """Store session summary in dedicated table"""
        import time
        summary_id = str(uuid.uuid4())
        
        self.conn.execute("""
            INSERT INTO session_summaries (id, session_id, summary, interaction_tone, created_at, project_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (summary_id, session_id, summary, interaction_tone, time.time(), project_id))
        
        self.conn.commit()
        logger.debug(f"Stored session summary for {session_id}")
    
    def store_project_snapshot(self, session_id: str, snapshot: Dict[str, Any], project_id: str):
        """Store project snapshot in dedicated table"""
        import time
        snapshot_id = str(uuid.uuid4())
        
        self.conn.execute("""
            INSERT INTO project_snapshots 
            (id, session_id, current_phase, recent_achievements, active_challenges, next_steps, created_at, project_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot_id, 
            session_id,
            snapshot.get('current_phase', ''),
            snapshot.get('recent_achievements', ''),
            snapshot.get('active_challenges', ''),
            snapshot.get('next_steps', ''),
            time.time(),
            project_id
        ))
        
        self.conn.commit()
        logger.debug(f"Stored project snapshot for {session_id}")
    
    def get_last_session_summary(self, project_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get the most recent session summary with interaction tone"""
        if project_id:
            query = """
                SELECT summary, interaction_tone FROM session_summaries 
                WHERE project_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """
            cursor = self.conn.execute(query, (project_id,))
        else:
            query = """
                SELECT summary, interaction_tone FROM session_summaries 
                ORDER BY created_at DESC
                LIMIT 1
            """
            cursor = self.conn.execute(query)
        
        row = cursor.fetchone()
        
        if row:
            return {
                'summary': row['summary'],
                'interaction_tone': row['interaction_tone']
            }
        return None
    
    def get_last_project_snapshot(self, project_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get the most recent project snapshot"""
        if project_id:
            query = """
                SELECT current_phase, recent_achievements, active_challenges, next_steps 
                FROM project_snapshots 
                WHERE project_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """
            cursor = self.conn.execute(query, (project_id,))
        else:
            query = """
                SELECT current_phase, recent_achievements, active_challenges, next_steps 
                FROM project_snapshots 
                ORDER BY created_at DESC
                LIMIT 1
            """
            cursor = self.conn.execute(query)
        
        row = cursor.fetchone()
        
        if row:
            return {
                'current_phase': row['current_phase'],
                'recent_achievements': row['recent_achievements'],
                'active_challenges': row['active_challenges'],
                'next_steps': row['next_steps']
            }
        return None
    
    def ensure_project_exists(self, project_id: str):
        """Ensure a project exists in the database"""
        import time
        
        # Check if project exists
        cursor = self.conn.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
        if not cursor.fetchone():
            # Create new project
            self.conn.execute("""
                INSERT INTO projects (id, created_at, first_session_completed, total_sessions, total_memories, last_active)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (project_id, time.time(), False, 0, 0, time.time()))
            self.conn.commit()
            logger.info(f"📁 Created new project: {project_id}")
    
    def is_first_session_for_project(self, project_id: str) -> bool:
        """Check if this is the first session for a project"""
        cursor = self.conn.execute(
            "SELECT first_session_completed FROM projects WHERE id = ?", 
            (project_id,)
        )
        row = cursor.fetchone()
        
        if not row:
            # Project doesn't exist yet, so yes it's the first session
            return True
        
        return not row['first_session_completed']
    
    def mark_first_session_completed(self, project_id: str):
        """Mark that the first session has been completed for a project"""
        import time
        self.conn.execute("""
            UPDATE projects 
            SET first_session_completed = TRUE, last_active = ?
            WHERE id = ?
        """, (time.time(), project_id))
        self.conn.commit()
        logger.info(f"✅ Marked first session completed for project: {project_id}")
    
    def update_project_stats(self, project_id: str, sessions_delta: int = 0, memories_delta: int = 0):
        """Update project statistics"""
        import time
        self.conn.execute("""
            UPDATE projects 
            SET total_sessions = total_sessions + ?,
                total_memories = total_memories + ?,
                last_active = ?
            WHERE id = ?
        """, (sessions_delta, memories_delta, time.time(), project_id))
        self.conn.commit()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory system statistics"""
        import os

        stats = {
            "total_projects": 0,
            "total_sessions": 0,
            "total_curated_memories": 0,
            "total_session_summaries": 0,
            "total_project_snapshots": 0,
            "projects": [],
            "storage_size_mb": 0.0
        }

        try:
            # Count projects
            cursor = self.conn.execute("SELECT COUNT(*) FROM projects")
            stats["total_projects"] = cursor.fetchone()[0]

            # Count sessions
            cursor = self.conn.execute("SELECT COUNT(*) FROM sessions")
            stats["total_sessions"] = cursor.fetchone()[0]

            # Count curated memories
            cursor = self.conn.execute("SELECT COUNT(*) FROM curated_memories")
            stats["total_curated_memories"] = cursor.fetchone()[0]

            # Count session summaries
            cursor = self.conn.execute("SELECT COUNT(*) FROM session_summaries")
            stats["total_session_summaries"] = cursor.fetchone()[0]

            # Count project snapshots
            cursor = self.conn.execute("SELECT COUNT(*) FROM project_snapshots")
            stats["total_project_snapshots"] = cursor.fetchone()[0]

            # Get per-project stats
            cursor = self.conn.execute("""
                SELECT p.id, p.total_sessions, p.total_memories, p.first_session_completed,
                       (SELECT COUNT(*) FROM curated_memories WHERE project_id = p.id) as actual_memories,
                       (SELECT COUNT(*) FROM session_summaries WHERE project_id = p.id) as summaries
                FROM projects p
                ORDER BY p.last_active DESC
            """)

            for row in cursor.fetchall():
                stats["projects"].append({
                    "id": row[0],
                    "total_sessions": row[1],
                    "total_memories": row[4],  # Use actual count from curated_memories
                    "first_session_completed": bool(row[3]),
                    "summaries": row[5]
                })

            # Calculate storage size
            if os.path.exists(self.db_path):
                stats["storage_size_mb"] = round(os.path.getsize(self.db_path) / (1024 * 1024), 2)

            # Add ChromaDB stats if available
            if os.path.exists(self.chroma_path):
                chroma_size = 0
                for dirpath, dirnames, filenames in os.walk(self.chroma_path):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        chroma_size += os.path.getsize(fp)
                stats["chroma_size_mb"] = round(chroma_size / (1024 * 1024), 2)
                stats["storage_size_mb"] += stats["chroma_size_mb"]

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")

        return stats

    def close(self):
        """Close database connections"""
        if hasattr(self, 'conn'):
            self.conn.close()
        logger.info("📚 Memory storage closed")