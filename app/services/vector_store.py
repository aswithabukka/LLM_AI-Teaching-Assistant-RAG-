import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
import numpy as np

from app.config.settings import settings


class VectorStore:
    """
    Vector database service for storing and retrieving document embeddings.
    Uses ChromaDB as the vector database.
    """
    
    def __init__(self):
        """Initialize the vector store service."""
        self.client = None
        self.collection = None
        self.collection_name = "course_notes_embeddings"
        self.dimension = settings.vector_db_dimension
        self.initialized = False
    
    def initialize(self) -> bool:
        """
        Initialize the connection to ChromaDB.
        
        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        # Quick validation before attempting connection
        try:
            print("Initializing ChromaDB vector store...")
            
            # Initialize ChromaDB client (persistent storage)
            persist_directory = os.path.join(os.getcwd(), "data", "chromadb")
            os.makedirs(persist_directory, exist_ok=True)
            
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(
                    anonymized_telemetry=False
                )
            )
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(
                    name=self.collection_name
                )
                print(f"Connected to existing ChromaDB collection: {self.collection_name}")
            except:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
                print(f"Created new ChromaDB collection: {self.collection_name}")
            
            self.initialized = True
            return True
            
        except Exception as e:
            print(f"Error initializing ChromaDB: {e}")
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
            # Prepare data for ChromaDB
            ids = []
            embeddings = []
            metadatas = []
            documents = []
            
            for vector in vectors:
                ids.append(vector["id"])
                embeddings.append(vector["values"])
                metadata = vector.get("metadata", {})
                metadatas.append(metadata)
                # Use content from metadata as document text
                documents.append(metadata.get("content", ""))
            
            # Check if any IDs already exist and handle duplicates
            try:
                existing_results = self.collection.get(ids=ids)
                existing_ids = set(existing_results.get("ids", []))
                
                # Filter out existing IDs to avoid duplicates
                new_ids = []
                new_embeddings = []
                new_metadatas = []
                new_documents = []
                
                for i, doc_id in enumerate(ids):
                    if doc_id not in existing_ids:
                        new_ids.append(doc_id)
                        new_embeddings.append(embeddings[i])
                        new_metadatas.append(metadatas[i])
                        new_documents.append(documents[i])
                
                if new_ids:
                    # Add only new vectors to ChromaDB collection
                    self.collection.add(
                        ids=new_ids,
                        embeddings=new_embeddings,
                        metadatas=new_metadatas,
                        documents=new_documents
                    )
                    print(f"Successfully added {len(new_ids)} new vectors to ChromaDB")
                else:
                    print(f"All {len(vectors)} vectors already exist in ChromaDB")
                    
            except Exception as get_error:
                # If get() fails, try adding all vectors (collection might be empty)
                print(f"Could not check existing vectors, adding all: {get_error}")
                self.collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    documents=documents
                )
                print(f"Successfully added {len(vectors)} vectors to ChromaDB")
            
            return True
            
        except Exception as e:
            import traceback
            print(f"Error adding vectors to ChromaDB: {e}")
            print(f"ChromaDB error details: {traceback.format_exc()}")
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
            # Delete vectors from ChromaDB collection
            self.collection.delete(ids=vector_ids)
            print(f"Successfully deleted {len(vector_ids)} vectors from ChromaDB")
            return True
        except Exception as e:
            print(f"Error deleting vectors from ChromaDB: {e}")
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
            # Query ChromaDB
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                where=filter
            )
            
            # Format the results for ChromaDB
            formatted_results = []
            if results["ids"] and len(results["ids"]) > 0:
                for i, doc_id in enumerate(results["ids"][0]):
                    formatted_results.append({
                        "id": doc_id,
                        "score": 1.0 - results["distances"][0][i],  # Convert distance to similarity
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {}
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
            # For ChromaDB, we can delete directly using where clause
            self.collection.delete(where=metadata_filter)
            print(f"Successfully deleted vectors with metadata filter: {metadata_filter}")
            return True
        except Exception as e:
            print(f"Error deleting vectors by metadata: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector database.
        
        Args:
            None
        
        Returns:
            Dict[str, Any]: Statistics about the vector database.
        """
        if not self.initialized:
            if not self.initialize():
                return {"error": "Vector store not initialized"}
        
        try:
            # Get collection info
            collection_info = self.collection.get()
            return {
                "collection_name": self.collection_name,
                "total_vectors": len(collection_info.get("ids", [])),
                "dimension": self.dimension,
                "initialized": self.initialized
            }
        except Exception as e:
            return {"error": f"Failed to get stats: {e}"}
    
    def list_vectors_by_document(self, document_id: int) -> List[Dict[str, Any]]:
        """
        List all vectors for a specific document (for debugging).
        
        Args:
            document_id: The document ID to search for.
            
        Returns:
            List[Dict[str, Any]]: List of vectors with metadata.
        """
        if not self.initialized:
            if not self.initialize():
                return []
        
        try:
            # Query all vectors for this document
            results = self.collection.get(
                where={"document_id": {"$eq": document_id}},
                include=["metadatas", "documents"]
            )
            
            vectors = []
            if results["ids"]:
                for i, vector_id in enumerate(results["ids"]):
                    vectors.append({
                        "id": vector_id,
                        "metadata": results["metadatas"][i] if results["metadatas"] else {},
                        "content_preview": results["documents"][i][:100] + "..." if results["documents"] and results["documents"][i] else ""
                    })
            
            return vectors
        except Exception as e:
            print(f"Error listing vectors for document {document_id}: {e}")
            return []
