"""Text chunking service for creating optimal chunks for embeddings and retrieval"""

import logging
import re
from typing import List, Optional, Dict
from dataclasses import dataclass
from uuid import uuid4

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    tiktoken = None
    TIKTOKEN_AVAILABLE = False

from .extraction import ExtractedContent, ExtractedSection

logger = logging.getLogger(__name__)


@dataclass
class ChunkData:
    """A chunk of text ready for embedding and storage"""
    id: str
    content: str
    token_count: int
    char_count: int
    section_title: Optional[str] = None
    page_number: Optional[int] = None
    section_type: str = "text"
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
            
        # Generate ID if not provided
        if not self.id:
            self.id = str(uuid4())


def count_tokens(text: str, model: str = "text-embedding-ada-002") -> int:
    """Count tokens in text using tiktoken"""
    if not TIKTOKEN_AVAILABLE:
        # Rough approximation: 1 token ≈ 4 characters
        return len(text) // 4
    
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception:
        # Fall back to character-based approximation
        return len(text) // 4


def create_chunks(
    content: ExtractedContent,
    chunk_size: int = 500,
    overlap_ratio: float = 0.15,
    min_chunk_size: int = 50,
    max_chunk_size: int = 800
) -> List[ChunkData]:
    """
    Create chunks from extracted content with optimal sizing for embeddings.
    
    Args:
        content: ExtractedContent from extraction service
        chunk_size: Target tokens per chunk (default: 500)
        overlap_ratio: Overlap between chunks (default: 15%)
        min_chunk_size: Minimum chunk size in tokens
        max_chunk_size: Maximum chunk size in tokens
        
    Returns:
        List[ChunkData]: Optimally sized chunks for embedding
    """
    logger.info(
        "Starting text chunking",
        extra={
            "section_count": len(content.sections),
            "target_chunk_size": chunk_size,
            "overlap_ratio": overlap_ratio
        }
    )
    
    chunks = []
    
    for section in content.sections:
        if not section.content.strip():
            continue
            
        # Handle short sections
        token_count = count_tokens(section.content)
        if token_count <= max_chunk_size:
            # Small section - keep as single chunk
            chunk = ChunkData(
                id=str(uuid4()),
                content=section.content.strip(),
                token_count=token_count,
                char_count=len(section.content),
                section_title=section.title,
                page_number=section.page_number,
                section_type=section.section_type,
                metadata={
                    "extraction_method": content.metadata.get("extraction_method", "unknown"),
                    "is_complete_section": True
                }
            )
            chunks.append(chunk)
            continue
        
        # Large section - split into chunks
        section_chunks = _split_long_section(
            section, 
            chunk_size, 
            overlap_ratio, 
            min_chunk_size, 
            max_chunk_size,
            content.metadata
        )
        chunks.extend(section_chunks)
    
    # Post-processing: merge very small chunks
    chunks = _merge_small_chunks(chunks, min_chunk_size)
    
    logger.info(
        "Text chunking completed",
        extra={
            "chunk_count": len(chunks),
            "avg_chunk_size": sum(c.token_count for c in chunks) / len(chunks) if chunks else 0,
            "total_tokens": sum(c.token_count for c in chunks)
        }
    )
    
    return chunks


def _split_long_section(
    section: ExtractedSection,
    chunk_size: int,
    overlap_ratio: float,
    min_chunk_size: int,
    max_chunk_size: int,
    global_metadata: Dict
) -> List[ChunkData]:
    """Split a long section into overlapping chunks"""
    
    text = section.content.strip()
    chunks = []
    
    # Split by sentences first
    sentences = _split_by_sentences(text)
    if not sentences:
        return []
    
    overlap_size = int(chunk_size * overlap_ratio)
    current_chunk_sentences = []
    current_tokens = 0
    
    i = 0
    while i < len(sentences):
        sentence = sentences[i]
        sentence_tokens = count_tokens(sentence)
        
        # If adding this sentence would exceed max size, finalize current chunk
        if current_tokens + sentence_tokens > max_chunk_size and current_chunk_sentences:
            chunk_text = ' '.join(current_chunk_sentences)
            if count_tokens(chunk_text) >= min_chunk_size:
                chunk = ChunkData(
                    id=str(uuid4()),
                    content=chunk_text,
                    token_count=count_tokens(chunk_text),
                    char_count=len(chunk_text),
                    section_title=section.title,
                    page_number=section.page_number,
                    section_type=section.section_type,
                    metadata={
                        **global_metadata,
                        "is_complete_section": False,
                        "chunk_index": len(chunks)
                    }
                )
                chunks.append(chunk)
            
            # Start new chunk with overlap
            if overlap_size > 0:
                # Keep last few sentences for overlap
                overlap_tokens = 0
                overlap_sentences = []
                for j in range(len(current_chunk_sentences) - 1, -1, -1):
                    sent = current_chunk_sentences[j]
                    sent_tokens = count_tokens(sent)
                    if overlap_tokens + sent_tokens <= overlap_size:
                        overlap_sentences.insert(0, sent)
                        overlap_tokens += sent_tokens
                    else:
                        break
                
                current_chunk_sentences = overlap_sentences
                current_tokens = overlap_tokens
            else:
                current_chunk_sentences = []
                current_tokens = 0
        
        # Add current sentence
        current_chunk_sentences.append(sentence)
        current_tokens += sentence_tokens
        i += 1
        
        # If we've reached a good chunk size, and we're not at the end
        if (current_tokens >= chunk_size and 
            i < len(sentences) and 
            current_tokens <= max_chunk_size):
            continue
    
    # Add final chunk
    if current_chunk_sentences:
        chunk_text = ' '.join(current_chunk_sentences)
        if count_tokens(chunk_text) >= min_chunk_size:
            chunk = ChunkData(
                id=str(uuid4()),
                content=chunk_text,
                token_count=count_tokens(chunk_text),
                char_count=len(chunk_text),
                section_title=section.title,
                page_number=section.page_number,
                section_type=section.section_type,
                metadata={
                    **global_metadata,
                    "is_complete_section": False,
                    "chunk_index": len(chunks)
                }
            )
            chunks.append(chunk)
    
    return chunks


def _split_by_sentences(text: str) -> List[str]:
    """Split text into sentences using regex"""
    # Simple sentence splitting - can be improved with NLTK if needed
    sentences = re.split(r'[.!?]+\s+', text)
    
    # Clean and filter
    cleaned_sentences = []
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 10:  # Filter very short fragments
            cleaned_sentences.append(sentence)
    
    return cleaned_sentences


def _merge_small_chunks(chunks: List[ChunkData], min_chunk_size: int) -> List[ChunkData]:
    """Merge chunks that are too small with adjacent chunks"""
    if not chunks:
        return chunks
    
    merged_chunks = []
    i = 0
    
    while i < len(chunks):
        current_chunk = chunks[i]
        
        # If chunk is too small and not the last chunk
        if (current_chunk.token_count < min_chunk_size and 
            i + 1 < len(chunks)):
            
            next_chunk = chunks[i + 1]
            
            # Check if they can be merged without exceeding max size
            combined_tokens = current_chunk.token_count + next_chunk.token_count
            if combined_tokens <= 800:  # max_chunk_size
                # Merge chunks
                merged_content = current_chunk.content + "\n\n" + next_chunk.content
                merged_chunk = ChunkData(
                    id=str(uuid4()),
                    content=merged_content,
                    token_count=count_tokens(merged_content),
                    char_count=len(merged_content),
                    section_title=current_chunk.section_title or next_chunk.section_title,
                    page_number=current_chunk.page_number or next_chunk.page_number,
                    section_type=current_chunk.section_type,
                    metadata={
                        **current_chunk.metadata,
                        "is_merged_chunk": True,
                        "original_chunk_count": 2
                    }
                )
                merged_chunks.append(merged_chunk)
                i += 2  # Skip both chunks
                continue
        
        # Add chunk as-is
        merged_chunks.append(current_chunk)
        i += 1
    
    return merged_chunks