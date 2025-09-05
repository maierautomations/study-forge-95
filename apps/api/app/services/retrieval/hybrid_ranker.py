"""Hybrid ranking algorithm that combines BM25 and Vector retrieval results"""

import logging
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from collections import defaultdict
import math

from .bm25_retrieval import BM25Result
from .vector_retrieval import VectorResult
from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class HybridResult:
    """Combined result from hybrid ranking"""
    chunk_id: str
    content: str
    page_number: Optional[int]
    section_ref: Optional[str]
    section_title: Optional[str]
    hybrid_score: float
    bm25_score: Optional[float]
    vector_score: Optional[float]
    rank_bm25: Optional[int]
    rank_vector: Optional[int]
    metadata: Dict[str, any]


class HybridRanker:
    """Hybrid ranking system combining BM25 and vector search results"""
    
    def __init__(self, bm25_weight: float = 0.4, vector_weight: float = 0.6):
        """
        Initialize hybrid ranker
        
        Args:
            bm25_weight: Weight for BM25 scores (default: 0.4)
            vector_weight: Weight for vector scores (default: 0.6)
        """
        self.settings = get_settings()
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        
        # Ensure weights sum to 1.0
        total_weight = bm25_weight + vector_weight
        if abs(total_weight - 1.0) > 0.001:
            logger.warning(
                "Weights don't sum to 1.0, normalizing",
                extra={
                    "bm25_weight": bm25_weight,
                    "vector_weight": vector_weight,
                    "total": total_weight
                }
            )
            self.bm25_weight = bm25_weight / total_weight
            self.vector_weight = vector_weight / total_weight
    
    def rank(
        self,
        bm25_results: List[BM25Result],
        vector_results: List[VectorResult],
        limit: int = 10,
        diversity_factor: float = 0.1
    ) -> List[HybridResult]:
        """
        Combine and rank BM25 and vector results using hybrid scoring
        
        Args:
            bm25_results: Results from BM25 retrieval
            vector_results: Results from vector retrieval  
            limit: Maximum number of results to return
            diversity_factor: Factor to promote diversity in results (0-1)
            
        Returns:
            List of HybridResult objects sorted by hybrid score
        """
        logger.info(
            "Starting hybrid ranking",
            extra={
                "bm25_count": len(bm25_results),
                "vector_count": len(vector_results),
                "limit": limit,
                "bm25_weight": self.bm25_weight,
                "vector_weight": self.vector_weight
            }
        )
        
        if not bm25_results and not vector_results:
            return []
        
        # Normalize scores for fair combination
        normalized_bm25 = self._normalize_bm25_scores(bm25_results)
        normalized_vector = self._normalize_vector_scores(vector_results)
        
        # Create lookup maps
        bm25_map = {r.chunk_id: (r, score, rank) for rank, (r, score) in enumerate(normalized_bm25)}
        vector_map = {r.chunk_id: (r, score, rank) for rank, (r, score) in enumerate(normalized_vector)}
        
        # Get all unique chunk IDs
        all_chunk_ids = set(bm25_map.keys()) | set(vector_map.keys())
        
        hybrid_results = []
        
        for chunk_id in all_chunk_ids:
            # Get scores from both methods (0 if not found)
            bm25_data = bm25_map.get(chunk_id)
            vector_data = vector_map.get(chunk_id)
            
            if bm25_data:
                bm25_result, bm25_norm_score, bm25_rank = bm25_data
                bm25_raw_score = bm25_result.score
            else:
                bm25_result, bm25_norm_score, bm25_rank = None, 0.0, None
                bm25_raw_score = None
            
            if vector_data:
                vector_result, vector_norm_score, vector_rank = vector_data
                vector_raw_score = vector_result.similarity_score
            else:
                vector_result, vector_norm_score, vector_rank = None, 0.0, None
                vector_raw_score = None
            
            # Calculate hybrid score
            hybrid_score = (
                self.bm25_weight * bm25_norm_score +
                self.vector_weight * vector_norm_score
            )
            
            # Apply reciprocal rank fusion (RRF) component
            rrf_score = self._calculate_rrf_score(bm25_rank, vector_rank)
            
            # Combine weighted score with RRF
            final_score = 0.8 * hybrid_score + 0.2 * rrf_score
            
            # Use content from available result (prefer BM25 for full content)
            source_result = bm25_result if bm25_result else vector_result
            
            hybrid_result = HybridResult(
                chunk_id=chunk_id,
                content=source_result.content,
                page_number=source_result.page_number,
                section_ref=source_result.section_ref,
                section_title=source_result.section_title,
                hybrid_score=final_score,
                bm25_score=bm25_raw_score,
                vector_score=vector_raw_score,
                rank_bm25=bm25_rank + 1 if bm25_rank is not None else None,
                rank_vector=vector_rank + 1 if vector_rank is not None else None,
                metadata={
                    'bm25_normalized': bm25_norm_score,
                    'vector_normalized': vector_norm_score,
                    'rrf_score': rrf_score,
                    'method': 'hybrid',
                    'weights': {
                        'bm25': self.bm25_weight,
                        'vector': self.vector_weight
                    }
                }
            )
            
            hybrid_results.append(hybrid_result)
        
        # Sort by hybrid score (descending)
        hybrid_results.sort(key=lambda x: x.hybrid_score, reverse=True)
        
        # Apply diversity filtering if requested
        if diversity_factor > 0:
            hybrid_results = self._apply_diversity_filter(
                hybrid_results, diversity_factor
            )
        
        # Limit results
        final_results = hybrid_results[:limit]
        
        logger.info(
            "Hybrid ranking completed",
            extra={
                "final_count": len(final_results),
                "top_score": final_results[0].hybrid_score if final_results else 0,
                "bm25_only": sum(1 for r in final_results if r.vector_score is None),
                "vector_only": sum(1 for r in final_results if r.bm25_score is None),
                "both_methods": sum(1 for r in final_results if r.bm25_score is not None and r.vector_score is not None)
            }
        )
        
        return final_results
    
    def _normalize_bm25_scores(self, results: List[BM25Result]) -> List[Tuple[BM25Result, float]]:
        """
        Normalize BM25 scores to 0-1 range
        
        Args:
            results: BM25 results to normalize
            
        Returns:
            List of (result, normalized_score) tuples
        """
        if not results:
            return []
        
        scores = [r.score for r in results]
        max_score = max(scores)
        min_score = min(scores)
        
        # Avoid division by zero
        if max_score == min_score:
            return [(r, 1.0) for r in results]
        
        # Min-max normalization
        normalized = []
        for result in results:
            norm_score = (result.score - min_score) / (max_score - min_score)
            normalized.append((result, norm_score))
        
        return normalized
    
    def _normalize_vector_scores(self, results: List[VectorResult]) -> List[Tuple[VectorResult, float]]:
        """
        Normalize vector similarity scores
        
        Args:
            results: Vector results to normalize
            
        Returns:
            List of (result, normalized_score) tuples
        """
        if not results:
            return []
        
        # Vector scores are already 0-1 (cosine similarity)
        # but we still normalize to handle edge cases
        scores = [r.similarity_score for r in results]
        max_score = max(scores)
        min_score = min(scores)
        
        if max_score == min_score:
            return [(r, 1.0) for r in results]
        
        normalized = []
        for result in results:
            # Ensure scores are in 0-1 range
            norm_score = max(0.0, min(1.0, result.similarity_score))
            normalized.append((result, norm_score))
        
        return normalized
    
    def _calculate_rrf_score(
        self, 
        bm25_rank: Optional[int], 
        vector_rank: Optional[int], 
        k: int = 60
    ) -> float:
        """
        Calculate Reciprocal Rank Fusion (RRF) score
        
        Args:
            bm25_rank: Rank in BM25 results (0-based, None if not present)
            vector_rank: Rank in vector results (0-based, None if not present)
            k: RRF constant (default: 60)
            
        Returns:
            RRF score
        """
        rrf_score = 0.0
        
        if bm25_rank is not None:
            rrf_score += 1.0 / (k + bm25_rank + 1)
        
        if vector_rank is not None:
            rrf_score += 1.0 / (k + vector_rank + 1)
        
        return rrf_score
    
    def _apply_diversity_filter(
        self, 
        results: List[HybridResult], 
        diversity_factor: float
    ) -> List[HybridResult]:
        """
        Apply diversity filtering to reduce redundant results
        
        Args:
            results: Sorted hybrid results
            diversity_factor: Strength of diversity filtering (0-1)
            
        Returns:
            Filtered results with diversity applied
        """
        if diversity_factor <= 0 or len(results) <= 1:
            return results
        
        filtered_results = []
        seen_sections: Dict[str, int] = defaultdict(int)
        seen_pages: Dict[int, int] = defaultdict(int)
        
        for result in results:
            # Calculate diversity penalty
            diversity_penalty = 0.0
            
            # Penalize if we've seen this section before
            if result.section_ref:
                section_count = seen_sections[result.section_ref]
                diversity_penalty += diversity_factor * section_count * 0.1
            
            # Penalize if we've seen this page before  
            if result.page_number is not None:
                page_count = seen_pages[result.page_number]
                diversity_penalty += diversity_factor * page_count * 0.05
            
            # Apply penalty to score
            adjusted_score = result.hybrid_score * (1.0 - diversity_penalty)
            
            # Update metadata with diversity info
            result.metadata['diversity_penalty'] = diversity_penalty
            result.metadata['adjusted_score'] = adjusted_score
            
            filtered_results.append(result)
            
            # Update counters
            if result.section_ref:
                seen_sections[result.section_ref] += 1
            if result.page_number is not None:
                seen_pages[result.page_number] += 1
        
        # Re-sort by adjusted scores if diversity was applied
        if diversity_factor > 0:
            filtered_results.sort(
                key=lambda x: x.metadata.get('adjusted_score', x.hybrid_score), 
                reverse=True
            )
        
        return filtered_results
    
    def get_ranking_explanation(self, results: List[HybridResult]) -> Dict[str, any]:
        """
        Generate explanation of ranking decisions
        
        Args:
            results: Hybrid ranking results
            
        Returns:
            Dictionary with ranking explanation
        """
        if not results:
            return {"message": "No results to explain"}
        
        explanation = {
            "hybrid_weights": {
                "bm25": self.bm25_weight,
                "vector": self.vector_weight
            },
            "result_count": len(results),
            "top_result_analysis": {},
            "method_coverage": {
                "bm25_only": 0,
                "vector_only": 0,
                "both_methods": 0
            },
            "score_distribution": {
                "max_hybrid": 0.0,
                "min_hybrid": 1.0,
                "avg_hybrid": 0.0
            }
        }
        
        # Analyze method coverage
        for result in results:
            if result.bm25_score is not None and result.vector_score is not None:
                explanation["method_coverage"]["both_methods"] += 1
            elif result.bm25_score is not None:
                explanation["method_coverage"]["bm25_only"] += 1
            else:
                explanation["method_coverage"]["vector_only"] += 1
        
        # Analyze score distribution
        hybrid_scores = [r.hybrid_score for r in results]
        explanation["score_distribution"]["max_hybrid"] = max(hybrid_scores)
        explanation["score_distribution"]["min_hybrid"] = min(hybrid_scores)
        explanation["score_distribution"]["avg_hybrid"] = sum(hybrid_scores) / len(hybrid_scores)
        
        # Analyze top result
        top_result = results[0]
        explanation["top_result_analysis"] = {
            "chunk_id": top_result.chunk_id,
            "hybrid_score": top_result.hybrid_score,
            "bm25_contribution": (top_result.metadata.get('bm25_normalized', 0) * self.bm25_weight),
            "vector_contribution": (top_result.metadata.get('vector_normalized', 0) * self.vector_weight),
            "rrf_score": top_result.metadata.get('rrf_score', 0),
            "has_bm25": top_result.bm25_score is not None,
            "has_vector": top_result.vector_score is not None
        }
        
        return explanation


async def test_hybrid_ranking():
    """Test function for hybrid ranking"""
    from .bm25_retrieval import BM25Result
    from .vector_retrieval import VectorResult
    
    # Create mock results
    bm25_results = [
        BM25Result("chunk1", "Content about machine learning", 1, "intro", "Introduction", 0.8),
        BM25Result("chunk2", "Neural networks explained", 2, "ch1", "Chapter 1", 0.6),
        BM25Result("chunk3", "Deep learning concepts", 3, "ch2", "Chapter 2", 0.4)
    ]
    
    vector_results = [
        VectorResult("chunk2", "Neural networks explained", 2, "ch1", "Chapter 1", 0.9),
        VectorResult("chunk4", "AI algorithms overview", 4, "ch3", "Chapter 3", 0.7),
        VectorResult("chunk1", "Content about machine learning", 1, "intro", "Introduction", 0.6)
    ]
    
    ranker = HybridRanker()
    results = ranker.rank(bm25_results, vector_results, limit=5)
    
    print(f"Hybrid ranking test: {len(results)} results")
    for i, result in enumerate(results, 1):
        print(f"{i}. Score: {result.hybrid_score:.3f} | BM25: {result.bm25_score} | Vector: {result.vector_score}")
        print(f"   Content: {result.content[:50]}...")
    
    # Get explanation
    explanation = ranker.get_ranking_explanation(results)
    print(f"\nRanking explanation: {explanation}")
    
    return results


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_hybrid_ranking())