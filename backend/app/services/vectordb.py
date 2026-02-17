"""
Vector database service using Qdrant
"""
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Any
import uuid
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

class VectorDBService:
    """Service for managing vector database operations"""
    
    def __init__(self):
        self.client = None
        
    def connect(self):
        """Connect to Qdrant and create collection if needed"""
        logger.info(f"Connecting to Qdrant at {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
        
        self.client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT
        )
        
        # Create collection if it doesn't exist
        try:
            self.client.get_collection(settings.COLLECTION_NAME)
            logger.info(f"Collection '{settings.COLLECTION_NAME}' already exists")
        except Exception:
            logger.info(f"Creating collection '{settings.COLLECTION_NAME}'")
            self.client.create_collection(
                collection_name=settings.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=settings.EMBEDDING_DIM, 
                    distance=Distance.COSINE
                )
            )
    
    def store_embeddings(
        self, 
        embeddings: List[List[float]], 
        chunks: List[str], 
        filename: str
    ) -> int:
        """
        Store embeddings in Qdrant
        
        Args:
            embeddings: List of embedding vectors
            chunks: List of text chunks
            filename: Source filename
            
        Returns:
            Number of points stored
        """
        if self.client is None:
            raise RuntimeError("Not connected to Qdrant. Call connect() first.")
        
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point_id = str(uuid.uuid4())
            points.append(
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "text": chunk,
                        "source": filename,
                        "chunk_id": i
                    }
                )
            )
        
        self.client.upsert(
            collection_name=settings.COLLECTION_NAME,
            points=points
        )
        
        return len(points)
    
    def search(
        self, 
        query_embedding: List[float], 
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors
        
        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            
        Returns:
            List of search results with text and metadata
        """
        if self.client is None:
            raise RuntimeError("Not connected to Qdrant. Call connect() first.")
        
        search_results = self.client.search(
            collection_name=settings.COLLECTION_NAME,
            query_vector=query_embedding,
            limit=top_k
        )
        
        results = []
        for result in search_results:
            results.append({
                "text": result.payload['text'],
                "source": result.payload['source'],
                "chunk_id": result.payload['chunk_id'],
                "score": result.score
            })
        
        return results
    
    def is_connected(self) -> bool:
        """Check if connected to Qdrant"""
        return self.client is not None

# Global instance
vectordb_service = VectorDBService()