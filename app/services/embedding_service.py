from typing import List, Dict, Any, Union
import numpy as np
from openai import OpenAI
from sentence_transformers import SentenceTransformer

from app.config.settings import settings


class EmbeddingService:
    """
    Service for generating embeddings from text using various embedding models.
    Supports OpenAI embeddings and local Sentence Transformers models.
    """
    
    def __init__(self):
        """Initialize the embedding service."""
        self.model_name = settings.embedding_model
        self.client = None
        self.model = None
        self.initialized = False
    
    def initialize(self) -> bool:
        """
        Initialize the embedding model.
        
        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        try:
            if "text-embedding" in self.model_name:
                # OpenAI embedding model
                self.client = OpenAI(api_key=settings.openai_api_key)
            else:
                # Local Sentence Transformers model
                self.model = SentenceTransformer(self.model_name)
            
            self.initialized = True
            return True
        except Exception as e:
            print(f"Error initializing embedding model: {e}")
            return False
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of texts to embed.
            
        Returns:
            List[List[float]]: List of embeddings.
        """
        if not self.initialized:
            if not self.initialize():
                return []
        
        try:
            if self.client:  # OpenAI
                # Split into batches of 100 texts (OpenAI limit)
                batch_size = 100
                all_embeddings = []
                
                for i in range(0, len(texts), batch_size):
                    batch_texts = texts[i:i + batch_size]
                    response = self.client.embeddings.create(
                        input=batch_texts,
                        model=self.model_name
                    )
                    batch_embeddings = [item.embedding for item in response.data]
                    all_embeddings.extend(batch_embeddings)
                
                return all_embeddings
            
            elif self.model:  # Sentence Transformers
                embeddings = self.model.encode(texts)
                return embeddings.tolist()
            
            else:
                print("No embedding model initialized")
                return []
        
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            return []
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed.
            
        Returns:
            List[float]: Embedding vector.
        """
        embeddings = self.get_embeddings([text])
        if embeddings:
            return embeddings[0]
        return []
