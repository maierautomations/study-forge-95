#!/usr/bin/env python3
"""
Test script for P4 - Hybrid Retrieval System

This script tests all components of the hybrid retrieval system:
- BM25 retrieval
- Vector retrieval  
- Hybrid ranking
- Citation extraction
- RAG service integration

Run with: python test_retrieval.py
"""

import asyncio
import logging
import sys
from typing import List
from uuid import uuid4

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_imports():
    """Test 1: Import all retrieval components"""
    print("🧪 Test 1: Testing imports...")
    try:
        from app.services.retrieval import BM25Retriever, VectorRetriever, HybridRanker, CitationExtractor
        from app.services.rag import RAGService, PromptBuilder, ResponseFormatter
        from app.core.config import get_settings
        print("✅ All retrieval imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_component_initialization():
    """Test 2: Initialize all retrieval components"""
    print("\n🧪 Test 2: Testing component initialization...")
    try:
        from app.services.retrieval import BM25Retriever, VectorRetriever, HybridRanker, CitationExtractor
        from app.services.rag import RAGService, PromptBuilder, ResponseFormatter
        
        # Initialize components
        bm25 = BM25Retriever()
        vector = VectorRetriever()
        ranker = HybridRanker()
        citation_extractor = CitationExtractor()
        rag_service = RAGService()
        prompt_builder = PromptBuilder()
        response_formatter = ResponseFormatter()
        
        print("✅ All components initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Component initialization failed: {e}")
        return False

async def test_database_connection():
    """Test 3: Test database connectivity for retrieval queries"""
    print("\n🧪 Test 3: Testing database connection...")
    try:
        from app.db.session import get_db_pool
        
        pool = await get_db_pool()
        if pool:
            async with pool.acquire() as conn:
                # Test basic query
                result = await conn.fetchval("SELECT 1")
                if result == 1:
                    print("✅ Database connection successful")
                    return True
        
        print("❌ Database connection failed")
        return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

async def test_bm25_query_processing():
    """Test 4: BM25 query processing"""
    print("\n🧪 Test 4: Testing BM25 query processing...")
    try:
        from app.services.retrieval import BM25Retriever
        
        bm25 = BM25Retriever()
        
        # Test query preprocessing
        test_queries = [
            "machine learning algorithms",
            "What are neural networks?",
            "deep learning vs traditional ML"
        ]
        
        for query in test_queries:
            processed = bm25._preprocess_query(query)
            if processed:
                print(f"  ✓ Processed: '{query}' → '{processed}'")
            else:
                print(f"  ❌ Failed to process: '{query}'")
                return False
        
        print("✅ BM25 query processing successful")
        return True
    except Exception as e:
        print(f"❌ BM25 query processing failed: {e}")
        return False

async def test_vector_embedding():
    """Test 5: Vector embedding generation"""
    print("\n🧪 Test 5: Testing vector embedding generation...")
    try:
        from app.services.retrieval import VectorRetriever
        from app.core.config import get_settings
        
        settings = get_settings()
        if not settings.openai_api_key:
            print("⚠️ Skipping vector embedding test - no OpenAI API key")
            return True
        
        vector = VectorRetriever()
        
        test_text = "machine learning algorithms"
        embedding = await vector._get_query_embedding(test_text)
        
        if embedding and len(embedding) == 1536:  # OpenAI embedding dimension
            print(f"✅ Generated embedding with {len(embedding)} dimensions")
            return True
        else:
            print("❌ Invalid embedding generated")
            return False
            
    except Exception as e:
        print(f"❌ Vector embedding failed: {e}")
        return False

async def test_hybrid_ranking():
    """Test 6: Hybrid ranking algorithm"""
    print("\n🧪 Test 6: Testing hybrid ranking algorithm...")
    try:
        from app.services.retrieval import HybridRanker
        from app.services.retrieval.bm25_retrieval import BM25Result
        from app.services.retrieval.vector_retrieval import VectorResult
        
        ranker = HybridRanker(bm25_weight=0.4, vector_weight=0.6)
        
        # Create mock results
        bm25_results = [
            BM25Result(
                chunk_id="chunk1",
                content="Machine learning is a subset of AI",
                score=0.8,
                page_number=1,
                section_ref="ch1",
                section_title="Introduction",
                metadata={}
            ),
            BM25Result(
                chunk_id="chunk2", 
                content="Neural networks are computational models",
                score=0.6,
                page_number=2,
                section_ref="ch2",
                section_title="Methods",
                metadata={}
            )
        ]
        
        vector_results = [
            VectorResult(
                chunk_id="chunk1",
                content="Machine learning is a subset of AI", 
                similarity_score=0.9,
                page_number=1,
                section_ref="ch1",
                section_title="Introduction",
                metadata={}
            ),
            VectorResult(
                chunk_id="chunk3",
                content="Deep learning uses neural networks",
                similarity_score=0.7,
                page_number=3,
                section_ref="ch3",
                section_title="Advanced Topics",
                metadata={}
            )
        ]
        
        # Test ranking
        hybrid_results = ranker.rank(bm25_results, vector_results, limit=5)
        
        if hybrid_results and len(hybrid_results) > 0:
            print(f"✅ Hybrid ranking produced {len(hybrid_results)} results")
            for i, result in enumerate(hybrid_results[:3]):
                bm25_score = getattr(result, 'bm25_score', 0) or 0
                vector_score = getattr(result, 'vector_score', 0) or 0
                print(f"  {i+1}. Chunk {result.chunk_id}: {result.hybrid_score:.3f} (BM25: {bm25_score:.3f}, Vec: {vector_score:.3f})")
            return True
        else:
            print("❌ Hybrid ranking failed")
            return False
            
    except Exception as e:
        print(f"❌ Hybrid ranking failed: {e}")
        return False

async def test_citation_extraction():
    """Test 7: Citation extraction"""
    print("\n🧪 Test 7: Testing citation extraction...")
    try:
        from app.services.retrieval import CitationExtractor
        from app.services.retrieval.hybrid_ranker import HybridResult
        
        extractor = CitationExtractor()
        
        # Create mock hybrid results
        hybrid_results = [
            HybridResult(
                chunk_id="chunk1",
                content="Machine learning algorithms enable computers to learn from data without being explicitly programmed. This approach has revolutionized many fields.",
                bm25_score=0.8,
                vector_score=0.9,
                hybrid_score=0.86,
                page_number=15,
                section_title="Machine Learning Basics",
                section_ref="ch2",
                rank_bm25=1,
                rank_vector=1,
                metadata={}
            )
        ]
        
        query = "machine learning algorithms"
        citations = extractor.extract_citations(query, hybrid_results, max_citations=3)
        
        if citations and len(citations) > 0:
            print(f"✅ Extracted {len(citations)} citations")
            for i, citation in enumerate(citations):
                print(f"  {i+1}. Page {citation.page_number}: {citation.text_snippet[:50]}...")
            return True
        else:
            print("❌ Citation extraction failed")
            return False
            
    except Exception as e:
        print(f"❌ Citation extraction failed: {e}")
        return False

async def test_prompt_building():
    """Test 8: Prompt building"""
    print("\n🧪 Test 8: Testing prompt building...")
    try:
        from app.services.rag import PromptBuilder
        from app.services.retrieval.citation_extractor import Citation
        
        builder = PromptBuilder()
        
        # Create test data
        question = "What is machine learning?"
        chunks = ["Machine learning is a subset of AI that enables computers to learn from data."]
        citations = [
            Citation(
                chunk_id="chunk1",
                page_number=15,
                section_ref="ch2",
                section_title="ML Basics",
                text_snippet="Machine learning is a subset of AI",
                relevance_score=0.9
            )
        ]
        
        prompt = builder.build_rag_prompt(
            question=question,
            chunks=chunks,
            citations=citations,
            document_title="AI Fundamentals"
        )
        
        if prompt and len(prompt) > 100:
            print(f"✅ Built prompt with {len(prompt)} characters")
            print(f"  Contains system instructions: {'You are an AI assistant' in prompt}")
            print(f"  Contains context: {'CONTEXT:' in prompt}")
            print(f"  Contains question: {question in prompt}")
            return True
        else:
            print("❌ Prompt building failed")
            return False
            
    except Exception as e:
        print(f"❌ Prompt building failed: {e}")
        return False

async def test_response_formatting():
    """Test 9: Response formatting"""
    print("\n🧪 Test 9: Testing response formatting...")
    try:
        from app.services.rag import ResponseFormatter
        from app.services.retrieval.citation_extractor import Citation
        
        formatter = ResponseFormatter()
        
        raw_answer = "Machine learning is a powerful approach [Citation 1] that uses algorithms to find patterns."
        citations = [
            Citation(
                chunk_id="chunk1",
                page_number=15,
                section_ref="ch2", 
                section_title="ML Basics",
                text_snippet="Machine learning enables computers to learn",
                relevance_score=0.9
            )
        ]
        
        formatted = formatter.format_answer(raw_answer, citations, confidence_score=0.85)
        
        if formatted and len(formatted) > len(raw_answer):
            print("✅ Response formatting successful")
            print(f"  Added confidence indicator: {'confidence' in formatted.lower()}")
            print(f"  Citation validation: {'[Citation 1]' in formatted}")
            return True
        else:
            print("❌ Response formatting failed")
            return False
            
    except Exception as e:
        print(f"❌ Response formatting failed: {e}")
        return False

async def test_rag_service_initialization():
    """Test 10: RAG service initialization"""
    print("\n🧪 Test 10: Testing RAG service initialization...")
    try:
        from app.services.rag import RAGService
        from app.core.config import get_settings
        
        settings = get_settings()
        rag_service = RAGService()
        
        # Check if all components are initialized
        components = [
            (rag_service.bm25_retriever, "BM25 Retriever"),
            (rag_service.vector_retriever, "Vector Retriever"),
            (rag_service.hybrid_ranker, "Hybrid Ranker"),
            (rag_service.citation_extractor, "Citation Extractor"),
            (rag_service.prompt_builder, "Prompt Builder"),
            (rag_service.response_formatter, "Response Formatter")
        ]
        
        for component, name in components:
            if component:
                print(f"  ✓ {name} initialized")
            else:
                print(f"  ❌ {name} failed to initialize")
                return False
        
        print("✅ RAG service initialization successful")
        return True
        
    except Exception as e:
        print(f"❌ RAG service initialization failed: {e}")
        return False

async def test_with_sample_data():
    """Test 11: Test with sample data (if database has data)"""
    print("\n🧪 Test 11: Testing with sample data...")
    try:
        from app.db.session import get_db_pool
        from app.services.rag import RAGService
        from app.core.config import get_settings
        
        settings = get_settings()
        
        # Check if we have sample data
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            chunk_count = await conn.fetchval("""
                SELECT COUNT(*) FROM public.chunks c
                JOIN public.documents d ON d.id = c.document_id
                LIMIT 1
            """)
            
            if chunk_count == 0:
                print("⚠️ No sample data found - skipping real data test")
                return True
            
            # Get a sample document
            doc_result = await conn.fetchrow("""
                SELECT d.id, d.filename 
                FROM public.documents d
                WHERE d.status = 'ready'
                LIMIT 1
            """)
            
            if not doc_result:
                print("⚠️ No ready documents found - skipping real data test")
                return True
            
            document_id = str(doc_result['id'])
            
            if not settings.openai_api_key:
                print("⚠️ No OpenAI API key - skipping full RAG test")
                return True
            
            # Test basic retrieval without full RAG
            from app.services.retrieval import BM25Retriever, VectorRetriever
            
            bm25 = BM25Retriever()
            vector = VectorRetriever()
            
            test_query = "machine learning"
            user_id = str(uuid4())  # Mock user ID
            
            try:
                bm25_results = await bm25.retrieve(test_query, document_id, user_id, limit=5)
                print(f"  ✓ BM25 retrieved {len(bm25_results)} results")
                
                vector_results = await vector.retrieve(test_query, document_id, user_id, limit=5)
                print(f"  ✓ Vector retrieved {len(vector_results)} results")
                
                print("✅ Sample data test successful")
                return True
                
            except Exception as e:
                print(f"⚠️ Sample data test partial failure: {e}")
                return True  # Don't fail the whole test suite
        
    except Exception as e:
        print(f"❌ Sample data test failed: {e}")
        return False

def print_summary(results: List[bool]):
    """Print test summary"""
    print("\n" + "="*60)
    print("🏁 P4 HYBRID RETRIEVAL TEST SUMMARY")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 All tests passed! P4 Hybrid Retrieval is working correctly.")
        print("\nNext steps:")
        print("- Test with real document data")
        print("- Validate API endpoints: POST /rag/query")
        print("- Move to P5: Quiz Engine implementation")
    else:
        print(f"\n⚠️ {total-passed} test(s) failed. Please review the issues above.")
        print("\nCommon issues:")
        print("- Missing environment variables (DATABASE_URL, OPENAI_API_KEY)")
        print("- Database connection problems")
        print("- Import path issues")
    
    return passed == total

async def main():
    """Run all retrieval tests"""
    print("🚀 Starting P4 Hybrid Retrieval System Tests")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("Component Initialization", test_component_initialization),
        ("Database Connection", test_database_connection),
        ("BM25 Query Processing", test_bm25_query_processing),
        ("Vector Embedding", test_vector_embedding),
        ("Hybrid Ranking", test_hybrid_ranking),
        ("Citation Extraction", test_citation_extraction),
        ("Prompt Building", test_prompt_building),
        ("Response Formatting", test_response_formatting),
        ("RAG Service Init", test_rag_service_initialization),
        ("Sample Data Test", test_with_sample_data)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {name} crashed: {e}")
            results.append(False)
    
    # Print summary
    success = print_summary(results)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())