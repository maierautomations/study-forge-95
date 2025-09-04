# StudyRAG API

FastAPI backend for StudyRAG - RAG-Chat with Citations & Quiz Generation for Students.

## 🏗️ Tech Stack

- **FastAPI** - Modern, fast web framework for Python APIs
- **asyncpg** - High-performance PostgreSQL driver  
- **Supabase** - Backend-as-a-Service (Auth, Database, Storage)
- **OpenAI** - Embeddings and LLM for RAG
- **pgvector** - Vector similarity search in PostgreSQL

## 📋 Prerequisites

- Python 3.11+
- Poetry (package manager)
- PostgreSQL with pgvector extension
- Supabase project (configured with schema)
- OpenAI API key

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
cd apps/api
poetry install
```

### 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your actual values
# - DATABASE_URL: Your PostgreSQL connection string
# - SUPABASE_URL and keys from your Supabase dashboard  
# - OPENAI_API_KEY: Your OpenAI API key
```

### 3. Database Schema

**IMPORTANT**: Before starting the API, ensure the database schema is set up:

1. Execute the SQL from `../../supabase/migrations/_proposed_fix.sql` in your Supabase SQL Editor
2. Verify that `chunks` and `embeddings` tables exist with indexes

### 4. Start Development Server

```bash
# Activate virtual environment and start server
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs (Swagger UI)
- **Health**: http://localhost:8000/health

### 5. Verify Setup

```bash
# Test health endpoint
curl http://localhost:8000/health

# Should return:
# {
#   "status": "healthy",
#   "version": "0.1.0", 
#   "checks": {
#     "database": {"status": "healthy", ...}
#   }
# }
```

## 📁 Project Structure

```
apps/api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── core/
│   │   ├── config.py        # Settings (Pydantic)
│   │   └── auth.py          # JWT/Supabase auth
│   ├── db/
│   │   └── session.py       # Database connections
│   └── api/
│       └── health.py        # Health check endpoints
├── pyproject.toml           # Dependencies & config
├── .env.example            # Environment template
└── README.md               # This file
```

## 🔧 Configuration

Key environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection | `postgresql://user:pass@host:5432/db` |
| `SUPABASE_URL` | Supabase project URL | `https://abc123.supabase.co` |
| `SUPABASE_ANON_KEY` | Public Supabase key | `eyJ...` |
| `SUPABASE_SERVICE_ROLE_KEY` | Private Supabase key | `eyJ...` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `ALLOWED_ORIGINS` | CORS origins | `http://localhost:3000` |

## 🧪 Development

### Code Quality Tools

```bash
# Format code
poetry run black .
poetry run isort .

# Type checking  
poetry run mypy app/

# Linting
poetry run ruff check .

# Run all checks
poetry run black . && poetry run isort . && poetry run mypy app/ && poetry run ruff check .
```

### Testing

```bash
# Run tests (when implemented)
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=app tests/
```

## 📊 API Endpoints

### Current (P0 - Health Check)

- `GET /` - API info
- `GET /health` - Health check with dependency status
- `GET /ping` - Simple ping/pong

### Planned (P1-P5)

- `POST /docs/ingest` - Start document ingestion  
- `GET /docs/status` - Check ingestion progress
- `POST /rag/query` - RAG query with citations
- `POST /quiz/generate` - Generate quiz from document
- `POST /quiz/submit` - Submit quiz answers

## 🐛 Troubleshooting

### Common Issues

1. **Database connection fails**
   ```bash
   # Check DATABASE_URL format
   # Ensure PostgreSQL is running
   # Verify network connectivity
   ```

2. **Missing tables error**
   ```bash
   # Execute schema migration:
   # Run SQL from ../../supabase/migrations/_proposed_fix.sql
   ```

3. **CORS errors in frontend**
   ```bash
   # Add frontend URL to ALLOWED_ORIGINS in .env
   ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
   ```

4. **Import errors**
   ```bash
   # Ensure you're in the poetry environment
   poetry shell
   
   # Or run commands with poetry
   poetry run python -m app.main
   ```

### Health Check Debug

```bash
# Detailed health check
curl http://localhost:8000/health | jq .

# Check specific components
curl http://localhost:8000/health | jq '.checks.database'
```

## 📈 Next Steps

1. **P1**: Implement schema validation endpoints
2. **P2**: Add document/RAG/quiz API endpoints (dummy responses)
3. **P3**: Implement document ingestion pipeline  
4. **P4**: Add hybrid search (BM25 + vector)
5. **P5**: Complete quiz generation engine

## 🤝 Development Workflow

1. Create feature branch from `main`
2. Make changes and test locally
3. Run code quality checks
4. Test with frontend integration  
5. Create pull request

## 📝 Logging

Structured JSON logs with:
- Request tracing
- Performance metrics
- Error details (no PII)
- Database query stats

Example log entry:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO", 
  "event": "rag_query_completed",
  "trace_id": "abc-123",
  "document_id": "doc-456", 
  "latency_ms": 1250,
  "chunks_retrieved": 8
}
```