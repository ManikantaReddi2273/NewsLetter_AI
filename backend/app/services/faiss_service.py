"""FAISS vector search service for semantic article search."""
import faiss
import numpy as np
import pickle
import io
from typing import List, Tuple, Optional
from sentence_transformers import SentenceTransformer
from loguru import logger
from app.config import get_settings

settings = get_settings()


class FAISSService:
    """Service for managing FAISS index and semantic search."""
    
    def __init__(self):
        """Initialize FAISS service."""
        self.model = None
        self.index = None
        self.article_id_map = {}  # Maps FAISS index to article ID
        self.dimension = settings.FAISS_DIMENSION
        # Don't load model immediately - lazy load when needed
        self._initialize_index()
    
    def _load_model(self):
        """Load sentence transformer model (lazy loading)."""
        if self.model is not None:
            return
            
        try:
            logger.info("Loading sentence-transformers model: all-MiniLM-L6-v2")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def _initialize_index(self):
        """Initialize FAISS index."""
        try:
            logger.info(f"Initializing FAISS index with dimension {self.dimension}")
            # Using IndexFlatL2 for exact L2 distance search
            self.index = faiss.IndexFlatL2(self.dimension)
            logger.info("FAISS index initialized")
        except Exception as e:
            logger.error(f"Failed to initialize FAISS index: {e}")
            raise
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text to embed
            
        Returns:
            Numpy array of shape (384,)
        """
        try:
            # Lazy load model when first needed
            self._load_model()
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.astype('float32')
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    def generate_embeddings_batch(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            Numpy array of shape (n, 384)
        """
        try:
            # Lazy load model when first needed
            self._load_model()
            embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
            return embeddings.astype('float32')
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise
    
    def add_embeddings(self, embeddings: np.ndarray, article_ids: List[int]):
        """
        Add embeddings to FAISS index.
        
        Args:
            embeddings: Numpy array of embeddings (n, 384)
            article_ids: List of corresponding article IDs
        """
        try:
            if len(embeddings) != len(article_ids):
                raise ValueError("Number of embeddings must match number of article IDs")
            
            # Get current index count
            start_idx = self.index.ntotal
            
            # Add to FAISS index
            self.index.add(embeddings)
            
            # Update article ID mapping
            for i, article_id in enumerate(article_ids):
                self.article_id_map[start_idx + i] = article_id
            
            logger.info(f"Added {len(embeddings)} embeddings to FAISS index. Total: {self.index.ntotal}")
        except Exception as e:
            logger.error(f"Failed to add embeddings to FAISS index: {e}")
            raise

    def add_single_embedding(self, embedding: np.ndarray, article_id: int):
        """Add a single embedding to the index and map it to an article."""
        try:
            embedding = embedding.reshape(1, -1).astype("float32")
            start_idx = self.index.ntotal
            self.index.add(embedding)
            self.article_id_map[start_idx] = article_id
            logger.info(f"Added embedding for article {article_id}. Total: {self.index.ntotal}")
        except Exception as e:
            logger.error(f"Failed to add single embedding: {e}")
            raise

    def rebuild_from_embeddings(self, rows: List[Tuple[int, bytes]]):
        """Rebuild the FAISS index from stored embeddings in the database."""
        try:
            self._initialize_index()
            self.article_id_map = {}
            if not rows:
                logger.warning("No stored embeddings found to rebuild FAISS index")
                return
            vectors = []
            article_ids = []
            for article_id, blob in rows:
                if not blob:
                    continue
                try:
                    vec = pickle.loads(blob)
                    vec = np.array(vec, dtype="float32").reshape(1, -1)
                    vectors.append(vec)
                    article_ids.append(article_id)
                except Exception as inner:
                    logger.warning(f"Skipping embedding for article {article_id}: {inner}")
            if not vectors:
                logger.warning("No valid embeddings to rebuild FAISS index")
                return
            matrix = np.vstack(vectors)
            self.index.add(matrix)
            for i, aid in enumerate(article_ids):
                self.article_id_map[i] = aid
            logger.info(f"Rebuilt FAISS index with {len(article_ids)} vectors")
        except Exception as e:
            logger.error(f"Failed to rebuild FAISS index: {e}")
            raise
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[int, float]]:
        """
        Search for similar articles using semantic similarity.
        
        Args:
            query: Search query text
            top_k: Number of top results to return
            
        Returns:
            List of tuples (article_id, distance)
        """
        try:
            if self.index.ntotal == 0:
                logger.warning("FAISS index is empty")
                return []
            
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            query_embedding = query_embedding.reshape(1, -1)
            
            # Search in FAISS
            top_k = min(top_k, self.index.ntotal)
            distances, indices = self.index.search(query_embedding, top_k)
            
            # Convert to article IDs
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx in self.article_id_map:
                    article_id = self.article_id_map[idx]
                    results.append((article_id, float(dist)))
            
            logger.info(f"Found {len(results)} results for query: {query[:50]}...")
            return results
        except Exception as e:
            logger.error(f"Failed to search FAISS index: {e}")
            raise

    def search_by_embedding(self, embedding: np.ndarray, top_k: int = 5) -> List[Tuple[int, float]]:
        """Search using a precomputed embedding."""
        try:
            if self.index.ntotal == 0:
                logger.warning("FAISS index is empty")
                return []
            emb = embedding.reshape(1, -1).astype("float32")
            top_k = min(top_k, self.index.ntotal)
            distances, indices = self.index.search(emb, top_k)
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx in self.article_id_map:
                    results.append((self.article_id_map[idx], float(dist)))
            return results
        except Exception as e:
            logger.error(f"Failed to search by embedding: {e}")
            raise
    
    def save_index(self, filepath: str):
        """
        Save FAISS index to disk.
        
        Args:
            filepath: Path to save the index
        """
        try:
            index_data = {
                'index': faiss.serialize_index(self.index),
                'article_id_map': self.article_id_map
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(index_data, f)
            
            logger.info(f"FAISS index saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")
            raise
    
    def load_index(self, filepath: str):
        """
        Load FAISS index from disk.
        
        Args:
            filepath: Path to load the index from
        """
        try:
            with open(filepath, 'rb') as f:
                index_data = pickle.load(f)
            
            self.index = faiss.deserialize_index(index_data['index'])
            self.article_id_map = index_data['article_id_map']
            
            logger.info(f"FAISS index loaded from {filepath}. Total vectors: {self.index.ntotal}")
        except Exception as e:
            logger.error(f"Failed to load FAISS index: {e}")
            raise
    
    def save_to_bytes(self) -> bytes:
        """
        Serialize FAISS index to bytes (for storing in database).
        
        Returns:
            Serialized index as bytes
        """
        try:
            index_data = {
                'index': faiss.serialize_index(self.index),
                'article_id_map': self.article_id_map
            }
            
            buffer = io.BytesIO()
            pickle.dump(index_data, buffer)
            buffer.seek(0)
            
            return buffer.read()
        except Exception as e:
            logger.error(f"Failed to serialize FAISS index: {e}")
            raise
    
    def load_from_bytes(self, data: bytes):
        """
        Deserialize FAISS index from bytes.
        
        Args:
            data: Serialized index bytes
        """
        try:
            buffer = io.BytesIO(data)
            index_data = pickle.load(buffer)
            
            self.index = faiss.deserialize_index(index_data['index'])
            self.article_id_map = index_data['article_id_map']
            
            logger.info(f"FAISS index loaded from bytes. Total vectors: {self.index.ntotal}")
        except Exception as e:
            logger.error(f"Failed to deserialize FAISS index: {e}")
            raise
    
    def get_index_stats(self) -> dict:
        """Get statistics about the FAISS index."""
        return {
            "total_vectors": self.index.ntotal,
            "dimension": self.dimension,
            "index_type": "IndexFlatL2",
            "articles_indexed": len(self.article_id_map)
        }


# Global FAISS service instance
faiss_service = FAISSService()
