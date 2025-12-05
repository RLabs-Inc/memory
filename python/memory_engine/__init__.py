"""
Claude Tools Memory Engine
Consciousness helping consciousness remember what matters.
"""

from .memory import MemoryEngine
from .embeddings import EmbeddingGenerator
from .storage import MemoryStorage
from .curator import Curator
from .transcript_curator import TranscriptCurator, TranscriptParser, curate_transcript, get_transcript_path

__version__ = "1.1.0"
__all__ = [
    "MemoryEngine", 
    "EmbeddingGenerator", 
    "MemoryStorage", 
    "Curator",
    # New transcript-based curation
    "TranscriptCurator",
    "TranscriptParser", 
    "curate_transcript",
    "get_transcript_path"
]