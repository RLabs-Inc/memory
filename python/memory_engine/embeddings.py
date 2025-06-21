"""
Embedding Generator

Converts text into semantic vectors for similarity matching and memory retrieval.
Uses efficient, lightweight models optimized for real-time operation.
"""

from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer
from loguru import logger


class EmbeddingGenerator:
    """
    Generates semantic embeddings for text using SentenceTransformers.
    
    Optimized for:
    - Real-time embedding generation
    - Semantic similarity matching
    - Memory-efficient operation
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding model.
        
        Default model (all-MiniLM-L6-v2):
        - 384 dimensions (compact)
        - 22.7M parameters (lightweight)
        - Good balance of speed and quality
        """
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the embedding model with error handling"""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("✅ Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of float values representing the embedding vector
        """
        if not text or not text.strip():
            return [0.0] * self.get_embedding_dimension()
        
        try:
            # Generate embedding
            embedding = self.model.encode(text.strip(), convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return [0.0] * self.get_embedding_dimension()
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        try:
            # Clean and prepare texts
            clean_texts = [text.strip() if text and text.strip() else " " for text in texts]
            
            # Batch embedding generation
            embeddings = self.model.encode(clean_texts, convert_to_numpy=True)
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            # Return zero vectors as fallback
            dim = self.get_embedding_dimension()
            return [[0.0] * dim for _ in texts]
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this model"""
        if self.model is None:
            return 384  # Default for all-MiniLM-L6-v2
        return self.model.get_sentence_embedding_dimension()
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score between -1 and 1 (higher = more similar)
        """
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Compute cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
        except Exception as e:
            logger.error(f"Failed to compute similarity: {e}")
            return 0.0
    
    def find_most_similar(self, 
                         query_embedding: List[float], 
                         candidate_embeddings: List[List[float]],
                         top_k: int = 5) -> List[tuple]:
        """
        Find the most similar embeddings to a query.
        
        Args:
            query_embedding: The embedding to search for
            candidate_embeddings: List of embeddings to search through
            top_k: Number of top results to return
            
        Returns:
            List of (index, similarity_score) tuples, sorted by similarity
        """
        if not candidate_embeddings:
            return []
        
        similarities = []
        for i, candidate in enumerate(candidate_embeddings):
            similarity = self.compute_similarity(query_embedding, candidate)
            similarities.append((i, similarity))
        
        # Sort by similarity (highest first) and return top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]