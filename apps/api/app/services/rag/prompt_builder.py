"""Prompt builder for RAG system"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

from app.services.retrieval.citation_extractor import Citation

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Build optimized prompts for RAG queries"""
    
    def __init__(
        self,
        max_context_length: int = 4000,
        citation_style: str = "numbered"
    ):
        """
        Initialize prompt builder
        
        Args:
            max_context_length: Maximum characters for context
            citation_style: Style for citations ("numbered", "apa", "simple")
        """
        self.max_context_length = max_context_length
        self.citation_style = citation_style
    
    def build_rag_prompt(
        self,
        question: str,
        chunks: List[str],
        citations: List[Citation],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        document_title: Optional[str] = None
    ) -> str:
        """
        Build a comprehensive RAG prompt
        
        Args:
            question: User's question
            chunks: Retrieved text chunks
            citations: Citation objects for reference
            conversation_history: Previous conversation turns
            document_title: Title of the source document
            
        Returns:
            Formatted prompt for LLM
        """
        logger.debug(
            "Building RAG prompt",
            extra={
                "question_length": len(question),
                "chunks_count": len(chunks),
                "citations_count": len(citations)
            }
        )
        
        # Build prompt sections
        system_section = self._build_system_section()
        context_section = self._build_context_section(chunks, citations, document_title)
        history_section = self._build_history_section(conversation_history)
        question_section = self._build_question_section(question)
        instruction_section = self._build_instruction_section()
        
        # Combine sections
        full_prompt = "\n\n".join(filter(None, [
            system_section,
            context_section,
            history_section,
            question_section,
            instruction_section
        ]))
        
        # Truncate if too long
        if len(full_prompt) > self.max_context_length:
            full_prompt = self._truncate_prompt(full_prompt)
        
        logger.debug(
            "RAG prompt built",
            extra={
                "prompt_length": len(full_prompt),
                "sections": ["system", "context", "history", "question", "instruction"]
            }
        )
        
        return full_prompt
    
    def _build_system_section(self) -> str:
        """Build system instruction section"""
        return """You are an AI assistant that helps users understand documents by providing accurate, helpful answers based on the provided context. Your responses should be:

1. **Accurate**: Only use information from the provided context
2. **Cited**: Always reference your sources using the provided citations  
3. **Comprehensive**: Provide thorough answers when the context allows
4. **Clear**: Use clear, concise language appropriate for the user's question
5. **Honest**: If the context doesn't contain enough information, say so

When citing sources, use the format [Citation X] where X is the citation number provided."""
    
    def _build_context_section(
        self,
        chunks: List[str],
        citations: List[Citation],
        document_title: Optional[str]
    ) -> str:
        """Build context section with chunks and citations"""
        if not chunks:
            return "CONTEXT: No relevant context provided."
        
        context_parts = ["CONTEXT:"]
        
        if document_title:
            context_parts.append(f"Document: {document_title}")
            context_parts.append("")
        
        # Add numbered citations with their content
        for i, (chunk, citation) in enumerate(zip(chunks, citations), 1):
            citation_header = f"[Citation {i}]"
            
            # Add citation metadata
            if citation.page_number:
                citation_header += f" (Page {citation.page_number})"
            if citation.section_title:
                citation_header += f" - {citation.section_title}"
            
            context_parts.append(citation_header)
            context_parts.append(chunk.strip())
            context_parts.append("")  # Empty line between citations
        
        return "\n".join(context_parts)
    
    def _build_history_section(
        self,
        conversation_history: Optional[List[Dict[str, str]]]
    ) -> Optional[str]:
        """Build conversation history section"""
        if not conversation_history:
            return None
        
        history_parts = ["CONVERSATION HISTORY:"]
        
        for turn in conversation_history[-3:]:  # Last 3 turns only
            role = turn.get("role", "user")
            content = turn.get("content", "")
            
            if role == "user":
                history_parts.append(f"User: {content}")
            elif role == "assistant":
                history_parts.append(f"Assistant: {content}")
        
        history_parts.append("")  # Empty line
        return "\n".join(history_parts)
    
    def _build_question_section(self, question: str) -> str:
        """Build current question section"""
        return f"CURRENT QUESTION: {question}"
    
    def _build_instruction_section(self) -> str:
        """Build instruction section"""
        return """INSTRUCTIONS:
Based on the provided context and conversation history, answer the current question. Follow these guidelines:

1. Use ONLY information from the provided context - do not add outside knowledge
2. Cite your sources using [Citation X] format when referencing specific information  
3. If the context doesn't contain enough information to fully answer the question, explain what's missing
4. Provide a clear, well-structured response
5. If the question asks for something not covered in the context, politely explain this limitation

ANSWER:"""
    
    def _truncate_prompt(self, prompt: str) -> str:
        """
        Truncate prompt to fit within context length limits
        
        Args:
            prompt: Original prompt
            
        Returns:
            Truncated prompt
        """
        if len(prompt) <= self.max_context_length:
            return prompt
        
        logger.warning(
            "Truncating prompt due to length",
            extra={
                "original_length": len(prompt),
                "max_length": self.max_context_length
            }
        )
        
        # Split into sections
        sections = prompt.split("\n\n")
        
        # Keep system and question sections, truncate context
        system_section = sections[0] if sections else ""
        question_parts = [s for s in sections if "CURRENT QUESTION:" in s]
        instruction_parts = [s for s in sections if "INSTRUCTIONS:" in s]
        
        # Calculate space for context
        fixed_length = len(system_section) + len("\n\n".join(question_parts + instruction_parts))
        available_context = self.max_context_length - fixed_length - 100  # Buffer
        
        # Truncate context section
        context_parts = [s for s in sections if "CONTEXT:" in s]
        if context_parts:
            context = context_parts[0]
            if len(context) > available_context:
                context = context[:available_context] + "\n\n[Context truncated due to length limits]"
                context_parts[0] = context
        
        # Rebuild prompt
        truncated_sections = [system_section] + context_parts + question_parts + instruction_parts
        return "\n\n".join(filter(None, truncated_sections))
    
    def build_followup_prompt(
        self,
        original_question: str,
        original_answer: str,
        followup_question: str,
        chunks: List[str],
        citations: List[Citation]
    ) -> str:
        """
        Build prompt for follow-up questions
        
        Args:
            original_question: Previous question
            original_answer: Previous answer
            followup_question: New follow-up question
            chunks: Retrieved chunks for follow-up
            citations: Citations for follow-up
            
        Returns:
            Formatted follow-up prompt
        """
        history = [
            {"role": "user", "content": original_question},
            {"role": "assistant", "content": original_answer}
        ]
        
        return self.build_rag_prompt(
            question=followup_question,
            chunks=chunks,
            citations=citations,
            conversation_history=history
        )
    
    def build_clarification_prompt(
        self,
        question: str,
        chunks: List[str],
        citations: List[Citation],
        clarification_type: str = "ambiguous"
    ) -> str:
        """
        Build prompt for clarifying ambiguous questions
        
        Args:
            question: Original question
            chunks: Retrieved chunks
            citations: Citations
            clarification_type: Type of clarification needed
            
        Returns:
            Clarification prompt
        """
        clarification_instructions = {
            "ambiguous": "The question is somewhat ambiguous. Provide the best answer you can based on the context, and suggest how the user might refine their question for a more specific answer.",
            "insufficient_context": "The context doesn't provide enough information to fully answer this question. Explain what information is available and what would be needed for a complete answer.",
            "multiple_interpretations": "This question could have multiple interpretations. Address the most likely interpretations based on the available context."
        }
        
        instruction = clarification_instructions.get(
            clarification_type,
            "Please answer based on the available context."
        )
        
        # Modify the instruction section
        prompt = self.build_rag_prompt(question, chunks, citations)
        prompt = prompt.replace(
            "INSTRUCTIONS:",
            f"SPECIAL INSTRUCTIONS: {instruction}\n\nINSTRUCTIONS:"
        )
        
        return prompt
    
    def build_summary_prompt(self, chunks: List[str], citations: List[Citation]) -> str:
        """
        Build prompt for document summarization
        
        Args:
            chunks: Text chunks to summarize
            citations: Citation information
            
        Returns:
            Summary prompt
        """
        context_section = self._build_context_section(chunks, citations, None)
        
        return f"""{self._build_system_section()}

{context_section}

TASK: Provide a comprehensive summary of the key points covered in the provided context. Structure your summary with:

1. Main topics and themes
2. Key findings or conclusions  
3. Important details and examples
4. Any notable insights or implications

Use [Citation X] format to reference specific information from the sources.

SUMMARY:"""


def test_prompt_builder():
    """Test function for prompt builder"""
    from app.services.retrieval.citation_extractor import Citation
    
    # Create test data
    chunks = [
        "Machine learning is a subset of artificial intelligence that enables computers to learn from data.",
        "Neural networks are computational models inspired by biological neural networks."
    ]
    
    citations = [
        Citation(
            chunk_id="chunk1",
            page_number=15,
            section_ref="ch2",
            section_title="Introduction to ML",
            text_snippet="Machine learning is a subset...",
            relevance_score=0.9
        ),
        Citation(
            chunk_id="chunk2", 
            page_number=23,
            section_ref="ch3",
            section_title="Neural Networks",
            text_snippet="Neural networks are computational...",
            relevance_score=0.8
        )
    ]
    
    builder = PromptBuilder()
    prompt = builder.build_rag_prompt(
        question="What is machine learning?",
        chunks=chunks,
        citations=citations,
        document_title="AI Fundamentals"
    )
    
    print("Prompt Builder Test:")
    print(f"Prompt length: {len(prompt)}")
    print("First 500 characters:")
    print(prompt[:500])
    print("...")
    
    return prompt


if __name__ == "__main__":
    test_prompt_builder()