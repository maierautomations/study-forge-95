# Document Ingestion Pipeline Setup

This document explains how to set up and test the complete document ingestion pipeline for StudyRAG.

## Prerequisites

### 1. Environment Variables

Create a `.env` file in the `apps/api/` directory with the following variables:

```env
# Database Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
DATABASE_URL=postgresql://postgres:your_password@db.your_project.supabase.co:5432/postgres

# OpenAI API Configuration  
OPENAI_API_KEY=your_openai_api_key

# JWT Configuration
JWT_SECRET_KEY=your_jwt_secret_key
JWT_ISSUER=https://your_project.supabase.co/auth/v1

# Application Configuration
DEBUG=true
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

### 2. Database Schema

Ensure your Supabase database has the required tables. Run the migrations:

```bash
# Apply the schema migrations
cd apps/api
# Use Supabase CLI or apply the SQL files in the project root:
# - 0001_init.sql
# - 0002_policies.sql
```

### 3. Dependencies

All Python dependencies should already be installed. If needed:

```bash
cd apps/api
poetry install
```

## Testing the Pipeline

### 1. Run the Test Script

```bash
cd apps/api
python test_ingestion.py
```

This will test:
- ✅ File validation
- ✅ Text extraction (PDF/DOCX/TXT)
- ✅ Text chunking with optimal size
- ✅ OpenAI embedding generation (requires API key)
- ✅ Database operations (requires DB connection)
- ✅ Full end-to-end pipeline

### 2. Expected Output

```
Starting StudyRAG Ingestion Pipeline Tests
==================================================

==================== test_file_validation ====================
INFO - Testing file validation...
INFO - ✓ Valid file validation passed
INFO - ✓ Invalid MIME type validation passed
INFO - ✓ Non-existent file validation passed
INFO - File validation tests completed ✓

==================== test_text_extraction ====================
INFO - Testing text extraction...
INFO - ✓ Extracted 2 sections
INFO - ✓ Title: Test Document
INFO - ✓ Page count: 1
INFO - Text extraction tests completed ✓

[... more tests ...]

==================================================
Test Results: 6 passed, 0 failed
🎉 All tests passed!
```

## Pipeline Components

### 1. File Upload & Validation
- **Location**: `app/services/ingestion.py:validate_file_for_ingestion()`
- **Function**: Validates file exists, checks size limits, verifies MIME type
- **Supported formats**: PDF, DOCX, DOC, TXT, Markdown
- **Size limit**: 100MB

### 2. Text Extraction
- **Location**: `app/services/extraction.py`
- **Primary method**: Unstructured (for PDFs, complex documents)
- **Fallback method**: MarkItDown (for all formats)
- **Output**: Structured sections with titles, content, page numbers

### 3. Text Chunking
- **Location**: `app/services/chunking.py`
- **Strategy**: Token-based with overlap
- **Default settings**: 500 tokens per chunk, 15% overlap
- **Features**: Section-aware splitting, metadata preservation

### 4. Embedding Generation
- **Location**: `app/services/embeddings.py`  
- **Provider**: OpenAI API
- **Model**: text-embedding-3-small (1536 dimensions)
- **Features**: Batch processing, retry logic, rate limiting

### 5. Database Storage
- **Location**: `app/db/operations.py`
- **Tables**: documents, chunks, embeddings
- **Features**: Bulk inserts, RLS policies, transaction safety

### 6. Background Processing
- **Location**: `app/workers/document_processor.py`
- **Features**: Concurrent processing, job queuing, error handling
- **Concurrency**: Max 3 simultaneous documents

## API Endpoints

### POST `/api/v1/docs/ingest`
Start document ingestion process.

**Request:**
```json
{
  "documentId": "uuid",
  "storagePath": "documents/user123/file.pdf", 
  "mime": "application/pdf"
}
```

**Response:**
```json
{
  "status": "started",
  "documentId": "uuid",
  "jobId": "job_abc123",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### GET `/api/v1/docs/status?documentId=uuid`
Check processing status.

**Response:**
```json
{
  "documentId": "uuid",
  "status": "completed",
  "progress": 100.0,
  "chunksCreated": 25,
  "embeddingsCreated": 25
}
```

## Error Handling

### Common Issues

1. **Database Connection Failed**
   - Check DATABASE_URL format
   - Verify Supabase project is running
   - Ensure RLS policies are properly configured

2. **OpenAI API Errors**
   - Verify OPENAI_API_KEY is valid
   - Check API quota and billing
   - Monitor rate limits

3. **File Processing Errors**
   - Unsupported file format
   - File too large (>100MB)
   - Corrupted file content

4. **Memory Issues**
   - Large documents may require chunking adjustment
   - Consider reducing concurrent job limits

### Monitoring

Check application logs for:
- Processing times
- Error rates  
- Database performance
- API call metrics

## Production Considerations

### 1. Resource Limits
- Memory: 2GB+ recommended for large documents
- CPU: Multi-core for concurrent processing
- Storage: Temp space for file processing

### 2. Scaling
- Increase worker concurrency based on resources
- Consider Redis for job queuing in multi-instance setups
- Monitor OpenAI API rate limits

### 3. Security
- Validate file types strictly
- Scan uploaded files for malware
- Implement request rate limiting
- Use service role key for database operations

### 4. Monitoring
- Set up health checks for all components
- Monitor processing queue depth
- Track success/failure rates
- Alert on API errors

## Troubleshooting

### Test Individual Components

```bash
# Test just text extraction
python -c "
import asyncio
from app.services.extraction import extract_text_from_file
result = asyncio.run(extract_text_from_file('/path/to/test.pdf', 'application/pdf'))
print(f'Extracted {len(result.sections)} sections')
"

# Test just embeddings
python -c "
import asyncio  
from app.services.embeddings import generate_embeddings
result = asyncio.run(generate_embeddings(['test sentence']))
print(f'Generated embedding with {len(result[0])} dimensions')
"
```

### Check Database Connection

```bash
python -c "
import asyncio
from app.db.session import get_db_pool
pool = asyncio.run(get_db_pool())
print('Database connected!' if pool else 'Database connection failed')
"
```

### Validate Configuration

```bash
python -c "
from app.core.config import get_settings
settings = get_settings()
print(f'OpenAI key configured: {bool(settings.openai_api_key)}')
print(f'Database URL configured: {bool(settings.database_url)}')
"
```