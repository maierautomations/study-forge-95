"""Database module for StudyRAG API"""

from .session import init_database, cleanup_database, get_db_pool
from .validation import validate_schema_complete
from .operations import (
    insert_chunks,
    insert_embeddings,
    update_document_status,
    get_document_chunks,
    get_document_embeddings,
    delete_document_chunks,
    get_chunk_with_embedding,
    count_document_chunks
)

__all__ = [
    "init_database",
    "cleanup_database", 
    "get_db_pool",
    "validate_schema_complete",
    "insert_chunks",
    "insert_embeddings", 
    "update_document_status",
    "get_document_chunks",
    "get_document_embeddings",
    "delete_document_chunks",
    "get_chunk_with_embedding",
    "count_document_chunks"
]