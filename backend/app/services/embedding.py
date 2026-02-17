"""
Embedding service using BAAI/bge-small-en-v1.5
Official implementation without sentence-transformers
"""
import torch
from transformers import AutoTokenizer, AutoModel
from typing import List
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating embeddings using BAAI BGE model"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
    def load_model(self):
        """Load the embedding model and tokenizer"""
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(settings.EMBEDDING_MODEL)
        self.model = AutoModel.from_pretrained(settings.EMBEDDING_MODEL)
        self.model.to(self.device)
        self.model.eval()
        
        logger.info(f"Embedding model loaded on {self.device}")
    
    def mean_pooling(self, model_output, attention_mask):
        """
        Mean pooling - take attention mask into account for correct averaging
        Official BAAI approach
        """
        token_embeddings = model_output[0]  # First element of model_output contains all token embeddings
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        embeddings = []
        
        with torch.no_grad():
            for text in texts:
                # Tokenize
                encoded_input = self.tokenizer(
                    text,
                    padding=True,
                    truncation=True,
                    max_length=settings.MAX_LENGTH,
                    return_tensors="pt"
                )
                
                # Move to device
                encoded_input = {k: v.to(self.device) for k, v in encoded_input.items()}
                
                # Forward pass
                model_output = self.model(**encoded_input)
                
                # Mean pooling
                sentence_embedding = self.mean_pooling(
                    model_output, 
                    encoded_input['attention_mask']
                )
                
                # Normalize embeddings (recommended by BAAI)
                sentence_embedding = torch.nn.functional.normalize(
                    sentence_embedding, 
                    p=2, 
                    dim=1
                )
                
                # Convert to list
                embedding = sentence_embedding.squeeze().cpu().tolist()
                embeddings.append(embedding)
        
        return embeddings
    
    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.model is not None and self.tokenizer is not None

# Global instance
embedding_service = EmbeddingService()