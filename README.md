# 📚 StudyMate AI - AI-Powered Learning Assistant

A comprehensive web application that allows users to upload course notes (PDFs, slides, documents), ask questions about them, and generate interactive quizzes. The application uses Retrieval-Augmented Generation (RAG) to provide accurate answers with citations to the source material, and leverages LLM technology to create educational quizzes based on document content.

StudyMate AI is designed for students, researchers, teaching assistants, and instructors who want to quickly find information in their course materials and create assessment tools without having to manually search through multiple documents.

## 🚀 Latest Features (v3.0)

### 🔐 **NEW: Modern OAuth Authentication**
- **Social Login Integration**: Login with Google and GitHub OAuth
- **Professional UI**: ChatGPT-style login interface with modern design
- **Enhanced Security**: JWT-based authentication with OAuth provider integration
- **Streamlined Registration**: Clean registration flow with password validation
- **User-Friendly Experience**: Simplified authentication process

### 🗑️ **NEW: Course & Document Management**
- **Delete Course Functionality**: Remove courses with confirmation dialog
- **Delete Document Support**: Remove individual documents from courses
- **Vector Store Cleanup**: Automatic cleanup of embeddings when content is deleted
- **Data Isolation**: Proper user data separation and privacy protection
- **Bulk Operations**: Efficient deletion of related data and files

### 📄 **Smart Citation System**
- **Intelligent Citation Logic**: Citations only appear when AI provides useful information
- **No False Citations**: No citations shown for "insufficient information" responses
- **Accurate Document Names**: Citations display actual filenames (e.g., "studyguide.pdf")
- **Confidence-Based Display**: Citation visibility based on answer confidence
- **Clean Presentation**: Streamlined citation format with document name and page

### 🎯 **Interactive Quiz Generation**
- **LLM-Powered Creation**: Generate high-quality Multiple Choice and True/False questions
- **Document-Based Content**: Questions generated from actual uploaded content
- **Interactive Interface**: Take quizzes with immediate scoring and explanations
- **Flexible Settings**: Configure 5-20 questions with customizable question types
- **Educational Focus**: Questions test comprehension and understanding

### 🔧 **System & Performance Improvements**
- **Enhanced Data Isolation**: Fixed cross-user data contamination issues
- **Vector Store Management**: Proper cleanup of embeddings on deletion
- **Improved Error Handling**: Better logging and error recovery
- **Modern UI/UX**: Enhanced navigation and user feedback
- **Database Optimization**: Improved schema and query performance

## Core Features

### 🔐 **Authentication & Security**
- **OAuth Integration**: Login with Google and GitHub
- **Email Registration**: Traditional email/password authentication
- **JWT Security**: Secure token-based authentication
- **Data Isolation**: User data properly separated and protected
- **Modern UI**: ChatGPT-style login interface

### 📚 **Document Management**
- **Multi-Format Support**: Upload PDF, DOCX, PPTX, and more
- **Automatic Processing**: Intelligent document chunking and indexing
- **Course Organization**: Organize documents by course/subject
- **Delete Operations**: Remove documents and courses with proper cleanup
- **Real-time Status**: Processing progress and status tracking

### 💬 **Intelligent Q&A System**
- **Natural Language Queries**: Ask questions in plain English
- **Smart Citations**: Citations only shown for useful answers
- **Accurate Sources**: Display actual document names and page numbers
- **Chat History**: Context-aware follow-up questions
- **Confidence Scoring**: Reliability indicators for answers

### 🎯 **Interactive Quiz Generation**
- **AI-Powered Creation**: Generate MCQ and True/False questions
- **Document-Based**: Questions derived from uploaded content
- **Interactive Interface**: Take quizzes with immediate feedback
- **Flexible Configuration**: 5-20 questions, customizable types
- **Educational Quality**: Focus on comprehension and learning

### 🔍 **Advanced Search & Retrieval**
- **Semantic Search**: State-of-the-art embedding-based search
- **Hybrid Approach**: Vector similarity + text matching
- **Smart Reranking**: Improved result relevance
- **Context Awareness**: Better understanding of user intent

### 🗑️ **Data Management**
- **Course Deletion**: Remove entire courses with confirmation
- **Document Removal**: Delete individual files and documents
- **Vector Cleanup**: Automatic embedding cleanup on deletion
- **Data Integrity**: Consistent data state across all systems

## Tech Stack

### 🖥️ **Core Framework**
- **Frontend**: Streamlit with interactive components and modern UI
- **Backend API**: FastAPI with async support and comprehensive routing
- **Database**: SQLAlchemy with SQLite (production-ready for PostgreSQL)
- **Authentication**: JWT + OAuth (Google, GitHub) with secure token management

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
   - **Optional**: Add OAuth credentials (Google, GitHub) for social login
5. Set up OAuth (Optional):
   - See `OAUTH_SETUP.md` for detailed OAuth configuration
   - Configure Google and GitHub OAuth applications
   - Add client IDs and secrets to `.env` file
6. Initialize the database:
   ```
   python init_db.py
   ```
7. Run the application:
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
│   │       ├── oauth.py     # 🆕 OAuth endpoints (Google, GitHub)
│   │       ├── courses.py   # Course management (with delete)
│   │       ├── documents.py # Document upload/management (with delete)
│   │       ├── questions.py # Q&A endpoints
│   │       ├── quiz.py      # Quiz generation endpoints
│   │       ├── admin.py     # Admin functionality
│   │       └── debug.py     # 🆕 Debug endpoints for vector store
│   ├── core/         # Core application logic
│   │   ├── database.py      # Database configuration
│   │   ├── auth.py          # Authentication logic
│   │   └── rag_pipeline.py  # Enhanced RAG pipeline
│   ├── models/       # Data models
│   │   ├── database.py      # SQLAlchemy models
│   │   └── schemas.py       # Pydantic schemas (enhanced with quiz models)
│   ├── services/     # External service integrations
│   │   ├── llm_service.py   # LLM integration (enhanced citations)
│   │   ├── quiz_service.py  # Quiz generation service
│   │   ├── oauth_service.py # 🆕 OAuth service (Google, GitHub)
│   │   ├── vector_store.py  # 🆕 Vector store with cleanup
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
├── .env.example     # Example environment variables (updated)
├── requirements.txt # Dependencies
├── run_app.py       # Unified application launcher
├── init_db.py       # 🆕 Database initialization script
├── clear_vector_store.py # 🆕 Vector store cleanup utility
├── test_vector_cleanup.py # 🆕 Vector cleanup test script
├── OAUTH_SETUP.md   # 🆕 OAuth setup guide
├── GOOGLE_OAUTH_SETUP.md # 🆕 Google OAuth detailed guide
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

### Version 3.0 (Latest - December 2024)
- ✅ **OAuth Authentication System**
  - Google and GitHub OAuth integration
  - ChatGPT-style login interface
  - Enhanced security with JWT + OAuth
  - Streamlined user registration and login

- ✅ **Course & Document Management**
  - Delete course functionality with confirmation dialog
  - Delete individual documents from courses
  - Automatic vector store cleanup on deletion
  - Enhanced data isolation and privacy protection

- ✅ **Smart Citation System**
  - Citations only shown for useful AI responses
  - No citations for "insufficient information" responses
  - Improved citation logic and confidence scoring
  - Better user experience with accurate citations

- ✅ **Vector Store Management**
  - Fixed cross-user data contamination issues
  - Proper cleanup of embeddings on deletion
  - Enhanced vector store operations
  - Debug tools for vector store monitoring

- ✅ **System Enhancements**
  - Improved error handling and logging
  - Enhanced UI/UX with modern design
  - Better database schema and performance
  - Comprehensive testing and debugging tools

### Version 2.0 (Previous)
- ✅ **Interactive Quiz Generation System**
- ✅ **Enhanced Citation System** 
- ✅ **System Improvements**
- ✅ **Backend Enhancements**

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
