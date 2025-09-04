"""StudyRAG API models package"""

from .common import ErrorResponse, BaseResponse
from .documents import DocumentBase, IngestRequest, IngestResponse, DocumentStatusResponse
from .rag import RagQuery, RagResponse, Citation
from .quiz import QuizConfig, QuizGenerateRequest, QuizGenerateResponse, QuizSubmitRequest, QuizSubmitResponse

__all__ = [
    # Common models
    "ErrorResponse",
    "BaseResponse",
    
    # Document models
    "DocumentBase",
    "IngestRequest", 
    "IngestResponse",
    "DocumentStatusResponse",
    
    # RAG models
    "RagQuery",
    "RagResponse", 
    "Citation",
    
    # Quiz models
    "QuizConfig",
    "QuizGenerateRequest",
    "QuizGenerateResponse", 
    "QuizSubmitRequest",
    "QuizSubmitResponse"
]