"""
PR #9 Fix: Real stats gathering in /memory/stats endpoint.

Before: /memory/stats returned placeholder zeros
After: Returns actual counts from database queries via get_stats() method
"""

import os
import shutil
import tempfile

from memory_engine.storage import MemoryStorage


class TestGetStats:
    """Test get_stats() returns real database statistics"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_memory.db")
        self.storage = MemoryStorage(db_path=self.db_path)
        # Override chroma_path after init
        self.storage.chroma_path = os.path.join(self.temp_dir, "test_chroma")
        os.makedirs(self.storage.chroma_path, exist_ok=True)

    def teardown_method(self):
        self.storage.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_stats_returns_real_counts(self):
        """
        PR #9 FIX: get_stats() queries the database and returns actual counts
        instead of placeholder zeros.
        """
        # Insert test data
        project_id = "test-project"

        self.storage.conn.execute(
            """
            INSERT INTO projects (id, total_sessions, total_memories, first_session_completed, last_active, created_at)
            VALUES (?, 0, 0, 0, ?, ?)
        """,
            (project_id, 1234567890, 1234567890),
        )

        self.storage.conn.execute(
            """
            INSERT INTO sessions (id, project_id, created_at, last_active)
            VALUES (?, ?, ?, ?)
        """,
            ("session-1", project_id, 1234567890, 1234567890),
        )

        self.storage.conn.execute(
            """
            INSERT INTO curated_memories (
                id, session_id, project_id, content, reasoning, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?)
        """,
            ("mem-1", "session-1", project_id, "Test memory", "Testing", 1234567890),
        )

        self.storage.conn.commit()

        stats = self.storage.get_stats()

        assert stats["total_projects"] == 1
        assert stats["total_sessions"] == 1
        assert stats["total_curated_memories"] == 1
        assert len(stats["projects"]) == 1
        assert stats["projects"][0]["id"] == project_id
