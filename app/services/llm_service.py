from typing import List, Dict, Any, Optional
import json
from openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
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
            
            # Create the chain
            chain = LLMChain(llm=self.llm, prompt=prompt)
            
            # Run the chain
            result = chain.run(
                context=formatted_context,
                question=question,
                chat_history=formatted_history
            )
            
            print(f"✅ LLM response received: {len(result)} characters")
            
            # Return simplified response format (no JSON parsing needed)
            return {
                "answer": result.strip(),
                "confidence": 0.8,
                "citations": []
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
