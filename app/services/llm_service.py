from typing import List, Dict, Any, Optional
import json
from openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from app.config.settings import settings


class LLMService:
    """
    Service for generating answers using Large Language Models.
    Supports OpenAI and Anthropic models through LangChain.
    """
    
    def __init__(self):
        """Initialize the LLM service."""
        self.provider = settings.llm_provider
        self.model_name = settings.llm_model
        self.client = None
        self.llm = None
        self.initialized = False
    
    def initialize(self) -> bool:
        """
        Initialize the LLM.
        
        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        try:
            if self.provider == "openai":
                self.client = OpenAI(api_key=settings.openai_api_key)
                self.llm = ChatOpenAI(
                    model_name=self.model_name,
                    temperature=0.1,
                    openai_api_key=settings.openai_api_key
                )
            elif self.provider == "anthropic":
                # For Anthropic, we use LangChain's integration
                from langchain_anthropic import ChatAnthropic
                self.llm = ChatAnthropic(
                    model_name=self.model_name,
                    temperature=0.1,
                    anthropic_api_key=settings.anthropic_api_key
                )
            else:
                print(f"Unsupported LLM provider: {self.provider}")
                return False
            
            self.initialized = True
            return True
        except Exception as e:
            print(f"Error initializing LLM: {e}")
            return False
    
    def generate_answer(
        self, 
        question: str, 
        context: List[Dict[str, Any]], 
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Generate an answer to a question based on the provided context.
        
        Args:
            question: The question to answer.
            context: The context to use for answering the question.
            chat_history: Optional chat history for follow-up questions.
            
        Returns:
            Dict[str, Any]: The generated answer with citations and confidence.
        """
        if not self.initialized:
            print("🔧 LLM not initialized, attempting initialization...")
            if not self.initialize():
                print("❌ LLM initialization failed")
                return {
                    "answer": "I'm sorry, but I couldn't generate an answer at this time.",
                    "confidence": 0.0,
                    "citations": []
                }
            else:
                print("✅ LLM initialized successfully")
        
        try:
            print(f"🤖 Generating answer for question: {question[:50]}...")
            print(f"📄 Context chunks received: {len(context)}")
            
            # Format the context for the prompt
            formatted_context = ""
            for i, ctx in enumerate(context):
                content = ctx["content"]
                # Handle different context formats
                if "metadata" in ctx:
                    source = ctx["metadata"].get("source", "Unknown")
                    page_number = ctx["metadata"].get("page_number", "Unknown")
                else:
                    # Fallback for simple context format
                    source = ctx.get("source", "Unknown")
                    page_number = ctx.get("page_number", "Unknown")
                formatted_context += f"[{i+1}] Source: {source}, Page: {page_number}\n{content}\n\n"
                print(f"  - Chunk {i+1}: {len(content)} chars from {source}")
            
            if not formatted_context.strip():
                print("❌ No context available for answer generation")
                return {
                    "answer": "I don't have enough information to answer this question based on the provided course materials.",
                    "confidence": 0.0,
                    "citations": []
                }
            
            # Format chat history if provided
            formatted_history = ""
            if chat_history and len(chat_history) > 0:
                for msg in chat_history:
                    role = msg.get("role", "")
                    content = msg.get("content", "")
                    if role == "user":
                        formatted_history += f"User: {content}\n"
                    elif role == "assistant":
                        formatted_history += f"Assistant: {content}\n"
            
            # Create the prompt - simplified to avoid JSON parsing issues
            prompt_template = """You are a helpful AI assistant that answers questions based on provided course notes and educational materials. 

CONTEXT:
{context}

{chat_history}

QUESTION: {question}

INSTRUCTIONS:
Answer the question based ONLY on the information in the CONTEXT. If the answer is not in the context, say "I don't have enough information to answer this question based on the provided course materials."

ANSWER:"""
            
            prompt = PromptTemplate(
                template=prompt_template,
                input_variables=["context", "question", "chat_history"]
            )
            
            # Create the chain using the new LangChain syntax
            chain = prompt | self.llm
            
            # Run the chain using invoke
            result = chain.invoke({
                "context": formatted_context,
                "question": question,
                "chat_history": formatted_history
            })
            
            # Extract content from the result (ChatOpenAI returns AIMessage object)
            answer_text = result.content if hasattr(result, 'content') else str(result)
            
            print(f"✅ LLM response received: {len(answer_text)} characters")
            
            # Check if the AI says it doesn't have enough information
            no_info_phrases = [
                "I don't have enough information",
                "I couldn't find any relevant information",
                "I cannot answer this question",
                "not enough information",
                "no relevant information",
                "cannot be answered based on",
                "not available in the provided"
            ]
            
            has_no_info = any(phrase.lower() in answer_text.lower() for phrase in no_info_phrases)
            
            # Create citations from the context chunks used (only if AI provided useful information)
            citations = []
            from datetime import datetime
            total_relevance = 0
            max_possible_score = 0
            
            # Only create citations if the AI provided useful information (not a "no info" response)
            if context and not has_no_info:
                chunk = context[0]  # Take only the best/first chunk
                # Normalize relevance score (fallback text search can give high scores like 2.0)
                raw_score = chunk.get("score", 0.0)
                # For text search scores > 1.0, normalize to 0-1 range
                normalized_score = min(raw_score / 5.0, 1.0) if raw_score > 1.0 else raw_score
                
                doc_id = chunk.get("document_id", 0)
                doc_name = chunk.get("document_name", f"Document {doc_id}")
                print(f"🔍 Using chunk document_name: {doc_name} (ID: {doc_id})")
                citation = {
                    "id": 1,  # Only one citation
                    "message_id": 0,  # Will be set by the calling function if needed
                    "document_id": doc_id,
                    "document_name": doc_name,
                    "page_number": chunk.get("page_number"),
                    "quote": chunk.get("content", "")[:150] + "..." if len(chunk.get("content", "")) > 150 else chunk.get("content", ""),
                    "relevance_score": round(normalized_score, 2),
                    "chunk_id": None,
                    "created_at": datetime.now()
                }
                citations.append(citation)
                total_relevance = normalized_score
                max_possible_score = 1.0
            elif has_no_info:
                print("🚫 No citations created - AI indicated insufficient information")
            
            # Calculate dynamic confidence based on:
            # 1. Average relevance score of retrieved chunks
            # 2. Number of chunks found (more chunks = higher confidence)
            # 3. Quality of the best match
            # 4. Whether AI indicated insufficient information
            if has_no_info:
                # If AI says no info, confidence should be very low
                confidence = 0.1
            elif len(context) > 0 and citations:
                avg_relevance = total_relevance / len(context)
                chunk_count_factor = min(len(context) / 5.0, 1.0)  # Normalize to 0-1
                best_match_score = max([c.get("score", 0.0) for c in context])
                best_match_normalized = min(best_match_score / 5.0, 1.0) if best_match_score > 1.0 else best_match_score
                
                # Weighted confidence calculation
                confidence = (avg_relevance * 0.5) + (chunk_count_factor * 0.3) + (best_match_normalized * 0.2)
                confidence = max(0.1, min(0.95, confidence))  # Keep between 10% and 95%
            else:
                confidence = 0.1
            
            # Return response with proper citations and dynamic confidence
            return {
                "answer": answer_text.strip(),
                "confidence": round(confidence, 2),
                "citations": citations
            }
        
        except Exception as e:
            import traceback
            print(f"Error generating answer: {e}")
            print(f"LLM error traceback: {traceback.format_exc()}")
            return {
                "answer": "I'm sorry, but I couldn't generate an answer at this time.",
                "confidence": 0.0,
                "citations": []
            }
