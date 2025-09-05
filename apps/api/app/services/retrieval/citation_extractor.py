"""Citation extraction service for generating source references from retrieved chunks"""

import logging
import re
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict

from .hybrid_ranker import HybridResult

logger = logging.getLogger(__name__)


@dataclass
class Citation:
    """Citation data structure"""
    chunk_id: str
    page_number: Optional[int]
    section_ref: Optional[str]
    section_title: Optional[str]
    text_snippet: str
    relevance_score: float
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    highlighted_snippet: Optional[str] = None
    metadata: Optional[Dict[str, any]] = None


@dataclass 
class CitationGroup:
    """Group of citations from same source/section"""
    source_ref: str  # page or section identifier
    source_title: Optional[str]
    citations: List[Citation]
    combined_snippet: str
    total_relevance: float


class CitationExtractor:
    """Extract and format citations from retrieved document chunks"""
    
    def __init__(
        self, 
        max_snippet_length: int = 200,
        min_snippet_length: int = 50,
        highlight_padding: int = 20
    ):
        """
        Initialize citation extractor
        
        Args:
            max_snippet_length: Maximum length of citation snippets
            min_snippet_length: Minimum length of citation snippets
            highlight_padding: Characters to include around highlighted terms
        """
        self.max_snippet_length = max_snippet_length
        self.min_snippet_length = min_snippet_length
        self.highlight_padding = highlight_padding
    
    def extract_citations(
        self,
        query_text: str,
        hybrid_results: List[HybridResult],
        max_citations: int = 5,
        min_relevance: float = 0.1
    ) -> List[Citation]:
        """
        Extract citations from hybrid retrieval results
        
        Args:
            query_text: Original user query for highlighting
            hybrid_results: Results from hybrid ranking
            max_citations: Maximum number of citations to extract
            min_relevance: Minimum relevance score for inclusion
            
        Returns:
            List of Citation objects
        """
        logger.info(
            "Extracting citations",
            extra={
                "query_text": query_text,
                "results_count": len(hybrid_results),
                "max_citations": max_citations
            }
        )
        
        if not hybrid_results:
            return []
        
        citations = []
        query_terms = self._extract_query_terms(query_text)
        
        for result in hybrid_results:
            if len(citations) >= max_citations:
                break
                
            if result.hybrid_score < min_relevance:
                continue
            
            # Extract best snippet from content
            snippet, start_char, end_char = self._extract_snippet(
                result.content, query_terms
            )
            
            # Create highlighted version
            highlighted_snippet = self._highlight_terms(snippet, query_terms)
            
            citation = Citation(
                chunk_id=result.chunk_id,
                page_number=result.page_number,
                section_ref=result.section_ref,
                section_title=result.section_title,
                text_snippet=snippet,
                relevance_score=result.hybrid_score,
                start_char=start_char,
                end_char=end_char,
                highlighted_snippet=highlighted_snippet,
                metadata={
                    'bm25_score': result.bm25_score,
                    'vector_score': result.vector_score,
                    'query_term_matches': self._count_query_matches(snippet, query_terms),
                    'snippet_quality': self._assess_snippet_quality(snippet, query_terms)
                }
            )
            
            citations.append(citation)
        
        # Sort citations by relevance score (descending)
        citations.sort(key=lambda c: c.relevance_score, reverse=True)
        
        logger.info(
            "Citation extraction completed",
            extra={
                "citations_extracted": len(citations),
                "avg_relevance": sum(c.relevance_score for c in citations) / max(len(citations), 1),
                "unique_pages": len(set(c.page_number for c in citations if c.page_number))
            }
        )
        
        return citations[:max_citations]
    
    def group_citations(
        self, 
        citations: List[Citation],
        group_by: str = "page"  # "page", "section", or "source"
    ) -> List[CitationGroup]:
        """
        Group citations by page, section, or other criteria
        
        Args:
            citations: List of citations to group
            group_by: Grouping criteria ("page", "section", "source")
            
        Returns:
            List of CitationGroup objects
        """
        if not citations:
            return []
        
        groups = defaultdict(list)
        
        # Group citations based on criteria
        for citation in citations:
            if group_by == "page" and citation.page_number is not None:
                key = f"page_{citation.page_number}"
                groups[key].append(citation)
            elif group_by == "section" and citation.section_ref:
                key = f"section_{citation.section_ref}"
                groups[key].append(citation)
            elif group_by == "source":
                # Group by page if available, otherwise section
                if citation.page_number is not None:
                    key = f"page_{citation.page_number}"
                elif citation.section_ref:
                    key = f"section_{citation.section_ref}"
                else:
                    key = f"chunk_{citation.chunk_id}"
                groups[key].append(citation)
        
        # Create CitationGroup objects
        citation_groups = []
        for group_key, group_citations in groups.items():
            # Sort citations within group by relevance
            group_citations.sort(key=lambda c: c.relevance_score, reverse=True)
            
            # Combine snippets
            combined_snippet = self._combine_snippets(
                [c.text_snippet for c in group_citations]
            )
            
            # Calculate total relevance
            total_relevance = sum(c.relevance_score for c in group_citations)
            
            # Determine source title
            source_title = None
            for citation in group_citations:
                if citation.section_title:
                    source_title = citation.section_title
                    break
            
            citation_group = CitationGroup(
                source_ref=group_key,
                source_title=source_title,
                citations=group_citations,
                combined_snippet=combined_snippet,
                total_relevance=total_relevance
            )
            
            citation_groups.append(citation_group)
        
        # Sort groups by total relevance
        citation_groups.sort(key=lambda g: g.total_relevance, reverse=True)
        
        return citation_groups
    
    def _extract_query_terms(self, query_text: str) -> List[str]:
        """
        Extract meaningful terms from user query
        
        Args:
            query_text: User's search query
            
        Returns:
            List of query terms for matching
        """
        if not query_text:
            return []
        
        # Clean and split query
        cleaned = re.sub(r'[^\w\s-]', '', query_text.lower())
        terms = cleaned.split()
        
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'what', 'where', 'when', 'why', 'how'
        }
        
        meaningful_terms = [term for term in terms if len(term) > 2 and term not in stop_words]
        
        return meaningful_terms
    
    def _extract_snippet(
        self, 
        content: str, 
        query_terms: List[str]
    ) -> Tuple[str, Optional[int], Optional[int]]:
        """
        Extract the best snippet from content based on query terms
        
        Args:
            content: Full chunk content
            query_terms: Terms to look for
            
        Returns:
            Tuple of (snippet, start_char, end_char)
        """
        if not content:
            return "", None, None
        
        if not query_terms:
            # No query terms, just take beginning
            snippet = content[:self.max_snippet_length]
            if len(content) > self.max_snippet_length:
                snippet += "..."
            return snippet, 0, len(snippet)
        
        # Find best matching section
        best_start = 0
        best_score = 0
        content_lower = content.lower()
        
        # Sliding window to find best snippet
        window_size = self.max_snippet_length
        step_size = 50
        
        for start in range(0, len(content) - window_size + 1, step_size):
            window = content_lower[start:start + window_size]
            
            # Score this window based on query term matches
            score = 0
            for term in query_terms:
                matches = len(re.findall(re.escape(term), window))
                score += matches
            
            # Bonus for terms appearing close together
            if len(query_terms) > 1:
                for i, term1 in enumerate(query_terms):
                    for term2 in query_terms[i+1:]:
                        term1_pos = window.find(term1)
                        term2_pos = window.find(term2)
                        if term1_pos != -1 and term2_pos != -1:
                            distance = abs(term1_pos - term2_pos)
                            if distance < 100:  # Close proximity bonus
                                score += 0.5
            
            if score > best_score:
                best_score = score
                best_start = start
        
        # Extract snippet around best position
        end_pos = min(best_start + window_size, len(content))
        snippet = content[best_start:end_pos]
        
        # Clean up snippet boundaries (try to end at sentence/word boundaries)
        snippet = self._clean_snippet_boundaries(snippet, is_start=best_start > 0)
        
        return snippet, best_start, best_start + len(snippet)
    
    def _clean_snippet_boundaries(self, snippet: str, is_start: bool = False) -> str:
        """
        Clean snippet to end at natural boundaries
        
        Args:
            snippet: Raw snippet text
            is_start: Whether this snippet starts mid-document
            
        Returns:
            Cleaned snippet
        """
        if not snippet:
            return snippet
        
        # Add ellipsis at start if needed
        if is_start and not snippet[0].isupper():
            snippet = "..." + snippet
        
        # Try to end at sentence boundary
        last_sentence = snippet.rfind('.')
        last_exclamation = snippet.rfind('!')
        last_question = snippet.rfind('?')
        
        sentence_end = max(last_sentence, last_exclamation, last_question)
        
        if sentence_end > len(snippet) * 0.7:  # If sentence end is reasonably far
            snippet = snippet[:sentence_end + 1]
        else:
            # Try to end at word boundary
            if len(snippet) >= self.max_snippet_length:
                last_space = snippet.rfind(' ', 0, self.max_snippet_length - 3)
                if last_space > len(snippet) * 0.8:
                    snippet = snippet[:last_space] + "..."
                else:
                    snippet = snippet[:self.max_snippet_length - 3] + "..."
        
        return snippet
    
    def _highlight_terms(self, snippet: str, query_terms: List[str]) -> str:
        """
        Highlight query terms in snippet
        
        Args:
            snippet: Text snippet to highlight
            query_terms: Terms to highlight
            
        Returns:
            Snippet with highlighted terms
        """
        if not query_terms:
            return snippet
        
        highlighted = snippet
        
        # Sort terms by length (longest first) to avoid partial replacements
        sorted_terms = sorted(query_terms, key=len, reverse=True)
        
        for term in sorted_terms:
            # Use case-insensitive replacement with word boundaries
            pattern = r'\b' + re.escape(term) + r'\b'
            highlighted = re.sub(
                pattern, 
                f'**{term}**',
                highlighted,
                flags=re.IGNORECASE
            )
        
        return highlighted
    
    def _count_query_matches(self, snippet: str, query_terms: List[str]) -> int:
        """Count how many query terms appear in snippet"""
        snippet_lower = snippet.lower()
        matches = 0
        
        for term in query_terms:
            if term in snippet_lower:
                matches += snippet_lower.count(term)
        
        return matches
    
    def _assess_snippet_quality(self, snippet: str, query_terms: List[str]) -> float:
        """
        Assess the quality of a snippet for citation purposes
        
        Args:
            snippet: Text snippet
            query_terms: Query terms
            
        Returns:
            Quality score (0-1)
        """
        if not snippet:
            return 0.0
        
        quality = 0.0
        
        # Length factor (prefer medium-length snippets)
        length_factor = min(len(snippet) / self.max_snippet_length, 1.0)
        if length_factor > 0.3:  # Not too short
            quality += 0.2
        
        # Query term coverage
        if query_terms:
            snippet_lower = snippet.lower()
            matching_terms = sum(1 for term in query_terms if term in snippet_lower)
            coverage = matching_terms / len(query_terms)
            quality += 0.4 * coverage
        
        # Sentence completeness (ends with punctuation)
        if snippet.strip().endswith(('.', '!', '?', '..."')):
            quality += 0.2
        
        # Readability (not too fragmented)
        sentences = snippet.count('.') + snippet.count('!') + snippet.count('?')
        if sentences >= 1:  # At least one complete thought
            quality += 0.2
        
        return min(quality, 1.0)
    
    def _combine_snippets(self, snippets: List[str]) -> str:
        """
        Combine multiple snippets into a coherent text
        
        Args:
            snippets: List of text snippets to combine
            
        Returns:
            Combined snippet text
        """
        if not snippets:
            return ""
        
        if len(snippets) == 1:
            return snippets[0]
        
        # Remove duplicates while preserving order
        unique_snippets = []
        seen = set()
        
        for snippet in snippets:
            snippet_clean = snippet.strip().lower()
            if snippet_clean not in seen and len(snippet_clean) > 10:
                unique_snippets.append(snippet)
                seen.add(snippet_clean)
        
        # Combine with appropriate separators
        combined = ""
        for i, snippet in enumerate(unique_snippets):
            if i > 0:
                combined += " ... "
            combined += snippet.strip()
        
        # Limit combined length
        if len(combined) > self.max_snippet_length * 2:
            combined = combined[:self.max_snippet_length * 2 - 3] + "..."
        
        return combined
    
    def format_citation_apa(self, citation: Citation, document_title: str = "") -> str:
        """
        Format citation in APA style
        
        Args:
            citation: Citation to format
            document_title: Title of the source document
            
        Returns:
            APA-formatted citation string
        """
        citation_parts = []
        
        if document_title:
            citation_parts.append(document_title)
        
        if citation.section_title:
            citation_parts.append(citation.section_title)
        
        if citation.page_number:
            citation_parts.append(f"p. {citation.page_number}")
        
        formatted = ", ".join(citation_parts)
        
        return formatted
    
    def format_citation_json(self, citation: Citation) -> Dict[str, any]:
        """
        Format citation as JSON object
        
        Args:
            citation: Citation to format
            
        Returns:
            Citation data as dictionary
        """
        return {
            "chunkId": citation.chunk_id,
            "page": citation.page_number,
            "section": citation.section_ref,
            "sectionTitle": citation.section_title,
            "textSnippet": citation.text_snippet,
            "relevanceScore": citation.relevance_score,
            "highlightedSnippet": citation.highlighted_snippet,
            "metadata": citation.metadata
        }


async def test_citation_extraction():
    """Test function for citation extraction"""
    from .hybrid_ranker import HybridResult
    
    # Create mock hybrid results
    results = [
        HybridResult(
            chunk_id="chunk1",
            content="Machine learning algorithms are computational procedures that enable computers to learn and make decisions from data. They form the foundation of artificial intelligence applications.",
            page_number=15,
            section_ref="ch2",
            section_title="Introduction to ML",
            hybrid_score=0.95,
            bm25_score=0.8,
            vector_score=0.9,
            rank_bm25=1,
            rank_vector=1,
            metadata={}
        ),
        HybridResult(
            chunk_id="chunk2", 
            content="Neural networks are inspired by biological neural systems and consist of interconnected nodes that process information. They are particularly effective for pattern recognition tasks.",
            page_number=23,
            section_ref="ch3",
            section_title="Neural Networks",
            hybrid_score=0.87,
            bm25_score=0.7,
            vector_score=0.95,
            rank_bm25=2,
            rank_vector=1,
            metadata={}
        )
    ]
    
    extractor = CitationExtractor()
    citations = extractor.extract_citations("machine learning algorithms", results)
    
    print(f"Citation extraction test: {len(citations)} citations")
    for citation in citations:
        print(f"Score: {citation.relevance_score:.3f}")
        print(f"Snippet: {citation.highlighted_snippet}")
        print(f"Source: Page {citation.page_number}, {citation.section_title}")
        print("---")
    
    return citations


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_citation_extraction())