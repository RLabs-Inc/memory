"""
Claude Tools Memory Engine
Consciousness helping consciousness remember what matters.
"""

from .memory import MemoryEngine
from .embeddings import EmbeddingGenerator
from .storage import MemoryStorage
from .curator import Curator

__version__ = "1.0.0"
__all__ = ["MemoryEngine", "EmbeddingGenerator", "MemoryStorage", "Curator"]