"""BM25-based full-text retrieval using PostgreSQL tsvector"""

import logging
import re
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from uuid import UUID

import asyncpg

from app.db.session import get_db_pool
from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class BM25Result:
    """Result from BM25 retrieval"""
    chunk_id: str
    content: str
    page_number: Optional[int]
    section_ref: Optional[str]
    section_title: Optional[str]
    score: float
    metadata: Optional[Dict[str, Any]] = None


class BM25Retriever:
    """BM25-based full-text search using PostgreSQL tsvector"""
    
    def __init__(self):
        self.settings = get_settings()
        
    async def retrieve(
        self,
        query_text: str,
        document_id: str,
        user_id: str,
        limit: int = 20,
        min_score: float = 0.0
    ) -> List[BM25Result]:
        """
        Perform BM25 retrieval on document chunks
        
        Args:
            query_text: User's search query
            document_id: Document UUID to search within
            user_id: User UUID for RLS
            limit: Maximum number of results
            min_score: Minimum BM25 score threshold
            
        Returns:
            List of BM25Result objects sorted by relevance score
        """
        logger.info(
            "Starting BM25 retrieval",
            extra={
                "query_text": query_text,
                "document_id": document_id,
                "user_id": user_id,
                "limit": limit
            }
        )
        
        # Preprocess query for better search
        processed_query = self._preprocess_query(query_text)
        
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
                
                # Execute BM25 query using ts_rank_cd for better relevance scoring
                query = """
                    SELECT 
                        c.id as chunk_id,
                        c.content,
                        c.page_number,
                        c.section_ref,
                        c.section_title,
                        ts_rank_cd(
                            weights => '{0.1, 0.2, 0.4, 1.0}',
                            vector => c.tsv,
                            query => plainto_tsquery('simple', $1),
                            normalization => 32
                        ) as score,
                        c.token_count,
                        c.char_count
                    FROM public.chunks c
                    JOIN public.documents d ON d.id = c.document_id
                    WHERE d.id = $2
                        AND c.tsv @@ plainto_tsquery('simple', $1)
                        AND ts_rank_cd(c.tsv, plainto_tsquery('simple', $1)) >= $3
                    ORDER BY score DESC
                    LIMIT $4;
                """
                
                rows = await conn.fetch(
                    query,
                    processed_query,
                    document_id,
                    min_score,
                    limit
                )
                
                results = []
                for row in rows:
                    result = BM25Result(
                        chunk_id=row['chunk_id'],
                        content=row['content'],
                        page_number=row['page_number'],
                        section_ref=row['section_ref'],
                        section_title=row['section_title'],
                        score=float(row['score']),
                        metadata={
                            'token_count': row['token_count'],
                            'char_count': row['char_count'],
                            'method': 'bm25'
                        }
                    )
                    results.append(result)
                
                logger.info(
                    "BM25 retrieval completed",
                    extra={
                        "results_count": len(results),
                        "top_score": results[0].score if results else 0,
                        "document_id": document_id
                    }
                )
                
                return results
                
        except asyncpg.PostgreSQLError as e:
            logger.error(
                "BM25 retrieval database error",
                extra={
                    "error": str(e),
                    "query_text": query_text,
                    "document_id": document_id
                }
            )
            return []
        except Exception as e:
            logger.error(
                "BM25 retrieval unexpected error",
                extra={
                    "error": str(e),
                    "query_text": query_text,
                    "document_id": document_id
                },
                exc_info=True
            )
            return []
    
    def _preprocess_query(self, query_text: str) -> str:
        """
        Preprocess query text for better search results
        
        Args:
            query_text: Raw user query
            
        Returns:
            Processed query text
        """
        if not query_text:
            return ""
        
        # Convert to lowercase
        processed = query_text.lower().strip()
        
        # Remove extra whitespace
        processed = re.sub(r'\s+', ' ', processed)
        
        # Remove special characters that might interfere with tsquery
        processed = re.sub(r'[^\w\s-]', '', processed)
        
        # Handle common phrases and synonyms
        processed = self._expand_query_terms(processed)
        
        logger.debug(
            "Query preprocessing",
            extra={
                "original": query_text,
                "processed": processed
            }
        )
        
        return processed
    
    def _expand_query_terms(self, query: str) -> str:
        """
        Expand query with synonyms and related terms
        
        Args:
            query: Preprocessed query
            
        Returns:
            Expanded query with additional terms
        """
        # Common academic/technical synonyms
        expansions = {
            'ai': 'artificial intelligence',
            'ml': 'machine learning', 
            'nn': 'neural network',
            'dl': 'deep learning',
            'nlp': 'natural language processing',
            'cv': 'computer vision',
            'algo': 'algorithm',
            'db': 'database',
            'api': 'application programming interface'
        }
        
        # Expand common abbreviations
        words = query.split()
        expanded_words = []
        
        for word in words:
            expanded_words.append(word)
            if word in expansions:
                expanded_words.append(expansions[word])
        
        return ' '.join(expanded_words)
    
    async def get_query_stats(
        self,
        query_text: str,
        document_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get statistics about query performance
        
        Args:
            query_text: Search query
            document_id: Document UUID
            user_id: User UUID
            
        Returns:
            Dictionary with query statistics
        """
        processed_query = self._preprocess_query(query_text)
        
        pool = await get_db_pool()
        if not pool:
            return {"error": "Database not available"}
            
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    "SELECT set_config('request.jwt.claims', $1, true)",
                    f'{{"sub":"{user_id}"}}'
                )
                
                # Get query statistics
                stats_query = """
                    SELECT 
                        COUNT(*) as total_chunks,
                        COUNT(CASE WHEN c.tsv @@ plainto_tsquery('simple', $1) THEN 1 END) as matching_chunks,
                        AVG(ts_rank_cd(c.tsv, plainto_tsquery('simple', $1))) as avg_score,
                        MAX(ts_rank_cd(c.tsv, plainto_tsquery('simple', $1))) as max_score
                    FROM public.chunks c
                    JOIN public.documents d ON d.id = c.document_id
                    WHERE d.id = $2;
                """
                
                row = await conn.fetchrow(stats_query, processed_query, document_id)
                
                return {
                    "original_query": query_text,
                    "processed_query": processed_query,
                    "total_chunks": row['total_chunks'],
                    "matching_chunks": row['matching_chunks'],
                    "avg_score": float(row['avg_score'] or 0),
                    "max_score": float(row['max_score'] or 0),
                    "match_ratio": row['matching_chunks'] / max(row['total_chunks'], 1)
                }
                
        except Exception as e:
            logger.error(
                "Error getting BM25 query stats",
                extra={"error": str(e), "query": query_text}
            )
            return {"error": str(e)}


async def test_bm25_retrieval():
    """Test function for BM25 retrieval"""
    retriever = BM25Retriever()
    
    # Test with sample data
    results = await retriever.retrieve(
        query_text="machine learning algorithms",
        document_id="test-doc-123",
        user_id="test-user-123",
        limit=5
    )
    
    print(f"BM25 retrieval test: {len(results)} results")
    for result in results:
        print(f"Score: {result.score:.3f}, Content: {result.content[:100]}...")
    
    return results


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_bm25_retrieval())