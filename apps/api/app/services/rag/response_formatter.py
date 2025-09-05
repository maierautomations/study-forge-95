"""Response formatter for RAG system outputs"""

import logging
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from app.services.retrieval.citation_extractor import Citation

logger = logging.getLogger(__name__)


class ResponseFormatter:
    """Format and enhance RAG responses"""
    
    def __init__(
        self,
        citation_style: str = "numbered",
        include_confidence: bool = True
    ):
        """
        Initialize response formatter
        
        Args:
            citation_style: Citation format ("numbered", "inline", "footnote")
            include_confidence: Whether to include confidence indicators
        """
        self.citation_style = citation_style
        self.include_confidence = include_confidence
    
    def format_answer(
        self,
        raw_answer: str,
        citations: List[Citation],
        confidence_score: Optional[float] = None
    ) -> str:
        """
        Format the raw LLM answer with proper citations and enhancements
        
        Args:
            raw_answer: Raw answer from LLM
            citations: List of citations to reference
            confidence_score: Overall confidence in the answer (0-1)
            
        Returns:
            Formatted answer with proper citations
        """
        if not raw_answer:
            return "I apologize, but I couldn't generate a proper answer to your question."
        
        logger.debug(
            "Formatting answer",
            extra={
                "raw_length": len(raw_answer),
                "citations_count": len(citations),
                "confidence": confidence_score
            }
        )
        
        # Clean up the raw answer
        formatted_answer = self._clean_answer(raw_answer)
        
        # Validate and fix citations
        formatted_answer = self._validate_citations(formatted_answer, citations)
        
        # Add confidence indicator if requested
        if self.include_confidence and confidence_score is not None:
            formatted_answer = self._add_confidence_indicator(
                formatted_answer, confidence_score
            )
        
        # Add citation list if using footnote style
        if self.citation_style == "footnote":
            formatted_answer = self._add_citation_footnotes(
                formatted_answer, citations
            )
        
        logger.debug(
            "Answer formatting completed",
            extra={
                "formatted_length": len(formatted_answer),
                "citation_references": len(re.findall(r'\[Citation \d+\]', formatted_answer))
            }
        )
        
        return formatted_answer
    
    def _clean_answer(self, raw_answer: str) -> str:
        """
        Clean up the raw answer text
        
        Args:
            raw_answer: Raw answer from LLM
            
        Returns:
            Cleaned answer text
        """
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', raw_answer.strip())
        
        # Fix common formatting issues
        cleaned = re.sub(r'\s+([.,!?;:])', r'\1', cleaned)  # Fix spacing before punctuation
        cleaned = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', cleaned)  # Fix sentence spacing
        
        # Ensure proper paragraph breaks
        cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
        
        # Remove any accidentally duplicated citations
        cleaned = re.sub(r'(\[Citation \d+\])\s*\1+', r'\1', cleaned)
        
        return cleaned
    
    def _validate_citations(self, answer: str, citations: List[Citation]) -> str:
        """
        Validate citation references in the answer
        
        Args:
            answer: Answer text with citation references
            citations: Available citations
            
        Returns:
            Answer with validated citations
        """
        if not citations:
            # Remove any citation references if no citations available
            return re.sub(r'\[Citation \d+\]', '', answer)
        
        # Find all citation references in the answer
        citation_refs = re.findall(r'\[Citation (\d+)\]', answer)
        valid_citations = set(str(i) for i in range(1, len(citations) + 1))
        
        # Replace invalid citation numbers
        for ref in set(citation_refs):
            if ref not in valid_citations:
                # Find the closest valid citation number
                closest = min(valid_citations, key=lambda x: abs(int(x) - int(ref)))
                answer = answer.replace(f'[Citation {ref}]', f'[Citation {closest}]')
                
                logger.warning(
                    "Fixed invalid citation reference",
                    extra={
                        "invalid_ref": ref,
                        "replaced_with": closest
                    }
                )
        
        return answer
    
    def _add_confidence_indicator(
        self, 
        answer: str, 
        confidence: float
    ) -> str:
        """
        Add confidence indicator to the answer
        
        Args:
            answer: Formatted answer
            confidence: Confidence score (0-1)
            
        Returns:
            Answer with confidence indicator
        """
        if confidence >= 0.9:
            indicator = "💡 **High confidence** - This answer is based on strong evidence from the document."
        elif confidence >= 0.7:
            indicator = "✓ **Medium confidence** - This answer is well-supported by the available information."
        elif confidence >= 0.5:
            indicator = "⚠️ **Moderate confidence** - This answer is based on limited information in the document."
        else:
            indicator = "❓ **Low confidence** - This answer may be incomplete due to limited relevant information."
        
        return f"{answer}\n\n*{indicator}*"
    
    def _add_citation_footnotes(
        self, 
        answer: str, 
        citations: List[Citation]
    ) -> str:
        """
        Add footnote-style citations to the answer
        
        Args:
            answer: Answer with citation references
            citations: List of citations
            
        Returns:
            Answer with footnote section
        """
        if not citations:
            return answer
        
        footnotes = ["\n\n**Sources:**"]
        
        for i, citation in enumerate(citations, 1):
            footnote = f"{i}. "
            
            # Add page reference
            if citation.page_number:
                footnote += f"Page {citation.page_number}"
                
            # Add section reference
            if citation.section_title:
                if citation.page_number:
                    footnote += f", {citation.section_title}"
                else:
                    footnote += citation.section_title
            
            # Add snippet if available
            if citation.text_snippet:
                snippet = citation.text_snippet
                if len(snippet) > 150:
                    snippet = snippet[:147] + "..."
                footnote += f": \"{snippet}\""
            
            footnotes.append(footnote)
        
        return answer + "\n".join(footnotes)
    
    def format_streaming_chunk(
        self,
        chunk: str,
        chunk_type: str = "content",
        metadata: Optional[Dict[str, any]] = None
    ) -> Dict[str, any]:
        """
        Format a streaming response chunk
        
        Args:
            chunk: Text chunk from streaming response
            chunk_type: Type of chunk ("content", "citation", "status")
            metadata: Additional metadata
            
        Returns:
            Formatted streaming chunk
        """
        return {
            "type": chunk_type,
            "content": chunk,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
    
    def format_error_response(
        self,
        error_message: str,
        error_type: str = "general",
        suggestions: Optional[List[str]] = None
    ) -> str:
        """
        Format error responses in a user-friendly way
        
        Args:
            error_message: Raw error message
            error_type: Type of error
            suggestions: Suggested next steps
            
        Returns:
            User-friendly error message
        """
        error_templates = {
            "no_context": "I couldn't find relevant information in the document to answer your question.",
            "generation_failed": "I encountered an issue while generating the answer.",
            "retrieval_failed": "I had trouble finding relevant information in the document.",
            "general": "I encountered an issue while processing your question."
        }
        
        base_message = error_templates.get(error_type, error_message)
        
        # Add suggestions if provided
        if suggestions:
            suggestion_text = "\n\nHere are some things you could try:\n"
            for suggestion in suggestions:
                suggestion_text += f"• {suggestion}\n"
            base_message += suggestion_text
        
        return base_message
    
    def format_no_results_response(
        self,
        question: str,
        document_title: Optional[str] = None
    ) -> str:
        """
        Format response when no relevant results are found
        
        Args:
            question: Original user question
            document_title: Title of searched document
            
        Returns:
            Helpful no-results message
        """
        base_message = "I couldn't find information directly relevant to your question"
        
        if document_title:
            base_message += f" in '{document_title}'"
        else:
            base_message += " in the document"
        
        suggestions = [
            "Try rephrasing your question with different keywords",
            "Check if your question relates to topics covered in the document",
            "Ask about specific concepts or sections mentioned in the document",
            "Try a broader or more general version of your question"
        ]
        
        return self.format_error_response(
            base_message,
            "no_context",
            suggestions
        )
    
    def extract_key_points(self, answer: str) -> List[str]:
        """
        Extract key points from a formatted answer
        
        Args:
            answer: Formatted answer text
            
        Returns:
            List of key points
        """
        # Look for numbered lists, bullet points, or clear statements
        key_points = []
        
        # Extract numbered points
        numbered_points = re.findall(r'^\d+\.\s*([^.]*\.)', answer, re.MULTILINE)
        key_points.extend(numbered_points)
        
        # Extract bullet points
        bullet_points = re.findall(r'^[•\-*]\s*([^.]*\.)', answer, re.MULTILINE)
        key_points.extend(bullet_points)
        
        # If no structured points, extract sentences with high information content
        if not key_points:
            sentences = re.split(r'[.!?]+', answer)
            key_points = [
                s.strip() + '.' for s in sentences 
                if len(s.strip()) > 20 and len(s.strip()) < 200
            ][:3]  # Top 3 sentences
        
        return [point.strip() for point in key_points if point.strip()]
    
    def add_related_questions(
        self,
        answer: str,
        citations: List[Citation],
        original_question: str
    ) -> str:
        """
        Add suggested related questions based on the answer and citations
        
        Args:
            answer: Formatted answer
            citations: Citations used in answer
            original_question: Original user question
            
        Returns:
            Answer with related questions section
        """
        if not citations:
            return answer
        
        # Generate related questions based on citation content
        related_questions = []
        
        # Extract topics from citations
        topics = set()
        for citation in citations:
            if citation.section_title:
                topics.add(citation.section_title)
        
        # Generate question templates
        question_templates = [
            "What else is mentioned about {}?",
            "How does {} relate to other concepts?",
            "Can you explain more about {}?",
            "What are the details of {}?"
        ]
        
        for topic in list(topics)[:2]:  # Limit to 2 topics
            for template in question_templates[:2]:  # 2 questions per topic
                related_questions.append(template.format(topic.lower()))
        
        if related_questions:
            related_section = "\n\n**You might also want to ask:**\n"
            for i, question in enumerate(related_questions[:3], 1):  # Max 3 questions
                related_section += f"{i}. {question}\n"
            
            return answer + related_section
        
        return answer


def test_response_formatter():
    """Test function for response formatter"""
    from app.services.retrieval.citation_extractor import Citation
    
    # Create test citations
    citations = [
        Citation(
            chunk_id="chunk1",
            page_number=15,
            section_ref="ch2", 
            section_title="Machine Learning Basics",
            text_snippet="Machine learning algorithms enable computers to learn from data without explicit programming.",
            relevance_score=0.9
        ),
        Citation(
            chunk_id="chunk2",
            page_number=23,
            section_ref="ch3",
            section_title="Neural Networks",
            text_snippet="Neural networks consist of interconnected nodes that process information in layers.",
            relevance_score=0.8
        )
    ]
    
    # Test raw answer
    raw_answer = "Machine learning is a powerful approach [Citation 1] that uses algorithms to find patterns in data. Neural networks [Citation 2] are one popular type of machine learning model."
    
    formatter = ResponseFormatter(citation_style="footnote")
    formatted_answer = formatter.format_answer(
        raw_answer, citations, confidence_score=0.85
    )
    
    print("Response Formatter Test:")
    print(formatted_answer)
    print("\n" + "="*50)
    
    # Test key points extraction
    key_points = formatter.extract_key_points(formatted_answer)
    print("Key Points:")
    for point in key_points:
        print(f"• {point}")
    
    return formatted_answer


if __name__ == "__main__":
    test_response_formatter()