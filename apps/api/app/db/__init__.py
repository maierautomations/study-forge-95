"""Database module for StudyRAG API"""

from .session import init_db_pool, close_db_pool, get_db_pool
from .validation import validate_schema
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
    "init_db_pool",
    "close_db_pool", 
    "get_db_pool",
    "validate_schema",
    "insert_chunks",
    "insert_embeddings", 
    "update_document_status",
    "get_document_chunks",
    "get_document_embeddings",
    "delete_document_chunks",
    "get_chunk_with_embedding",
    "count_document_chunks"
]