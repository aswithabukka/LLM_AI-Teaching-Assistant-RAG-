from typing import List, Dict, Any, Optional
import uuid
import json
from sqlalchemy.orm import Session

from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore
from app.services.reranker_service import RerankerService
from app.services.llm_service import LLMService
from app.models.database import Document, DocumentChunk, ChatSession, ChatMessage, Citation
from app.config.settings import settings


class RAGPipeline:
    """
    Retrieval-Augmented Generation pipeline for the course notes Q&A application.
    Handles the entire process from question to answer with citations.
    """
    
    def __init__(self):
        """Initialize the RAG pipeline."""
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
        self.reranker_service = RerankerService()
        self.llm_service = LLMService()
        
        # Initialize core services immediately
        self.embedding_service.initialize()
        self.reranker_service.initialize()
        self.llm_service.initialize()
        
        # Vector store will be initialized lazily when needed
        self._vector_store_initialized = False
    
    def _ensure_vector_store(self) -> bool:
        """Ensure vector store is initialized when needed"""
        if not self._vector_store_initialized:
            self._vector_store_initialized = self.vector_store.initialize()
        return self._vector_store_initialized
    
    def index_document_chunks(
        self, 
        chunks: List[Dict[str, Any]], 
        document_id: int
    ) -> List[str]:
        """
        Index document chunks in the vector database.
        
        Args:
            chunks: List of document chunks to index.
            document_id: ID of the document.
            
        Returns:
            List[str]: List of vector IDs.
        """
        # Generate embeddings for chunks
        texts = [chunk["content"] for chunk in chunks]
        embeddings = self.embedding_service.get_embeddings(texts)
        
        if not embeddings:
            return []
        
        # Prepare vectors for indexing
        vectors = []
        vector_ids = []
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            vector_id = f"chunk_{document_id}_{i}"
            
            # Add to vector list
            vectors.append({
                "id": vector_id,
                "values": embedding,
                "metadata": {
                    "document_id": document_id,
                    "chunk_index": i,
                    "content": chunk["content"],
                    "page": chunk.get("page", 0),
                    "source": chunk.get("source", ""),
                }
            })
            
            vector_ids.append(vector_id)
        
        # Lazy initialize vector store before upserting
        if vectors and self._ensure_vector_store():
            self.vector_store.upsert_vectors(vectors)
        
        return vector_ids
    
    def retrieve_relevant_chunks(
        self, 
        query: str, 
        course_id: int, 
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks for a query.
        
        Args:
            query: The query to retrieve chunks for.
            course_id: ID of the course to search in.
            top_k: Number of chunks to retrieve.
            
        Returns:
            List[Dict[str, Any]]: List of relevant chunks.
        """
        if top_k is None:
            top_k = settings.top_k_retrieval
        
        # Try vector search first, fall back to simple text search if it fails
        chunks = []
        
        try:
            # Generate embedding for query
            query_embedding = self.embedding_service.get_embedding(query)
            
            if query_embedding and self._ensure_vector_store():
                # Query the vector store
                filter_dict = {"metadata": {"course_id": course_id}}
                results = self.vector_store.query_vectors(
                    query_vector=query_embedding,
                    top_k=top_k,
                    filter=filter_dict
                )
                
                # Format results from vector store
                for result in results:
                    chunks.append({
                        "content": result.get("metadata", {}).get("content", ""),
                        "page_number": result.get("metadata", {}).get("page_number"),
                        "source": result.get("metadata", {}).get("source", ""),
                        "score": result.get("score", 0.0)
                    })
        except Exception as e:
            print(f"Vector search failed, falling back to text search: {e}")
        
        # If vector search failed or returned no results, use simple text matching
        if not chunks:
            chunks = self._fallback_text_search(query, course_id, top_k)
        
        return chunks
    
    def _fallback_text_search(self, query: str, course_id: int, top_k: int) -> List[Dict[str, Any]]:
        """
        Fallback text search when vector search is unavailable.
        """
        from sqlalchemy.orm import sessionmaker
        from app.core.database import engine
        from app.models.database import Document, DocumentChunk
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            # Get all document chunks for the course
            documents = db.query(Document).filter(Document.course_id == course_id).all()
            document_ids = [doc.id for doc in documents]
            
            if not document_ids:
                return []
            
            # Get chunks and do simple text matching
            chunks = db.query(DocumentChunk).filter(
                DocumentChunk.document_id.in_(document_ids)
            ).all()
            
            # Simple keyword matching
            query_words = query.lower().split()
            scored_chunks = []
            
            for chunk in chunks:
                content = chunk.content.lower()
                score = 0
                
                # Count keyword matches
                for word in query_words:
                    if len(word) > 2:  # Skip very short words
                        score += content.count(word)
                
                if score > 0:
                    scored_chunks.append({
                        "content": chunk.content,
                        "page_number": chunk.page_number,
                        "source": f"Document {chunk.document_id}",
                        "score": score
                    })
            
            # Sort by score and return top results
            scored_chunks.sort(key=lambda x: x["score"], reverse=True)
            return scored_chunks[:top_k]
            
        except Exception as e:
            print(f"Fallback text search failed: {e}")
            return []
        finally:
            db.close()
        
        
        return chunks
    
    def rerank_chunks(
        self, 
        query: str, 
        chunks: List[Dict[str, Any]], 
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Rerank chunks based on relevance to the query.
        
        Args:
            query: The query to rerank against.
            chunks: List of chunks to rerank.
            top_n: Number of results to return after reranking.
            
        Returns:
            List[Dict[str, Any]]: Reranked chunks.
        """
        return self.reranker_service.rerank(query, chunks, top_n)
    
    def generate_answer(
        self, 
        query: str, 
        chunks: List[Dict[str, Any]], 
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Generate an answer based on the query and retrieved chunks.
        
        Args:
            query: The query to answer.
            chunks: The chunks to use for answering.
            chat_history: Optional chat history for follow-up questions.
            
        Returns:
            Dict[str, Any]: The generated answer with citations and confidence.
        """
        return self.llm_service.generate_answer(query, chunks, chat_history)
    
    def process_question(
        self, 
        question: str, 
        course_id: int, 
        db: Session, 
        chat_session_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Process a question through the entire RAG pipeline.
        
        Args:
            question: The question to answer.
            course_id: ID of the course to search in.
            db: Database session.
            chat_session_id: Optional ID of the chat session.
            user_id: Optional ID of the user.
            
        Returns:
            Dict[str, Any]: The answer with citations and metadata.
        """
        # Create or get chat session
        if not chat_session_id and user_id:
            chat_session = ChatSession(
                title=question[:50] + "..." if len(question) > 50 else question,
                user_id=user_id,
                course_id=course_id
            )
            db.add(chat_session)
            db.commit()
            db.refresh(chat_session)
            chat_session_id = chat_session.id
        
        # Get chat history if chat_session_id is provided
        chat_history = []
        if chat_session_id:
            messages = db.query(ChatMessage).filter(
                ChatMessage.chat_session_id == chat_session_id
            ).order_by(ChatMessage.created_at).all()
            
            for msg in messages:
                chat_history.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # Retrieve relevant chunks
        chunks = self.retrieve_relevant_chunks(question, course_id)
        
        if not chunks:
            answer_data = {
                "answer": "I couldn't find any relevant information in the course materials to answer your question.",
                "confidence": 0.0,
                "citations": []
            }
        else:
            # Rerank chunks
            reranked_chunks = self.rerank_chunks(question, chunks)
            
            # Generate answer
            answer_data = self.generate_answer(question, reranked_chunks, chat_history)
        
        # Save question and answer to chat history if chat_session_id is provided
        if chat_session_id:
            # Save user question
            user_message = ChatMessage(
                chat_session_id=chat_session_id,
                role="user",
                content=question
            )
            db.add(user_message)
            db.commit()
            db.refresh(user_message)
            
            # Save assistant answer
            assistant_message = ChatMessage(
                chat_session_id=chat_session_id,
                role="assistant",
                content=answer_data["answer"]
            )
            db.add(assistant_message)
            db.commit()
            db.refresh(assistant_message)
            
            # Save citations
            for citation in answer_data.get("citations", []):
                source = citation.get("source", "")
                page = citation.get("page", None)
                quote = citation.get("quote", "")
                
                # Find the document
                document = db.query(Document).filter(
                    Document.original_filename == source,
                    Document.course_id == course_id
                ).first()
                
                if document:
                    # Find the chunk if page is provided
                    chunk = None
                    if page:
                        chunk = db.query(DocumentChunk).filter(
                            DocumentChunk.document_id == document.id,
                            DocumentChunk.page_number == page
                        ).first()
                    
                    # Create citation
                    db_citation = Citation(
                        message_id=assistant_message.id,
                        document_id=document.id,
                        chunk_id=chunk.id if chunk else None,
                        page_number=page,
                        quote=quote,
                        relevance_score=citation.get("relevance_score", None)
                    )
                    db.add(db_citation)
            
            db.commit()
            
            # Add chat_session_id to response
            answer_data["chat_session_id"] = chat_session_id
        
        return answer_data
