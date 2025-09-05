"""RAG Service orchestrator for retrieval-augmented generation"""

import logging
import time
import asyncio
from typing import List, Dict, Optional, AsyncGenerator, Tuple
from dataclasses import dataclass

from app.services.retrieval import BM25Retriever, VectorRetriever, HybridRanker, CitationExtractor
from app.services.embeddings import generate_embeddings
from .prompt_builder import PromptBuilder
from .response_formatter import ResponseFormatter
from app.core.config import get_settings

import openai

logger = logging.getLogger(__name__)


@dataclass
class RAGResponse:
    """Response from RAG pipeline"""
    answer: str
    citations: List[Dict[str, any]]
    query_id: str
    processing_time: float
    retrieval_stats: Dict[str, any]
    llm_stats: Dict[str, any]
    metadata: Dict[str, any]


@dataclass
class RAGConfig:
    """Configuration for RAG pipeline"""
    max_chunks: int = 10
    bm25_weight: float = 0.4
    vector_weight: float = 0.6
    min_relevance: float = 0.1
    max_citations: int = 5
    temperature: float = 0.7
    max_tokens: int = 1000
    streaming: bool = False


class RAGService:
    """Main RAG service orchestrator"""
    
    def __init__(self, config: Optional[RAGConfig] = None):
        """
        Initialize RAG service
        
        Args:
            config: RAG configuration settings
        """
        self.config = config or RAGConfig()
        self.settings = get_settings()
        
        # Initialize components
        self.bm25_retriever = BM25Retriever()
        self.vector_retriever = VectorRetriever()
        self.hybrid_ranker = HybridRanker(
            bm25_weight=self.config.bm25_weight,
            vector_weight=self.config.vector_weight
        )
        self.citation_extractor = CitationExtractor()
        self.prompt_builder = PromptBuilder()
        self.response_formatter = ResponseFormatter()
        
        # Initialize OpenAI client
        openai.api_key = self.settings.openai_api_key
    
    async def query(
        self,
        question: str,
        document_id: str,
        user_id: str,
        config_override: Optional[Dict[str, any]] = None
    ) -> RAGResponse:
        """
        Process a RAG query end-to-end
        
        Args:
            question: User's question
            document_id: Document UUID to search
            user_id: User UUID for RLS
            config_override: Override default config parameters
            
        Returns:
            RAGResponse with answer and citations
        """
        start_time = time.time()
        query_id = f"rag_{int(start_time)}_{hash(question) % 1000000}"
        
        logger.info(
            "Starting RAG query",
            extra={
                "query_id": query_id,
                "question": question,
                "document_id": document_id,
                "user_id": user_id
            }
        )
        
        # Apply config overrides
        effective_config = self._merge_config(config_override)
        
        try:
            # Step 1: Hybrid Retrieval
            retrieval_start = time.time()
            hybrid_results = await self._retrieve_chunks(
                question, document_id, user_id, effective_config
            )
            retrieval_time = time.time() - retrieval_start
            
            if not hybrid_results:
                logger.warning(
                    "No relevant chunks found",
                    extra={"query_id": query_id, "question": question}
                )
                return self._create_no_results_response(
                    query_id, question, time.time() - start_time
                )
            
            # Step 2: Extract Citations
            citations = self.citation_extractor.extract_citations(
                question, hybrid_results, 
                max_citations=effective_config.max_citations
            )
            
            # Step 3: Build Prompt
            prompt = self.prompt_builder.build_rag_prompt(
                question=question,
                chunks=[r.content for r in hybrid_results[:effective_config.max_chunks]],
                citations=citations
            )
            
            # Step 4: Generate Answer
            llm_start = time.time()
            raw_answer = await self._generate_answer(prompt, effective_config)
            llm_time = time.time() - llm_start
            
            # Step 5: Format Response
            formatted_answer = self.response_formatter.format_answer(
                raw_answer, citations
            )
            
            total_time = time.time() - start_time
            
            # Prepare response
            response = RAGResponse(
                answer=formatted_answer,
                citations=[self.citation_extractor.format_citation_json(c) for c in citations],
                query_id=query_id,
                processing_time=total_time,
                retrieval_stats={
                    "chunks_retrieved": len(hybrid_results),
                    "retrieval_time": retrieval_time,
                    "bm25_weight": effective_config.bm25_weight,
                    "vector_weight": effective_config.vector_weight
                },
                llm_stats={
                    "model": "gpt-3.5-turbo",
                    "temperature": effective_config.temperature,
                    "max_tokens": effective_config.max_tokens,
                    "generation_time": llm_time
                },
                metadata={
                    "question_length": len(question),
                    "prompt_length": len(prompt),
                    "answer_length": len(formatted_answer),
                    "config": effective_config.__dict__
                }
            )
            
            logger.info(
                "RAG query completed successfully",
                extra={
                    "query_id": query_id,
                    "processing_time": total_time,
                    "chunks_used": len(hybrid_results),
                    "citations_count": len(citations)
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(
                "RAG query failed",
                extra={
                    "query_id": query_id,
                    "error": str(e),
                    "question": question
                },
                exc_info=True
            )
            
            return self._create_error_response(
                query_id, question, str(e), time.time() - start_time
            )
    
    async def query_streaming(
        self,
        question: str,
        document_id: str,
        user_id: str,
        config_override: Optional[Dict[str, any]] = None
    ) -> AsyncGenerator[Dict[str, any], None]:
        """
        Process a RAG query with streaming response
        
        Args:
            question: User's question
            document_id: Document UUID to search
            user_id: User UUID for RLS
            config_override: Override default config parameters
            
        Yields:
            Streaming response chunks
        """
        query_id = f"rag_stream_{int(time.time())}_{hash(question) % 1000000}"
        
        logger.info(
            "Starting streaming RAG query",
            extra={
                "query_id": query_id,
                "question": question,
                "document_id": document_id
            }
        )
        
        try:
            # Apply config overrides
            effective_config = self._merge_config(config_override)
            effective_config.streaming = True
            
            # Send initial status
            yield {
                "type": "status",
                "message": "Starting retrieval...",
                "query_id": query_id
            }
            
            # Step 1: Hybrid Retrieval
            hybrid_results = await self._retrieve_chunks(
                question, document_id, user_id, effective_config
            )
            
            yield {
                "type": "status", 
                "message": f"Retrieved {len(hybrid_results)} relevant chunks",
                "chunks_count": len(hybrid_results)
            }
            
            if not hybrid_results:
                yield {
                    "type": "error",
                    "message": "No relevant content found for your question"
                }
                return
            
            # Step 2: Extract Citations
            citations = self.citation_extractor.extract_citations(
                question, hybrid_results,
                max_citations=effective_config.max_citations
            )
            
            yield {
                "type": "citations",
                "citations": [self.citation_extractor.format_citation_json(c) for c in citations]
            }
            
            # Step 3: Build Prompt and Stream Answer
            prompt = self.prompt_builder.build_rag_prompt(
                question=question,
                chunks=[r.content for r in hybrid_results[:effective_config.max_chunks]],
                citations=citations
            )
            
            yield {
                "type": "status",
                "message": "Generating answer..."
            }
            
            # Stream the answer generation
            async for chunk in self._generate_answer_streaming(prompt, effective_config):
                yield {
                    "type": "answer_chunk",
                    "content": chunk
                }
            
            yield {
                "type": "complete",
                "query_id": query_id,
                "message": "Query completed successfully"
            }
            
        except Exception as e:
            logger.error(
                "Streaming RAG query failed",
                extra={"query_id": query_id, "error": str(e)},
                exc_info=True
            )
            
            yield {
                "type": "error",
                "message": f"Query failed: {str(e)}",
                "query_id": query_id
            }
    
    async def _retrieve_chunks(
        self,
        question: str,
        document_id: str,
        user_id: str,
        config: RAGConfig
    ) -> List:
        """
        Perform hybrid retrieval to get relevant chunks
        
        Args:
            question: User's question
            document_id: Document UUID
            user_id: User UUID
            config: RAG configuration
            
        Returns:
            List of hybrid results
        """
        # Run BM25 and vector retrieval in parallel
        bm25_task = self.bm25_retriever.retrieve(
            query_text=question,
            document_id=document_id,
            user_id=user_id,
            limit=20
        )
        
        vector_task = self.vector_retriever.retrieve(
            query_text=question,
            document_id=document_id,
            user_id=user_id,
            limit=20
        )
        
        bm25_results, vector_results = await asyncio.gather(
            bm25_task, vector_task, return_exceptions=True
        )
        
        # Handle exceptions
        if isinstance(bm25_results, Exception):
            logger.error(f"BM25 retrieval failed: {bm25_results}")
            bm25_results = []
        
        if isinstance(vector_results, Exception):
            logger.error(f"Vector retrieval failed: {vector_results}")
            vector_results = []
        
        # Combine using hybrid ranker
        hybrid_results = self.hybrid_ranker.rank(
            bm25_results=bm25_results,
            vector_results=vector_results,
            limit=config.max_chunks * 2  # Get more for better selection
        )
        
        # Filter by minimum relevance
        filtered_results = [
            r for r in hybrid_results 
            if r.hybrid_score >= config.min_relevance
        ]
        
        return filtered_results
    
    async def _generate_answer(self, prompt: str, config: RAGConfig) -> str:
        """
        Generate answer using OpenAI API
        
        Args:
            prompt: Formatted prompt for LLM
            config: RAG configuration
            
        Returns:
            Generated answer text
        """
        try:
            client = openai.AsyncOpenAI(api_key=self.settings.openai_api_key)
            
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=config.temperature,
                max_tokens=config.max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise Exception(f"Failed to generate answer: {str(e)}")
    
    async def _generate_answer_streaming(
        self, 
        prompt: str, 
        config: RAGConfig
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming answer using OpenAI API
        
        Args:
            prompt: Formatted prompt for LLM
            config: RAG configuration
            
        Yields:
            Answer text chunks
        """
        try:
            client = openai.AsyncOpenAI(api_key=self.settings.openai_api_key)
            
            stream = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"OpenAI streaming API error: {e}")
            raise Exception(f"Failed to generate streaming answer: {str(e)}")
    
    def _merge_config(self, config_override: Optional[Dict[str, any]]) -> RAGConfig:
        """
        Merge config override with default config
        
        Args:
            config_override: Override parameters
            
        Returns:
            Merged RAG configuration
        """
        config_dict = self.config.__dict__.copy()
        
        if config_override:
            config_dict.update(config_override)
        
        return RAGConfig(**config_dict)
    
    def _create_no_results_response(
        self, 
        query_id: str, 
        question: str, 
        processing_time: float
    ) -> RAGResponse:
        """Create response for when no relevant chunks are found"""
        return RAGResponse(
            answer="I couldn't find relevant information in the document to answer your question. Please try rephrasing your question or check if the document contains the information you're looking for.",
            citations=[],
            query_id=query_id,
            processing_time=processing_time,
            retrieval_stats={"chunks_retrieved": 0},
            llm_stats={},
            metadata={"question": question, "result_type": "no_results"}
        )
    
    def _create_error_response(
        self, 
        query_id: str, 
        question: str, 
        error: str, 
        processing_time: float
    ) -> RAGResponse:
        """Create response for when an error occurs"""
        return RAGResponse(
            answer=f"I encountered an error while processing your question: {error}",
            citations=[],
            query_id=query_id,
            processing_time=processing_time,
            retrieval_stats={},
            llm_stats={},
            metadata={"question": question, "result_type": "error", "error": error}
        )


async def test_rag_service():
    """Test function for RAG service"""
    service = RAGService()
    
    response = await service.query(
        question="What are machine learning algorithms?",
        document_id="test-doc-123",
        user_id="test-user-123"
    )
    
    print(f"RAG Service Test:")
    print(f"Answer: {response.answer}")
    print(f"Citations: {len(response.citations)}")
    print(f"Processing time: {response.processing_time:.2f}s")
    
    return response


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_rag_service())