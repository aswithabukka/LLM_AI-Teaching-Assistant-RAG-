# Deployment Guide for Course Notes Q&A

This guide provides instructions for deploying the Course Notes Q&A application in different environments.

## Prerequisites

- Python 3.8+
- Docker and Docker Compose (for containerized deployment)
- API keys for:
  - OpenAI
  - Pinecone
  - Cohere (optional, for reranking)

## Local Development Deployment

### 1. Clone the repository

```bash
git clone <repository-url>
cd course-notes-qa
```

### 2. Set up environment variables

Copy the example environment file and fill in your API keys:

```bash
cp .env.example .env
```

Edit the `.env` file with your API keys and configuration.

### 3. Create a virtual environment and install dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Run the application

```bash
python run.py
```

This will start both the FastAPI backend and Streamlit frontend.

- Backend API: http://localhost:8000
- Frontend UI: http://localhost:8501
- Admin Dashboard: http://localhost:8501/admin_dashboard.py

## Docker Deployment

### 1. Build and run with Docker Compose

```bash
docker-compose up -d
```

This will:
- Build the Docker image
- Start the PostgreSQL database
- Start the application container
- Mount the data directory for persistence

### 2. Access the application

- Backend API: http://localhost:8000
- Frontend UI: http://localhost:8501
- Admin Dashboard: http://localhost:8501/admin_dashboard.py

## Cloud Deployment Options

### Railway

1. Create a new project in Railway
2. Connect your GitHub repository
3. Add the required environment variables
4. Deploy the application

### Fly.io

1. Install the Fly CLI
2. Initialize the project:
   ```bash
   fly launch
   ```
3. Add the required environment variables:
   ```bash
   fly secrets set OPENAI_API_KEY=your_openai_api_key
   fly secrets set PINECONE_API_KEY=your_pinecone_api_key
   fly secrets set PINECONE_ENVIRONMENT=your_pinecone_environment
   ```
4. Deploy the application:
   ```bash
   fly deploy
   ```

### Render

1. Create a new Web Service in Render
2. Connect your GitHub repository
3. Set the build command: `pip install -r requirements.txt`
4. Set the start command: `python run.py`
5. Add the required environment variables
6. Deploy the application

## Database Migration

If you need to switch from SQLite to PostgreSQL:

1. Update the `DATABASE_URL` in your `.env` file:
   ```
   DATABASE_URL=postgresql://username:password@localhost:5432/course_notes_qa
   ```

2. Run the database migration:
   ```bash
   alembic revision --autogenerate -m "Initial migration"
   alembic upgrade head
   ```

## Scaling Considerations

- For production deployments, consider using a managed PostgreSQL database
- For high traffic, consider using a load balancer and multiple application instances
- For large document collections, consider upgrading your Pinecone plan
- Monitor API usage to avoid exceeding rate limits

## Monitoring and Maintenance

- Use the Admin Dashboard to monitor system performance
- Regularly evaluate the RAG pipeline performance
- Keep dependencies updated
- Monitor API usage and costs
