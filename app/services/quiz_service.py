"""
Quiz Generation Service

This service generates quizzes (MCQs and True/False) based on document content.
"""

from typing import List, Dict, Any, Optional
from app.services.llm_service import LLMService
from app.models.database import Document, DocumentChunk
from sqlalchemy.orm import Session
import json
import random


class QuizService:
    """Service for generating quizzes from document content."""
    
    def __init__(self):
        self.llm_service = LLMService()
        # Initialize the LLM service
        if not self.llm_service.initialize():
            raise Exception("Failed to initialize LLM service for quiz generation")
    
    def generate_quiz(
        self, 
        document_id: int, 
        db: Session,
        num_questions: int = 10,
        question_types: List[str] = ["mcq", "true_false"]
    ) -> Dict[str, Any]:
        """
        Generate a quiz based on document content.
        
        Args:
            document_id: ID of the document to generate quiz from
            db: Database session
            num_questions: Number of questions to generate (default: 10)
            question_types: Types of questions to generate (mcq, true_false)
            
        Returns:
            Dict containing quiz questions and metadata
        """
        # Get document and its chunks
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"Document with ID {document_id} not found")
        
        # Get document chunks for content
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).all()
        
        if not chunks:
            raise ValueError(f"No content found for document {document.original_filename}")
        
        # Combine chunk content for quiz generation
        content_text = "\n\n".join([chunk.content for chunk in chunks[:10]])  # Use first 10 chunks
        
        # Generate quiz questions
        quiz_data = self._generate_quiz_questions(
            content_text, 
            document.original_filename,
            num_questions,
            question_types
        )
        
        return {
            "document_id": document_id,
            "document_name": document.original_filename,
            "quiz_data": quiz_data,
            "total_questions": len(quiz_data.get("questions", [])),
            "question_types": question_types
        }
    
    def _generate_quiz_questions(
        self, 
        content: str, 
        document_name: str,
        num_questions: int,
        question_types: List[str]
    ) -> Dict[str, Any]:
        """Generate quiz questions using LLM."""
        
        # Calculate how many of each type
        num_mcq = num_questions // 2 if "mcq" in question_types else 0
        num_tf = num_questions - num_mcq if "true_false" in question_types else 0
        
        # If only one type requested, allocate all questions to that type
        if len(question_types) == 1:
            if "mcq" in question_types:
                num_mcq = num_questions
                num_tf = 0
            else:
                num_tf = num_questions
                num_mcq = 0
        
        prompt = f"""
You are an expert quiz creator. Create {num_questions} educational quiz questions based on the document content below.

DOCUMENT: {document_name}
CONTENT:
{content[:4000]}

INSTRUCTIONS:
1. Create {num_mcq} Multiple Choice Questions (4 options each, A-D format)
2. Create {num_tf} True/False Questions
3. Focus on KEY CONCEPTS, FACTS, and IMPORTANT DETAILS from the document
4. Make questions test comprehension, not just memorization
5. Ensure MCQ distractors are plausible but clearly wrong
6. Write clear, specific questions that reference the document content

EXAMPLE GOOD QUESTIONS:
- "What is the primary purpose of SeaWulf according to the document?"
- "How many CPU compute nodes does SeaWulf have?"
- "What command is used to connect to SeaWulf?"

AVOID:
- Generic questions like "This document contains..."
- Questions not based on document content
- Ambiguous or unclear questions

OUTPUT FORMAT (JSON only, no extra text):
{{
    "questions": [
        {{
            "id": 1,
            "type": "mcq",
            "question": "What is the primary purpose of SeaWulf?",
            "options": [
                "A) Student course management",
                "B) High Performance Computing for research",
                "C) Library catalog system", 
                "D) Email server for faculty"
            ],
            "correct_answer": "B",
            "explanation": "The document clearly states that SeaWulf is an HPC cluster dedicated to research applications for Stony Brook faculty, staff, and students."
        }},
        {{
            "id": 2,
            "type": "true_false",
            "question": "SeaWulf has exactly 362 CPU compute nodes.",
            "correct_answer": "True",
            "explanation": "The document specifies that SeaWulf has 362 CPU compute nodes where computational work is performed."
        }}
    ]
}}"""
        
        try:
            # Use LLM to generate quiz
            response = self.llm_service.llm.invoke(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Try to parse JSON response
            try:
                # Extract JSON from response (in case there's extra text)
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                json_text = response_text[json_start:json_end]
                
                print(f"🔍 LLM Response: {response_text[:500]}...")
                print(f"🔍 Extracted JSON: {json_text[:500]}...")
                
                quiz_data = json.loads(json_text)
                
                # Validate and clean up the quiz data
                validated_quiz = self._validate_and_clean_quiz(quiz_data, num_questions)
                print(f"✅ Generated {len(validated_quiz['questions'])} valid questions")
                return validated_quiz
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing failed: {e}")
                print(f"❌ Raw response: {response_text}")
                # If JSON parsing fails, create a fallback quiz
                return self._create_fallback_quiz(content, document_name, num_questions)
                
        except Exception as e:
            print(f"Error generating quiz: {e}")
            return self._create_fallback_quiz(content, document_name, num_questions)
    
    def _validate_and_clean_quiz(self, quiz_data: Dict, expected_questions: int) -> Dict[str, Any]:
        """Validate and clean quiz data from LLM."""
        questions = quiz_data.get("questions", [])
        
        # Ensure we have the right number of questions
        if len(questions) > expected_questions:
            questions = questions[:expected_questions]
        
        # Clean and validate each question
        cleaned_questions = []
        for i, q in enumerate(questions):
            cleaned_q = {
                "id": i + 1,
                "type": q.get("type", "mcq"),
                "question": q.get("question", "").strip(),
                "correct_answer": q.get("correct_answer", "").strip(),
                "explanation": q.get("explanation", "").strip()
            }
            
            if cleaned_q["type"] == "mcq":
                options = q.get("options", [])
                if len(options) >= 4:
                    cleaned_q["options"] = options[:4]  # Ensure exactly 4 options
                else:
                    # Skip invalid MCQ questions
                    continue
            
            if cleaned_q["question"] and cleaned_q["correct_answer"]:
                cleaned_questions.append(cleaned_q)
        
        return {"questions": cleaned_questions}
    
    def _create_fallback_quiz(self, content: str, document_name: str, num_questions: int) -> Dict[str, Any]:
        """Create a better fallback quiz if LLM generation fails."""
        questions = []
        
        # Extract meaningful sentences and create better questions
        sentences = [s.strip() for s in content.split('.') if len(s.strip()) > 30]
        
        # Create questions based on content analysis
        for i, sentence in enumerate(sentences[:num_questions]):
            if sentence:
                # Try to create a more meaningful question
                if "SeaWulf" in sentence:
                    questions.append({
                        "id": i + 1,
                        "type": "true_false",
                        "question": f"According to the document: {sentence}",
                        "correct_answer": "True",
                        "explanation": f"This information is directly stated in the document {document_name}."
                    })
                elif any(keyword in sentence.lower() for keyword in ['cpu', 'gpu', 'node', 'cluster', 'research']):
                    questions.append({
                        "id": i + 1,
                        "type": "true_false", 
                        "question": f"The document mentions: {sentence}",
                        "correct_answer": "True",
                        "explanation": f"This technical detail is provided in {document_name}."
                    })
                else:
                    questions.append({
                        "id": i + 1,
                        "type": "true_false",
                        "question": f"Based on {document_name}: {sentence}",
                        "correct_answer": "True",
                        "explanation": f"This statement is found in the document content."
                    })
        
        # If we still need more questions, create some generic but better ones
        while len(questions) < num_questions:
            questions.append({
                "id": len(questions) + 1,
                "type": "true_false",
                "question": f"The document '{document_name}' provides technical information about computing resources.",
                "correct_answer": "True",
                "explanation": "Based on the document content, it contains technical information."
            })
        
        print(f"⚠️ Using fallback quiz generation - created {len(questions)} questions")
        return {"questions": questions[:num_questions]}
