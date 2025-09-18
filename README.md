# Course Notes Q&A - AI Teaching Assistant with RAG

A web application that allows users to upload course notes (PDFs, slides, documents) and ask questions about them. The application uses Retrieval-Augmented Generation (RAG) to provide accurate answers with citations to the source material.

This application is designed for students, researchers, teaching assistants, and instructors who want to quickly find information in their course materials without having to manually search through multiple documents.

## 🚀 Latest Features

- **Ultra-fast Processing**: Optimized processing for small files (<15KB) with instant text extraction
- **Enhanced Table Extraction**: Improved DOCX processing to extract data from tables and structured content
- **Cancel Processing**: Ability to cancel document processing operations
- **Robust Error Handling**: Comprehensive logging and error recovery
- **Streamlined Authentication**: JWT-based authentication with simplified token validation

## Features

- Upload and manage course notes in various formats (PDF, DOCX, etc.)
- Ask questions about the content of your notes
- Get answers with citations to the source material
- View source material inline
- Support for follow-up questions (chat history aware)
- Admin features to re-index on new uploads and monitor quality

## Tech Stack

- **Frontend**: Streamlit
- **Backend API**: FastAPI
- **Embeddings**: OpenAI text-embedding-3-large
- **Vector Database**: Pinecone
- **LLM for Generation**: GPT-4o-mini / Claude 3.5 Sonnet
- **Retrieval/RAG Framework**: LangChain
- **Reranker**: Cohere Rerank v3
- **Parsing/Chunking**: pymupdf, unstructured, pypandoc
- **Storage**: Local file system (can be extended to S3)
- **Authentication**: Simple email-based authentication
- **Evaluation**: RAGAS, custom evaluation sets

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
│   ├── core/         # Core application logic
│   ├── models/       # Data models
│   ├── services/     # External service integrations
│   ├── utils/        # Utility functions
│   ├── config/       # Configuration
│   └── frontend/     # Streamlit frontend
│       ├── components/ # UI components
│       ├── pages/    # Streamlit pages
│       └── static/   # Static assets
├── data/
│   ├── uploads/      # Uploaded files
│   ├── processed/    # Processed files
│   └── temp/         # Temporary files
├── scripts/         # Utility scripts
├── tests/           # Unit and integration tests
├── .env             # Environment variables
├── .env.example     # Example environment variables
├── requirements.txt # Dependencies
├── Dockerfile       # Docker configuration
├── docker-compose.yml # Docker Compose configuration
├── DEPLOYMENT.md    # Deployment guide
├── start.sh         # Startup script
└── README.md        # This file
```

## Usage Instructions

### User Interface

1. **Login/Register**: Start by creating an account or logging in
2. **Create a Course**: Create a new course to organize your notes
3. **Upload Documents**: Upload PDF, DOCX, or PPTX files to your course
4. **Ask Questions**: Ask questions about your course materials
5. **View Answers**: Get answers with citations to the source material
6. **Follow-up Questions**: Continue the conversation with follow-up questions

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

## Success Criteria

- Answer groundedness: ≥85% of answers include at least one correct citation
- Latency (p95): ≤3s for short questions, ≤6s for long context
- RAG quality (RAGAS): Faithfulness ≥0.8, Answer Relevance ≥0.8
- Hallucination rate: <10% (manual eval set of 50 Qs)
