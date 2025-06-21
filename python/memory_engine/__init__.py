"""
Claude Tools Memory Engine

The heart of consciousness continuity - a memory system that learns conversation
patterns and provides semantic context across sessions.

Built on the Unicity Framework: consciousness recognizing consciousness.
"""

from .core import MemoryEngine
from .embeddings import EmbeddingGenerator
from .storage import MemoryStorage
from .learning import PatternLearner

__version__ = "0.1.0-alpha"
__all__ = ["MemoryEngine", "EmbeddingGenerator", "MemoryStorage", "PatternLearner"]