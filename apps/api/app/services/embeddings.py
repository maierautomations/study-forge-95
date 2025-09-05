"""Embeddings generation service using OpenAI API"""

import asyncio
import logging
from typing import List, Optional, Tuple
import openai
from openai import AsyncOpenAI

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """Service for generating text embeddings using OpenAI"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        self.model = "text-embedding-3-small"  # Latest, efficient model
        self.batch_size = 100  # OpenAI batch limit
        self.max_retries = 3
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors (1536-dimensional)
            
        Raises:
            openai.OpenAIError: If API calls fail
        """
        if not texts:
            return []
            
        logger.info(
            "Starting embedding generation",
            extra={
                "text_count": len(texts),
                "model": self.model,
                "batch_size": self.batch_size
            }
        )
        
        # Process in batches to respect API limits
        all_embeddings = []
        
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            batch_embeddings = await self._generate_batch_embeddings(batch)
            all_embeddings.extend(batch_embeddings)
            
            # Log progress for large batches
            if len(texts) > self.batch_size:
                logger.info(
                    "Embedding batch completed",
                    extra={
                        "batch_num": (i // self.batch_size) + 1,
                        "batch_size": len(batch),
                        "total_completed": len(all_embeddings),
                        "total_texts": len(texts)
                    }
                )
        
        logger.info(
            "Embedding generation completed",
            extra={
                "text_count": len(texts),
                "embedding_count": len(all_embeddings),
                "embedding_dimension": len(all_embeddings[0]) if all_embeddings else 0
            }
        )
        
        return all_embeddings
    
    async def _generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a single batch with retry logic"""
        
        for attempt in range(self.max_retries):
            try:
                # Prepare texts (clean and truncate if necessary)
                cleaned_texts = [self._prepare_text(text) for text in texts]
                
                # Call OpenAI API
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=cleaned_texts,
                    encoding_format="float"
                )
                
                # Extract embeddings from response
                embeddings = [data.embedding for data in response.data]
                
                if len(embeddings) != len(texts):
                    raise ValueError(f"Embedding count mismatch: got {len(embeddings)}, expected {len(texts)}")
                
                return embeddings
                
            except openai.RateLimitError as e:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(
                    "Rate limit hit, retrying",
                    extra={
                        "attempt": attempt + 1,
                        "wait_time": wait_time,
                        "error": str(e)
                    }
                )
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                logger.error(
                    "Embedding generation error",
                    extra={
                        "attempt": attempt + 1,
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                )
                
                if attempt == self.max_retries - 1:
                    raise
                
                # Wait before retry
                await asyncio.sleep(1.0 * (attempt + 1))
        
        raise RuntimeError(f"Failed to generate embeddings after {self.max_retries} attempts")
    
    def _prepare_text(self, text: str) -> str:
        """Prepare text for embedding generation"""
        if not text or not text.strip():
            return " "  # OpenAI doesn't accept empty strings
        
        # Clean text
        text = text.strip()
        
        # Truncate if too long (8191 tokens is the limit for text-embedding-3-small)
        # Rough approximation: 1 token ≈ 4 characters
        max_chars = 8191 * 4
        if len(text) > max_chars:
            text = text[:max_chars]
            logger.warning(
                "Text truncated for embedding",
                extra={"original_length": len(text), "truncated_length": max_chars}
            )
        
        return text


# Global service instance
_embeddings_service: Optional[EmbeddingsService] = None


async def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Convenience function to generate embeddings.
    
    Args:
        texts: List of text strings to embed
        
    Returns:
        List of embedding vectors
    """
    global _embeddings_service
    
    if _embeddings_service is None:
        _embeddings_service = EmbeddingsService()
    
    return await _embeddings_service.generate_embeddings(texts)


async def generate_single_embedding(text: str) -> List[float]:
    """
    Generate embedding for a single text.
    
    Args:
        text: Text string to embed
        
    Returns:
        Single embedding vector
    """
    embeddings = await generate_embeddings([text])
    return embeddings[0] if embeddings else []


async def generate_chunk_embeddings(chunks: List[str]) -> List[Tuple[int, List[float]]]:
    """
    Generate embeddings for chunks with index tracking.
    
    Args:
        chunks: List of chunk texts
        
    Returns:
        List of (chunk_index, embedding) tuples
    """
    embeddings = await generate_embeddings(chunks)
    return [(i, embedding) for i, embedding in enumerate(embeddings)]