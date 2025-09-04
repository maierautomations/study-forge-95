"""RAG (Retrieval Augmented Generation) models"""

from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

from .common import BaseResponse


class RagQuery(BaseModel):
    """RAG query request"""
    document_id: UUID = Field(description="Document ID to query against", alias="documentId")
    question: str = Field(description="User's question", min_length=1, max_length=1000)
    max_chunks: Optional[int] = Field(default=10, description="Maximum chunks for context", alias="maxChunks", ge=1, le=20)
    include_citations: bool = Field(default=True, description="Include citations in response", alias="includeCitations")
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "documentId": "550e8400-e29b-41d4-a716-446655440000",
                "question": "What are the main findings of this research?",
                "maxChunks": 10,
                "includeCitations": True
            }
        }


class Citation(BaseModel):
    """Citation reference from source document"""
    chunk_id: UUID = Field(description="Chunk ID for reference", alias="chunkId")
    page: Optional[int] = Field(default=None, description="Page number (if available)", ge=1)
    section: Optional[str] = Field(default=None, description="Section reference (if available)")
    text_snippet: str = Field(description="Relevant text snippet", alias="textSnippet", max_length=500)
    relevance_score: Optional[float] = Field(default=None, description="Relevance score (0-1)", alias="relevanceScore", ge=0, le=1)
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "chunkId": "660e8400-e29b-41d4-a716-446655440000",
                "page": 5,
                "section": "3.2 Results",
                "textSnippet": "The experiment showed significant improvement in performance metrics...",
                "relevanceScore": 0.85
            }
        }


class RagResponse(BaseResponse):
    """RAG response with answer and citations"""
    answer: str = Field(description="Generated answer to the question")
    citations: List[Citation] = Field(description="Source citations for the answer")
    question: str = Field(description="Original question for reference")
    document_id: UUID = Field(description="Document ID that was queried", alias="documentId")
    processing_time_ms: Optional[float] = Field(default=None, description="Processing time in milliseconds", alias="processingTimeMs")
    model_used: Optional[str] = Field(default=None, description="LLM model used for generation", alias="modelUsed")
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "answer": "Based on the research findings, the main discoveries include improved performance metrics and significant cost reductions in the proposed methodology.",
                "citations": [
                    {
                        "chunkId": "660e8400-e29b-41d4-a716-446655440000",
                        "page": 5,
                        "section": "3.2 Results",
                        "textSnippet": "The experiment showed significant improvement...",
                        "relevanceScore": 0.85
                    }
                ],
                "question": "What are the main findings of this research?",
                "documentId": "550e8400-e29b-41d4-a716-446655440000",
                "processingTimeMs": 1250.5,
                "modelUsed": "gpt-4o-mini",
                "timestamp": "2024-01-01T00:00:00Z",
                "trace_id": "rag_trace_123"
            }
        }


class SearchQuery(BaseModel):
    """Semantic search query (without LLM generation)"""
    document_id: UUID = Field(description="Document ID to search", alias="documentId")
    query: str = Field(description="Search query", min_length=1, max_length=500)
    limit: Optional[int] = Field(default=10, description="Maximum results to return", ge=1, le=50)
    search_type: Optional[str] = Field(default="hybrid", description="Search type: semantic, bm25, or hybrid", alias="searchType")
    
    class Config:
        populate_by_name = True


class SearchResult(BaseModel):
    """Individual search result"""
    chunk_id: UUID = Field(description="Chunk ID", alias="chunkId")
    content: str = Field(description="Chunk content")
    score: float = Field(description="Search relevance score", ge=0, le=1)
    page: Optional[int] = Field(default=None, description="Page number")
    section: Optional[str] = Field(default=None, description="Section reference")
    
    class Config:
        populate_by_name = True


class SearchResponse(BaseResponse):
    """Search results response"""
    results: List[SearchResult] = Field(description="Search results")
    query: str = Field(description="Original search query")
    document_id: UUID = Field(description="Document ID searched", alias="documentId")
    total_chunks: int = Field(description="Total chunks in document", alias="totalChunks")
    search_type: str = Field(description="Search type used", alias="searchType")
    
    class Config:
        populate_by_name = True