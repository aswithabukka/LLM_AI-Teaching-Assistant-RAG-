# Course Notes Q&A - AI Teaching Assistant with RAG

A comprehensive web application that allows users to upload course notes (PDFs, slides, documents), ask questions about them, and generate interactive quizzes. The application uses Retrieval-Augmented Generation (RAG) to provide accurate answers with citations to the source material, and leverages LLM technology to create educational quizzes based on document content.

This application is designed for students, researchers, teaching assistants, and instructors who want to quickly find information in their course materials and create assessment tools without having to manually search through multiple documents.

## 🚀 Latest Features (v2.0)

### 🎯 **NEW: Interactive Quiz Generation System**
- **LLM-Powered Quiz Creation**: Generate high-quality Multiple Choice and True/False questions from uploaded documents
- **Intelligent Question Generation**: Uses advanced prompts to create meaningful, educational questions that test comprehension
- **Interactive Quiz Interface**: Take quizzes with immediate scoring, answer explanations, and performance tracking
- **Flexible Quiz Settings**: Configure number of questions (5-20) and question types (MCQ, True/False, or both)
- **Document-Based Content**: Questions are generated from actual document content, ensuring relevance and accuracy

### 📄 **Enhanced Citation System**
- **Accurate Document Names**: Citations now display actual filenames (e.g., "bigdatanotes.pdf") instead of generic IDs
- **Single Best Citation**: Streamlined to show only the most relevant source per answer to reduce clutter
- **Improved Metadata Storage**: Document names stored in vector database for consistent retrieval
- **Better Citation Display**: Clean, user-friendly citation format with document name and page number

### 🔧 **System Improvements**
- **Ultra-fast Processing**: Optimized processing for small files (<15KB) with instant text extraction
- **Enhanced Table Extraction**: Improved DOCX processing to extract data from tables and structured content
- **Robust Error Handling**: Comprehensive logging and error recovery throughout the application
- **Streamlined Authentication**: JWT-based authentication with simplified token validation
- **Improved UI/UX**: Better navigation, course name display, and user feedback

## Core Features

### 📚 **Document Management**
- Upload and manage course notes in various formats (PDF, DOCX, PPTX, etc.)
- Automatic document processing and chunking for optimal retrieval
- Course-based organization of documents
- Real-time processing status and progress tracking

### 💬 **Intelligent Q&A System**
- Ask questions about the content of your notes using natural language
- Get accurate answers with citations to the source material
- View source material inline with page numbers and document names
- Support for follow-up questions with chat history awareness
- Confidence scoring for answer reliability

### 🎯 **Interactive Quiz Generation**
- Generate educational quizzes from uploaded documents
- Multiple Choice Questions (MCQ) with 4 options each
- True/False questions with detailed explanations
- Configurable quiz settings (5-20 questions, question types)
- Interactive quiz interface with scoring and performance tracking
- LLM-powered question creation for high-quality assessments

### 🔍 **Advanced Search & Retrieval**
- Semantic search using state-of-the-art embeddings
- Hybrid search combining vector similarity and text matching
- Reranking for improved result relevance
- Context-aware retrieval for better answer quality

### 👥 **User Management**
- Simple email-based authentication system
- Course creation and management
- Chat history and session management
- Admin features for system monitoring and quality control

## Tech Stack

### 🖥️ **Core Framework**
- **Frontend**: Streamlit with interactive components
- **Backend API**: FastAPI with async support
- **Database**: SQLAlchemy with SQLite (production-ready for PostgreSQL)
- **Authentication**: JWT-based authentication system

### 🤖 **AI & ML Components**
- **Embeddings**: OpenAI text-embedding-3-large
- **Vector Database**: ChromaDB (local) / Pinecone (cloud)
- **LLM for Q&A**: GPT-4o-mini / Claude 3.5 Sonnet
- **LLM for Quiz Generation**: GPT-4o-mini with specialized prompts
- **Retrieval Framework**: LangChain with custom RAG pipeline
- **Reranking**: Cohere Rerank v3 for improved relevance

### 📄 **Document Processing**
- **PDF Processing**: pymupdf for text and metadata extraction
- **DOCX Processing**: unstructured for table and structure extraction
- **Text Chunking**: Custom chunking with overlap for optimal retrieval
- **Metadata Management**: Enhanced metadata storage with document names

### 🔧 **Infrastructure**
- **Storage**: Local file system (extensible to S3/cloud storage)
- **Caching**: In-memory caching for improved performance
- **Logging**: Comprehensive logging and error tracking
- **Evaluation**: RAGAS metrics and custom evaluation sets

## Setup Instructions

1. Clone this repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Fill in your API keys (OpenAI, Pinecone, Cohere)
5. Initialize the database with a default admin user:
   ```
   python scripts/init_db.py
   ```
6. Run the application:
   ```
   ./start.sh
   ```
   Or run the components separately:
   ```
   # Backend API
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   
   # Frontend UI
   streamlit run app/frontend/app.py
   
   # Admin Dashboard
   streamlit run app/frontend/admin_dashboard.py
   ```

## Project Structure

```
course-notes-qa/
├── app/
│   ├── api/          # FastAPI routes
│   │   └── routes/   # API route modules
│   │       ├── auth.py      # Authentication endpoints
│   │       ├── courses.py   # Course management
│   │       ├── documents.py # Document upload/management
│   │       ├── questions.py # Q&A endpoints
│   │       ├── quiz.py      # 🆕 Quiz generation endpoints
│   │       └── admin.py     # Admin functionality
│   ├── core/         # Core application logic
│   │   ├── database.py      # Database configuration
│   │   ├── auth.py          # Authentication logic
│   │   └── rag_pipeline.py  # Enhanced RAG pipeline
│   ├── models/       # Data models
│   │   ├── database.py      # SQLAlchemy models
│   │   └── schemas.py       # Pydantic schemas (enhanced with quiz models)
│   ├── services/     # External service integrations
│   │   ├── llm_service.py   # LLM integration
│   │   ├── quiz_service.py  # 🆕 Quiz generation service
│   │   └── file_service.py  # File processing
│   ├── utils/        # Utility functions
│   ├── config/       # Configuration
│   └── frontend/     # Streamlit frontend
│       └── app.py    # Main frontend app (enhanced with quiz functionality)
├── data/
│   ├── uploads/      # Uploaded files
│   ├── chromadb/     # ChromaDB vector store
│   └── temp/         # Temporary files
├── scripts/         # Utility scripts
├── tests/           # Unit and integration tests
├── .env             # Environment variables
├── .env.example     # Example environment variables
├── requirements.txt # Dependencies
├── run_app.py       # 🆕 Unified application launcher
├── Dockerfile       # Docker configuration
├── docker-compose.yml # Docker Compose configuration
├── DEPLOYMENT.md    # Deployment guide
└── README.md        # This file
```

## Usage Instructions

### User Interface

#### 📚 **Getting Started**
1. **Login/Register**: Start by creating an account or logging in
2. **Create a Course**: Create a new course to organize your notes
3. **Upload Documents**: Upload PDF, DOCX, or PPTX files to your course
4. **Wait for Processing**: Documents are automatically processed and indexed

#### 💬 **Q&A System**
1. **Navigate to Courses**: Select your course from the sidebar
2. **Ask Questions**: Ask questions about your course materials in natural language
3. **View Answers**: Get accurate answers with citations showing document names and page numbers
4. **Follow-up Questions**: Continue the conversation with context-aware follow-up questions
5. **View Chat History**: Access previous conversations from the Chat History tab

#### 🎯 **Quiz Generation (NEW)**
1. **Navigate to Quiz Tab**: Select "Quiz" from the main navigation
2. **Select Document**: Choose a document from your course to generate quiz from
3. **Configure Quiz Settings**:
   - Set number of questions (5-20)
   - Choose question types (Multiple Choice, True/False, or both)
4. **Generate Quiz**: Click "Generate Quiz" and wait for AI-powered question creation
5. **Take Quiz**: Answer questions using the interactive interface
6. **View Results**: 
   - Calculate your score with the "Calculate Score" button
   - Reveal answers and explanations with "Show Answers"
   - Generate a new quiz with "New Quiz" button

#### 📊 **Quiz Features**
- **Multiple Choice Questions**: 4-option questions with plausible distractors
- **True/False Questions**: Statement-based questions with detailed explanations
- **Immediate Feedback**: See correct answers and explanations
- **Performance Tracking**: Calculate scores and track your understanding
- **Educational Focus**: Questions test comprehension, not just memorization

### Admin Dashboard

The admin dashboard provides tools for monitoring and managing the application:

1. **System Stats**: View system statistics including user count, document count, and vector store stats
2. **User Management**: Manage user accounts and permissions
3. **Evaluation**: Evaluate the RAG pipeline performance using RAGAS metrics
4. **Monitoring**: Monitor system performance, usage, and errors

## Deployment Options

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

### Local Development

```bash
./start.sh
```

### Docker Deployment

```bash
docker-compose up -d
```

### Cloud Deployment

The application can be deployed to various cloud platforms including:
- Railway
- Fly.io
- Render

## Recent Improvements & Changelog

### Version 2.0 (Latest)
- ✅ **Added Interactive Quiz Generation System**
  - LLM-powered question creation with GPT-4o-mini
  - Support for MCQ and True/False questions
  - Interactive quiz interface with scoring
  - Configurable quiz settings and question types

- ✅ **Enhanced Citation System**
  - Fixed document name display in citations
  - Improved metadata storage in vector database
  - Streamlined to single best citation per answer
  - Better citation formatting and display

- ✅ **System Improvements**
  - Enhanced error handling and logging
  - Improved UI/UX with better navigation
  - Fixed Streamlit duplicate key errors
  - Better course name display throughout application

- ✅ **Backend Enhancements**
  - New quiz API endpoints (`/api/quiz/generate`, `/api/quiz/documents`)
  - Enhanced RAG pipeline with document name storage
  - Improved LLM service integration
  - Better schema validation with Pydantic models

## Success Criteria

### 📊 **Q&A System Performance**
- Answer groundedness: ≥85% of answers include at least one correct citation
- Latency (p95): ≤3s for short questions, ≤6s for long context
- RAG quality (RAGAS): Faithfulness ≥0.8, Answer Relevance ≥0.8
- Hallucination rate: <10% (manual eval set of 50 Qs)
- Citation accuracy: ≥95% show correct document names and page numbers

### 🎯 **Quiz System Performance**
- Question quality: ≥90% of generated questions are educationally meaningful
- Content relevance: ≥95% of questions are based on actual document content
- Quiz generation time: ≤30s for 10 questions
- Answer accuracy: ≥95% of correct answers are factually accurate
- User engagement: Interactive interface with immediate feedback
