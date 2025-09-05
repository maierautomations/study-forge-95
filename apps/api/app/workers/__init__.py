"""Background workers for document processing"""

from .document_processor import process_document_background

__all__ = [
    "process_document_background"
]