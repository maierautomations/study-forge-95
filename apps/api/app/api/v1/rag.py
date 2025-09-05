"""RAG (Retrieval Augmented Generation) endpoints"""

import logging
import uuid
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.rag import (
    RagQuery, 
    RagResponse, 
    Citation,
    SearchQuery,
    SearchResponse,
    SearchResult
)
from app.models.common import BaseResponse
from app.api.deps import get_current_user_id, get_trace_id
from app.services.rag import RAGService, RAGConfig

logger = logging.getLogger(__name__)
router = APIRouter()


# Chat session and message models
class ChatSession(BaseModel):
    """Chat session model"""
    id: UUID = Field(description="Session ID")
    user_id: UUID = Field(description="User ID", alias="userId")
    document_id: UUID = Field(description="Document ID", alias="documentId")
    title: str = Field(description="Session title")
    created_at: datetime = Field(description="Creation timestamp", alias="createdAt")
    updated_at: datetime = Field(description="Last update timestamp", alias="updatedAt")
    
    class Config:
        populate_by_name = True


class ChatMessage(BaseModel):
    """Chat message model"""
    id: UUID = Field(description="Message ID")
    session_id: UUID = Field(description="Session ID", alias="sessionId")
    role: str = Field(description="Message role (user or assistant)")
    content: str = Field(description="Message content")
    sources: Optional[dict] = Field(default=None, description="Sources/citations")
    timestamp: datetime = Field(description="Message timestamp")
    
    class Config:
        populate_by_name = True


class ChatSessionCreateRequest(BaseModel):
    """Chat session creation request"""
    document_id: UUID = Field(description="Document ID", alias="documentId")
    title: Optional[str] = Field(default=None, description="Session title")
    
    class Config:
        populate_by_name = True


class ChatMessageCreateRequest(BaseModel):
    """Chat message creation request"""
    session_id: UUID = Field(description="Session ID", alias="sessionId")
    content: str = Field(description="Message content")
    role: str = Field(description="Message role (user or assistant)")
    sources: Optional[dict] = Field(default=None, description="Sources/citations")
    
    class Config:
        populate_by_name = True


@router.post("/query", response_model=RagResponse)
async def rag_query(
    request: RagQuery,
    user_id: UUID = Depends(get_current_user_id),
    trace_id: Optional[str] = Depends(get_trace_id)
):
    """
    Query document using RAG (Retrieval Augmented Generation)
    
    Process:
    1. Generate embedding for user question
    2. Perform hybrid search (BM25 + vector similarity)  
    3. Retrieve top relevant chunks as context
    4. Generate answer using LLM with retrieved context
    5. Return answer with source citations
    
    This is the core StudyRAG functionality for document Q&A.
    """
    logger.info(
        "RAG query started",
        extra={
            "trace_id": trace_id,
            "document_id": str(request.document_id),
            "user_id": str(user_id),
            "question_length": len(request.question),
            "max_chunks": getattr(request, 'max_chunks', 10)
        }
    )
    
    try:
        # Configure RAG service based on request parameters
        config_override = {
            "max_chunks": getattr(request, 'max_chunks', 10),
            "temperature": getattr(request, 'temperature', 0.7),
            "max_tokens": getattr(request, 'max_tokens', 1000)
        }
        
        # Initialize RAG service
        rag_service = RAGService()
        
        # Process the query
        rag_response = await rag_service.query(
            question=request.question,
            document_id=str(request.document_id),
            user_id=str(user_id),
            config_override=config_override
        )
        
        # Convert RAG service response to API response format
        api_citations = []
        for citation_dict in rag_response.citations:
            api_citation = Citation(
                chunkId=UUID(citation_dict["chunkId"]),
                page=citation_dict.get("page"),
                section=citation_dict.get("section"),
                textSnippet=citation_dict["textSnippet"],
                relevanceScore=citation_dict["relevanceScore"]
            )
            api_citations.append(api_citation)
        
        # Return API response
        return RagResponse(
            answer=rag_response.answer,
            citations=api_citations,
            question=request.question,
            document_id=request.document_id,
            processing_time_ms=rag_response.processing_time * 1000,  # Convert to milliseconds
            model_used=rag_response.llm_stats.get("model", "gpt-3.5-turbo"),
            trace_id=trace_id
        )
        
    except Exception as e:
        logger.error(
            "RAG query failed",
            extra={
                "trace_id": trace_id,
                "document_id": str(request.document_id),
                "user_id": str(user_id),
                "error": str(e)
            },
            exc_info=True
        )
        
        # Return error response with helpful message
        return RagResponse(
            answer=f"I encountered an error while processing your question: {str(e)}. Please try again or rephrase your question.",
            citations=[],
            question=request.question,
            document_id=request.document_id,
            processing_time_ms=0,
            model_used="error",
            trace_id=trace_id
        )


@router.post("/query/stream")
async def rag_query_stream(
    request: RagQuery,
    user_id: UUID = Depends(get_current_user_id),
    trace_id: Optional[str] = Depends(get_trace_id)
):
    """
    Query document using RAG with streaming response
    
    Returns a streaming response with:
    1. Status updates during processing
    2. Citations when found
    3. Answer chunks as they're generated
    4. Completion status
    
    Response format: Server-Sent Events (text/plain)
    """
    logger.info(
        "Streaming RAG query started",
        extra={
            "trace_id": trace_id,
            "document_id": str(request.document_id),
            "user_id": str(user_id),
            "question_length": len(request.question)
        }
    )
    
    async def generate_stream():
        try:
            # Configure RAG service for streaming
            config_override = {
                "max_chunks": getattr(request, 'max_chunks', 10),
                "temperature": getattr(request, 'temperature', 0.7),
                "max_tokens": getattr(request, 'max_tokens', 1000),
                "streaming": True
            }
            
            # Initialize RAG service
            rag_service = RAGService()
            
            # Stream the query processing
            async for chunk in rag_service.query_streaming(
                question=request.question,
                document_id=str(request.document_id),
                user_id=str(user_id),
                config_override=config_override
            ):
                # Format as Server-Sent Event
                chunk_data = f"data: {chunk}\n\n"
                yield chunk_data
                
        except Exception as e:
            logger.error(
                "Streaming RAG query failed",
                extra={
                    "trace_id": trace_id,
                    "error": str(e)
                },
                exc_info=True
            )
            
            error_chunk = {
                "type": "error",
                "message": f"Stream error: {str(e)}",
                "trace_id": trace_id
            }
            yield f"data: {error_chunk}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Trace-ID": trace_id or ""
        }
    )


@router.post("/search", response_model=SearchResponse)
async def search_document(
    request: SearchQuery,
    user_id: UUID = Depends(get_current_user_id),
    trace_id: Optional[str] = Depends(get_trace_id)
):
    """
    Search document without LLM generation
    
    Performs hybrid search (BM25 + vector) and returns ranked chunks
    without generating an answer. Useful for:
    - Finding specific information quickly
    - Debugging search relevance
    - Building custom interfaces
    """
    logger.info(
        "Document search started",
        extra={
            "trace_id": trace_id,
            "document_id": str(request.document_id),
            "user_id": str(user_id),
            "query_length": len(request.query),
            "search_type": request.search_type,
            "limit": request.limit
        }
    )
    
    # DUMMY: Return sample search results
    dummy_results = [
        SearchResult(
            chunkId=UUID("660e8400-e29b-41d4-a716-446655440000"),
            content="The experimental methodology involved a comprehensive evaluation using multiple datasets to ensure robustness and generalizability of the findings. We employed cross-validation techniques and statistical significance testing to validate our results...",
            score=0.95,
            page=5,
            section="3.2 Results"
        ),
        SearchResult(
            chunkId=UUID("660e8400-e29b-41d4-a716-446655440001"),
            content="Previous research in this domain has shown limitations in scalability and accuracy. Our approach addresses these issues through novel algorithmic improvements and optimization strategies that reduce computational complexity while maintaining performance...",
            score=0.89,
            page=2,
            section="2.1 Related Work"
        ),
        SearchResult(
            chunkId=UUID("660e8400-e29b-41d4-a716-446655440002"),
            content="The implications of these findings extend beyond the immediate research context. Potential applications include industrial automation, data processing pipelines, and real-time decision support systems where accuracy and efficiency are paramount...",
            score=0.82,
            page=15,
            section="5. Conclusions"
        )
    ]
    
    # Apply limit
    limited_results = dummy_results[:request.limit or 10]
    
    return SearchResponse(
        results=limited_results,
        query=request.query,
        document_id=request.document_id,
        totalChunks=47,  # Total chunks in document
        searchType=request.search_type or "hybrid",
        trace_id=trace_id
    )


@router.get("/sessions", response_model=List[ChatSession])
async def get_chat_sessions(
    document_id: UUID = Query(description="Document ID to get sessions for", alias="documentId"),
    user_id: UUID = Depends(get_current_user_id),
    trace_id: Optional[str] = Depends(get_trace_id)
):
    """
    Get chat sessions for a document
    
    Returns all chat sessions for the specified document.
    """
    logger.info(
        "Chat sessions requested",
        extra={
            "trace_id": trace_id,
            "document_id": str(document_id),
            "user_id": str(user_id)
        }
    )
    
    # DUMMY: Return sample chat sessions
    return [
        ChatSession(
            id=UUID("880e8400-e29b-41d4-a716-446655440000"),
            userId=user_id,
            documentId=document_id,
            title="Research Questions",
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow()
        ),
        ChatSession(
            id=UUID("880e8400-e29b-41d4-a716-446655440001"),
            userId=user_id,
            documentId=document_id,
            title="Study Session",
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow()
        )
    ]


@router.post("/sessions", response_model=ChatSession)
async def create_chat_session(
    request: ChatSessionCreateRequest,
    user_id: UUID = Depends(get_current_user_id),
    trace_id: Optional[str] = Depends(get_trace_id)
):
    """
    Create a new chat session
    
    Creates a new chat session for the specified document.
    """
    logger.info(
        "Chat session creation requested",
        extra={
            "trace_id": trace_id,
            "document_id": str(request.document_id),
            "user_id": str(user_id),
            "title": request.title
        }
    )
    
    # DUMMY: Return new chat session
    session_id = UUID(f"{uuid.uuid4()}")
    return ChatSession(
        id=session_id,
        userId=user_id,
        documentId=request.document_id,
        title=request.title or f"Chat Session {session_id.hex[:8]}",
        createdAt=datetime.utcnow(),
        updatedAt=datetime.utcnow()
    )


@router.get("/messages", response_model=List[ChatMessage])
async def get_chat_messages(
    session_id: UUID = Query(description="Session ID to get messages for", alias="sessionId"),
    user_id: UUID = Depends(get_current_user_id),
    trace_id: Optional[str] = Depends(get_trace_id)
):
    """
    Get messages for a chat session
    
    Returns all messages in the specified chat session.
    """
    logger.info(
        "Chat messages requested",
        extra={
            "trace_id": trace_id,
            "session_id": str(session_id),
            "user_id": str(user_id)
        }
    )
    
    # DUMMY: Return sample chat messages
    return [
        ChatMessage(
            id=UUID("990e8400-e29b-41d4-a716-446655440000"),
            sessionId=session_id,
            role="user",
            content="What are the main findings of this research?",
            sources=None,
            timestamp=datetime.utcnow()
        ),
        ChatMessage(
            id=UUID("990e8400-e29b-41d4-a716-446655440001"),
            sessionId=session_id,
            role="assistant",
            content="Based on the document, the main findings include...",
            sources={
                "chunks": ["chunk1", "chunk2"],
                "pages": [5, 12]
            },
            timestamp=datetime.utcnow()
        )
    ]


@router.post("/messages", response_model=ChatMessage)
async def create_chat_message(
    request: ChatMessageCreateRequest,
    user_id: UUID = Depends(get_current_user_id),
    trace_id: Optional[str] = Depends(get_trace_id)
):
    """
    Create a new chat message
    
    Adds a new message to the specified chat session.
    """
    logger.info(
        "Chat message creation requested",
        extra={
            "trace_id": trace_id,
            "session_id": str(request.session_id),
            "user_id": str(user_id),
            "role": request.role
        }
    )
    
    # DUMMY: Return new chat message
    return ChatMessage(
        id=UUID(f"{uuid.uuid4()}"),
        sessionId=request.session_id,
        role=request.role,
        content=request.content,
        sources=request.sources,
        timestamp=datetime.utcnow()
    )