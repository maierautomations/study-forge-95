"""OpenAPI schema export and customization"""

from typing import Dict, Any
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app import __version__


def custom_openapi(app: FastAPI) -> Dict[str, Any]:
    """
    Generate custom OpenAPI schema with enhanced metadata
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="StudyRAG API",
        version=__version__,
        description="""
# StudyRAG API

**RAG-powered Chat with Citations & Quiz Generation for Students**

## Features

- 📚 **Document Processing**: Upload and process academic documents (PDF, DOCX, TXT)
- 🔍 **Intelligent Search**: Hybrid search combining BM25 and semantic vector search
- 💬 **RAG Chat**: Get answers with proper citations from your documents
- 📝 **Quiz Generation**: Auto-generate quizzes based on document content
- 🔒 **Secure**: Row-level security with user isolation
- ⚡ **Fast**: Optimized with pgvector for vector operations

## Authentication

All endpoints (except health checks) require JWT authentication:

```
Authorization: Bearer <your-jwt-token>
```

For development, use: `Bearer dev-user-123`

## Rate Limits

- Document ingestion: 10 requests/minute
- RAG queries: 60 requests/minute
- Quiz generation: 5 requests/minute

## Support

- 📖 Documentation: See `/docs` for interactive API documentation
- 🐛 Issues: Report bugs via GitHub Issues
- 💡 Feature requests: Submit enhancement requests

## DSGVO Compliance

This API is designed for EU compliance:
- User data isolation via RLS policies  
- No service keys exposed to frontend
- Audit logging for data access
- Right to deletion support
        """,
        routes=app.routes,
        contact={
            "name": "StudyRAG Team",
            "email": "support@studyrag.example.com",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
        servers=[
            {
                "url": "http://localhost:8002",
                "description": "Development server"
            },
            {
                "url": "https://api.studyrag.example.com",
                "description": "Production server"
            }
        ]
    )
    
    # Customize security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token from Supabase Auth. For development use: `dev-user-123`"
        }
    }
    
    # Add global security requirement
    openapi_schema["security"] = [{"BearerAuth": []}]
    
    # Add custom tags
    openapi_schema["tags"] = [
        {
            "name": "Health",
            "description": "Health check and system status endpoints"
        },
        {
            "name": "Schema", 
            "description": "Database schema validation endpoints"
        },
        {
            "name": "Documents",
            "description": "Document upload, processing and management"
        },
        {
            "name": "RAG",
            "description": "Retrieval Augmented Generation - chat with documents"
        },
        {
            "name": "Quiz",
            "description": "Quiz generation and submission from document content"
        }
    ]
    
    # Add response examples
    openapi_schema["components"]["examples"] = {
        "ErrorResponse": {
            "summary": "Standard error response",
            "value": {
                "type": "/errors/validation-error",
                "title": "Validation Error", 
                "status": 422,
                "detail": "The request contains invalid data",
                "timestamp": "2024-01-01T00:00:00Z",
                "trace_id": "abc123"
            }
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def export_openapi_json(app: FastAPI) -> str:
    """Export OpenAPI schema as JSON string"""
    import json
    schema = custom_openapi(app)
    return json.dumps(schema, indent=2, default=str)