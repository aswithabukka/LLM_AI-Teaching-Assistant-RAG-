import os
import json
from typing import List, Dict, Any, Optional, Tuple
import pinecone
import numpy as np

from app.config.settings import settings


class VectorStore:
    """
    Vector database service for storing and retrieving document embeddings.
    Uses Pinecone as the vector database.
    """
    
    def __init__(self):
        """Initialize the vector store service."""
        self.pc = None
        self.index = None
        self.index_name = settings.vector_db_name
        self.dimension = settings.vector_db_dimension
        self.initialized = False
    
    def initialize(self) -> bool:
        """
        Initialize the connection to Pinecone.
        
        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        # Quick validation before attempting connection
        if not settings.pinecone_api_key or settings.pinecone_api_key == "":
            print("No Pinecone API key provided. Vector store will not be available.")
            return False
            
        try:
            import requests
            from requests.adapters import HTTPAdapter
            
            # Configure with short timeouts to fail quickly
            session = requests.Session()
            adapter = HTTPAdapter(max_retries=1)  # Minimal retries
            session.mount('https://', adapter)
            
            # Initialize Pinecone client with custom session and timeouts
            self.pc = pinecone.Pinecone(
                api_key=settings.pinecone_api_key,
                request_options={
                    "timeout": 3.0  # Short 3 second timeout
                }
            )
            
            # Quick check if index exists with timeout
            existing_indexes = self.pc.list_indexes().names()
            
            if self.index_name not in existing_indexes:
                # Create a new index with timeouts
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric="cosine",
                    spec=pinecone.ServerlessSpec(cloud="aws", region="us-east-1")
                )
            
            # Connect to the index
            self.index = self.pc.Index(self.index_name)
            self.initialized = True
            return True
        except Exception as e:
            print(f"Error initializing vector store: {e}")
            return False
    
    def upsert_vectors(self, vectors: List[Dict[str, Any]]) -> bool:
        """
        Insert or update vectors in the vector database.
        
        Args:
            vectors: List of vectors to insert or update.
                Each vector should have 'id', 'values', and 'metadata' keys.
        
        Returns:
            bool: True if upsert was successful, False otherwise.
        """
        if not self.initialized:
            if not self.initialize():
                return False
        
        try:
            # Upsert vectors in batches of 100
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.index.upsert(vectors=batch)
            return True
        except Exception as e:
            print(f"Error upserting vectors: {e}")
            return False
    
    def delete_vectors(self, vector_ids: List[str]) -> bool:
        """
        Delete vectors from the vector database.
        
        Args:
            vector_ids: List of vector IDs to delete.
        
        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        if not self.initialized:
            if not self.initialize():
                return False
        
        try:
            # Delete vectors in batches of 100
            batch_size = 100
            for i in range(0, len(vector_ids), batch_size):
                batch = vector_ids[i:i + batch_size]
                self.index.delete(ids=batch)
            return True
        except Exception as e:
            print(f"Error deleting vectors: {e}")
            return False
    
    def query_vectors(
        self, 
        query_vector: List[float], 
        top_k: int = 5, 
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query the vector database for similar vectors.
        
        Args:
            query_vector: The query vector.
            top_k: Number of results to return.
            filter: Filter to apply to the query.
        
        Returns:
            List[Dict[str, Any]]: List of query results.
        """
        if not self.initialized:
            if not self.initialize():
                return []
        
        try:
            # Query the index
            results = self.index.query(
                vector=query_vector,
                top_k=top_k,
                include_values=False,
                include_metadata=True,
                filter=filter
            )
            
            # Format the results
            formatted_results = []
            for match in results["matches"]:
                formatted_results.append({
                    "id": match["id"],
                    "score": match["score"],
                    "metadata": match["metadata"]
                })
            
            return formatted_results
        except Exception as e:
            print(f"Error querying vectors: {e}")
            return []
    
    def delete_by_metadata(self, metadata_filter: Dict[str, Any]) -> bool:
        """
        Delete vectors based on metadata filter.
        
        Args:
            metadata_filter: Filter to apply for deletion.
        
        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        if not self.initialized:
            if not self.initialize():
                return False
        
        try:
            # First, query to get the IDs of vectors to delete
            results = self.index.query(
                vector=[0.0] * self.dimension,  # Dummy vector
                top_k=10000,  # Get as many as possible
                include_values=False,
                include_metadata=False,
                filter=metadata_filter
            )
            
            # Extract IDs
            vector_ids = [match["id"] for match in results["matches"]]
            
            # Delete the vectors
            if vector_ids:
                return self.delete_vectors(vector_ids)
            
            return True
        except Exception as e:
            print(f"Error deleting vectors by metadata: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector database.
        
        Returns:
            Dict[str, Any]: Statistics about the vector database.
        """
        if not self.initialized:
            if not self.initialize():
                return {}
        
        try:
            # Get index stats
            stats = self.index.describe_index_stats()
            return stats
        except Exception as e:
            print(f"Error getting vector store stats: {e}")
            return {"namespaces": {}, "dimension": self.dimension, "total_vector_count": 0}
