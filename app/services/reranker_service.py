from typing import List, Dict, Any
import cohere
import numpy as np

from app.config.settings import settings


class RerankerService:
    """
    Service for reranking retrieved documents to improve relevance.
    Uses Cohere's reranking API.
    """
    
    def __init__(self):
        """Initialize the reranker service."""
        self.client = None
        self.initialized = False
    
    def initialize(self) -> bool:
        """
        Initialize the reranker client.
        
        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        try:
            self.client = cohere.Client(settings.cohere_api_key)
            self.initialized = True
            return True
        except Exception as e:
            print(f"Error initializing reranker: {e}")
            return False
    
    def rerank(
        self, 
        query: str, 
        documents: List[Dict[str, Any]], 
        top_n: int = None
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents based on relevance to the query.
        
        Args:
            query: The query to rerank against.
            documents: List of documents to rerank.
            top_n: Number of results to return after reranking.
            
        Returns:
            List[Dict[str, Any]]: Reranked documents.
        """
        if not self.initialized:
            if not self.initialize():
                return documents
        
        if not documents:
            return []
        
        if top_n is None:
            top_n = len(documents)
        
        try:
            # Extract document texts
            docs = [doc["content"] for doc in documents]
            
            # Call Cohere rerank API
            response = self.client.rerank(
                query=query,
                documents=docs,
                model="rerank-english-v3.0",
                top_n=top_n
            )
            
            # Create reranked documents list
            reranked_docs = []
            for result in response.results:
                idx = result.index
                reranked_docs.append({
                    **documents[idx],
                    "relevance_score": result.relevance_score
                })
            
            return reranked_docs
        
        except Exception as e:
            print(f"Error reranking documents: {e}")
            return documents
