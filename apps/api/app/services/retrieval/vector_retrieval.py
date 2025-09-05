"""Vector-based semantic retrieval using pgvector and OpenAI embeddings"""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import asyncio

import asyncpg
import numpy as np

from app.db.session import get_db_pool
from app.services.embeddings import generate_embeddings
from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class VectorResult:
    """Result from vector retrieval"""
    chunk_id: str
    content: str
    page_number: Optional[int]
    section_ref: Optional[str] 
    section_title: Optional[str]
    similarity_score: float
    metadata: Optional[Dict[str, Any]] = None


class VectorRetriever:
    """Vector-based semantic search using pgvector and OpenAI embeddings"""
    
    def __init__(self):
        self.settings = get_settings()
        self._embedding_cache: Dict[str, List[float]] = {}
        
    async def retrieve(
        self,
        query_text: str,
        document_id: str,
        user_id: str,
        limit: int = 20,
        min_similarity: float = 0.0
    ) -> List[VectorResult]:
        """
        Perform vector retrieval on document chunks
        
        Args:
            query_text: User's search query
            document_id: Document UUID to search within
            user_id: User UUID for RLS
            limit: Maximum number of results
            min_similarity: Minimum cosine similarity threshold (0-1)
            
        Returns:
            List of VectorResult objects sorted by similarity score
        """
        logger.info(
            "Starting vector retrieval",
            extra={
                "query_text": query_text,
                "document_id": document_id,
                "user_id": user_id,
                "limit": limit
            }
        )
        
        # Generate query embedding
        try:
            query_embedding = await self._get_query_embedding(query_text)
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return []
        except Exception as e:
            logger.error(
                "Error generating query embedding",
                extra={"error": str(e), "query_text": query_text}
            )
            return []
        
        pool = await get_db_pool()
        if not pool:
            logger.error("Database pool not available")
            return []
            
        try:
            async with pool.acquire() as conn:
                # Set user context for RLS
                await conn.execute(
                    "SELECT set_config('request.jwt.claims', $1, true)",
                    f'{{"sub":"{user_id}"}}'
                )
                
                # Execute vector similarity query using cosine distance
                query = """
                    SELECT 
                        c.id as chunk_id,
                        c.content,
                        c.page_number,
                        c.section_ref,
                        c.section_title,
                        1 - (e.embedding <=> $1::vector) as similarity_score,
                        c.token_count,
                        c.char_count
                    FROM public.embeddings e
                    JOIN public.chunks c ON c.id = e.chunk_id
                    JOIN public.documents d ON d.id = c.document_id
                    WHERE d.id = $2
                        AND 1 - (e.embedding <=> $1::vector) >= $3
                    ORDER BY e.embedding <=> $1::vector
                    LIMIT $4;
                """
                
                rows = await conn.fetch(
                    query,
                    query_embedding,
                    document_id,
                    min_similarity,
                    limit
                )
                
                results = []
                for row in rows:
                    result = VectorResult(
                        chunk_id=row['chunk_id'],
                        content=row['content'],
                        page_number=row['page_number'],
                        section_ref=row['section_ref'],
                        section_title=row['section_title'],
                        similarity_score=float(row['similarity_score']),
                        metadata={
                            'token_count': row['token_count'],
                            'char_count': row['char_count'],
                            'method': 'vector'
                        }
                    )
                    results.append(result)
                
                logger.info(
                    "Vector retrieval completed",
                    extra={
                        "results_count": len(results),
                        "top_score": results[0].similarity_score if results else 0,
                        "document_id": document_id
                    }
                )
                
                return results
                
        except asyncpg.PostgreSQLError as e:
            logger.error(
                "Vector retrieval database error",
                extra={
                    "error": str(e),
                    "query_text": query_text,
                    "document_id": document_id
                }
            )
            return []
        except Exception as e:
            logger.error(
                "Vector retrieval unexpected error",
                extra={
                    "error": str(e),
                    "query_text": query_text,
                    "document_id": document_id
                },
                exc_info=True
            )
            return []
    
    async def _get_query_embedding(self, query_text: str) -> Optional[List[float]]:
        """
        Get embedding for query text with caching
        
        Args:
            query_text: Text to embed
            
        Returns:
            Embedding vector or None if failed
        """
        if not query_text:
            return None
            
        # Check cache first
        cache_key = query_text.strip().lower()
        if cache_key in self._embedding_cache:
            logger.debug("Using cached query embedding")
            return self._embedding_cache[cache_key]
        
        try:
            embeddings = await generate_embeddings([query_text])
            if not embeddings or not embeddings[0]:
                return None
            
            embedding = embeddings[0]
            
            # Cache the embedding (limit cache size)
            if len(self._embedding_cache) > 100:
                # Remove oldest entry (simple LRU)
                oldest_key = next(iter(self._embedding_cache))
                del self._embedding_cache[oldest_key]
            
            self._embedding_cache[cache_key] = embedding
            
            logger.debug(
                "Generated query embedding",
                extra={
                    "query_length": len(query_text),
                    "embedding_dimension": len(embedding)
                }
            )
            
            return embedding
            
        except Exception as e:
            logger.error(
                "Failed to generate query embedding",
                extra={"error": str(e), "query_text": query_text}
            )
            return None
    
    async def find_similar_chunks(
        self,
        reference_chunk_id: str,
        document_id: str,
        user_id: str,
        limit: int = 10,
        min_similarity: float = 0.7
    ) -> List[VectorResult]:
        """
        Find chunks similar to a reference chunk
        
        Args:
            reference_chunk_id: ID of the reference chunk
            document_id: Document UUID to search within
            user_id: User UUID for RLS
            limit: Maximum number of results
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of similar chunks
        """
        pool = await get_db_pool()
        if not pool:
            return []
            
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    "SELECT set_config('request.jwt.claims', $1, true)",
                    f'{{"sub":"{user_id}"}}'
                )
                
                # Get reference embedding and find similar chunks
                query = """
                    WITH ref_embedding AS (
                        SELECT e.embedding
                        FROM public.embeddings e
                        JOIN public.chunks c ON c.id = e.chunk_id
                        JOIN public.documents d ON d.id = c.document_id
                        WHERE c.id = $1 AND d.id = $2
                    )
                    SELECT 
                        c.id as chunk_id,
                        c.content,
                        c.page_number,
                        c.section_ref,
                        c.section_title,
                        1 - (e.embedding <=> ref.embedding) as similarity_score
                    FROM public.embeddings e
                    JOIN public.chunks c ON c.id = e.chunk_id
                    JOIN public.documents d ON d.id = c.document_id
                    CROSS JOIN ref_embedding ref
                    WHERE d.id = $2
                        AND c.id != $1
                        AND 1 - (e.embedding <=> ref.embedding) >= $3
                    ORDER BY e.embedding <=> ref.embedding
                    LIMIT $4;
                """
                
                rows = await conn.fetch(
                    query,
                    reference_chunk_id,
                    document_id,
                    min_similarity,
                    limit
                )
                
                results = []
                for row in rows:
                    result = VectorResult(
                        chunk_id=row['chunk_id'],
                        content=row['content'],
                        page_number=row['page_number'],
                        section_ref=row['section_ref'],
                        section_title=row['section_title'],
                        similarity_score=float(row['similarity_score']),
                        metadata={'method': 'vector_similar'}
                    )
                    results.append(result)
                
                return results
                
        except Exception as e:
            logger.error(
                "Error finding similar chunks",
                extra={
                    "error": str(e),
                    "reference_chunk_id": reference_chunk_id,
                    "document_id": document_id
                }
            )
            return []
    
    async def get_embedding_stats(
        self,
        document_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get statistics about embeddings in a document
        
        Args:
            document_id: Document UUID
            user_id: User UUID
            
        Returns:
            Dictionary with embedding statistics
        """
        pool = await get_db_pool()
        if not pool:
            return {"error": "Database not available"}
            
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    "SELECT set_config('request.jwt.claims', $1, true)",
                    f'{{"sub":"{user_id}"}}'
                )
                
                # Get embedding statistics
                stats_query = """
                    SELECT 
                        COUNT(*) as total_embeddings,
                        AVG(array_length(e.embedding, 1)) as avg_dimension,
                        COUNT(DISTINCT c.page_number) as pages_with_embeddings
                    FROM public.embeddings e
                    JOIN public.chunks c ON c.id = e.chunk_id
                    JOIN public.documents d ON d.id = c.document_id
                    WHERE d.id = $1;
                """
                
                row = await conn.fetchrow(stats_query, document_id)
                
                return {
                    "document_id": document_id,
                    "total_embeddings": row['total_embeddings'],
                    "avg_dimension": int(row['avg_dimension'] or 0),
                    "pages_with_embeddings": row['pages_with_embeddings'],
                    "cache_size": len(self._embedding_cache)
                }
                
        except Exception as e:
            logger.error(
                "Error getting embedding stats",
                extra={"error": str(e), "document_id": document_id}
            )
            return {"error": str(e)}
    
    def clear_cache(self):
        """Clear the embedding cache"""
        self._embedding_cache.clear()
        logger.info("Embedding cache cleared")


async def test_vector_retrieval():
    """Test function for vector retrieval"""
    retriever = VectorRetriever()
    
    # Test with sample data
    results = await retriever.retrieve(
        query_text="What are neural networks?",
        document_id="test-doc-123",
        user_id="test-user-123",
        limit=5
    )
    
    print(f"Vector retrieval test: {len(results)} results")
    for result in results:
        print(f"Similarity: {result.similarity_score:.3f}, Content: {result.content[:100]}...")
    
    return results


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_vector_retrieval())