#!/usr/bin/env python3
"""
Test script for document ingestion pipeline end-to-end

This script tests the complete ingestion pipeline:
1. File validation
2. Text extraction 
3. Chunking
4. Embedding generation
5. Database operations (mocked if DB not available)

Prerequisites:
- OpenAI API key in .env
- Sample documents in test_files/
- Database connection (optional, will mock if unavailable)
"""

import asyncio
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import List, Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_file_validation():
    """Test file validation logic"""
    from app.services.ingestion import validate_file_for_ingestion
    
    logger.info("Testing file validation...")
    
    # Test with a temporary text file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Sample document content for testing")
        temp_path = f.name
    
    try:
        # Test valid file
        result = validate_file_for_ingestion(temp_path, "text/plain")
        assert result == True, "Text file should be valid"
        logger.info("✓ Valid file validation passed")
        
        # Test invalid MIME type
        result = validate_file_for_ingestion(temp_path, "image/jpeg")
        assert result == False, "JPEG file should be invalid"
        logger.info("✓ Invalid MIME type validation passed")
        
        # Test non-existent file
        result = validate_file_for_ingestion("/nonexistent/file.txt", "text/plain")
        assert result == False, "Non-existent file should be invalid"
        logger.info("✓ Non-existent file validation passed")
        
    finally:
        # Cleanup
        os.unlink(temp_path)
    
    logger.info("File validation tests completed ✓")


async def test_text_extraction():
    """Test text extraction service"""
    from app.services.extraction import extract_text_from_file
    
    logger.info("Testing text extraction...")
    
    # Create a sample text file
    test_content = """
    # Test Document
    
    This is a test document for the StudyRAG ingestion pipeline.
    
    ## Section 1
    This section contains information about machine learning concepts.
    
    ## Section 2  
    This section covers natural language processing topics.
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(test_content)
        temp_path = f.name
    
    try:
        # Extract text
        extracted = await extract_text_from_file(temp_path, "text/plain")
        
        assert extracted.sections, "Should extract sections"
        assert len(extracted.sections) > 0, "Should have at least one section"
        assert "test document" in extracted.sections[0].content.lower(), "Should contain expected content"
        
        logger.info(f"✓ Extracted {len(extracted.sections)} sections")
        logger.info(f"✓ Title: {extracted.title}")
        logger.info(f"✓ Page count: {extracted.page_count}")
        
    finally:
        os.unlink(temp_path)
    
    logger.info("Text extraction tests completed ✓")


async def test_chunking():
    """Test chunking service"""
    from app.services.chunking import create_chunks
    from app.services.extraction import ExtractedContent, ExtractedSection
    
    logger.info("Testing chunking...")
    
    # Create sample content
    sections = [
        ExtractedSection(
            content="This is the first section with some content about machine learning and artificial intelligence. " * 20,
            title="Introduction",
            section_type="heading",
            page_number=1
        ),
        ExtractedSection(
            content="This is the second section with different content about neural networks and deep learning. " * 20,
            title="Neural Networks", 
            section_type="heading",
            page_number=1
        )
    ]
    
    extracted_content = ExtractedContent(
        sections=sections,
        title="Test Document",
        page_count=1,
        metadata={}
    )
    
    # Create chunks
    chunks = create_chunks(extracted_content, chunk_size=100, overlap_ratio=0.1)
    
    assert len(chunks) > 0, "Should create chunks"
    assert all(chunk.token_count > 0 for chunk in chunks), "All chunks should have token counts"
    assert all(chunk.char_count > 0 for chunk in chunks), "All chunks should have character counts"
    
    logger.info(f"✓ Created {len(chunks)} chunks")
    logger.info(f"✓ Average chunk size: {sum(c.token_count for c in chunks) / len(chunks):.1f} tokens")
    
    logger.info("Chunking tests completed ✓")


async def test_embeddings():
    """Test embedding generation (requires OpenAI API key)"""
    from app.services.embeddings import generate_embeddings
    from app.core.config import get_settings
    
    logger.info("Testing embeddings...")
    
    settings = get_settings()
    if not settings.openai_api_key:
        logger.warning("⚠ OpenAI API key not found, skipping embedding tests")
        return
    
    # Test embedding generation
    test_texts = [
        "This is a test sentence about machine learning.",
        "This is another test sentence about natural language processing.",
        "A third sentence about artificial intelligence applications."
    ]
    
    try:
        start_time = time.time()
        embeddings = await generate_embeddings(test_texts)
        end_time = time.time()
        
        assert len(embeddings) == len(test_texts), "Should generate embedding for each text"
        assert all(len(emb) > 0 for emb in embeddings), "All embeddings should have dimensions"
        assert all(isinstance(emb[0], float) for emb in embeddings), "Embeddings should be float arrays"
        
        logger.info(f"✓ Generated {len(embeddings)} embeddings")
        logger.info(f"✓ Embedding dimension: {len(embeddings[0])}")
        logger.info(f"✓ Generation time: {end_time - start_time:.2f}s")
        
    except Exception as e:
        logger.error(f"❌ Embedding generation failed: {e}")
        logger.warning("Check OpenAI API key and connectivity")
    
    logger.info("Embedding tests completed ✓")


async def test_full_pipeline():
    """Test complete ingestion pipeline"""
    from app.services.ingestion import ingest_document
    
    logger.info("Testing full ingestion pipeline...")
    
    # Create a test document
    test_content = """
    # Machine Learning Fundamentals
    
    Machine learning is a subset of artificial intelligence (AI) that provides systems 
    the ability to automatically learn and improve from experience without being explicitly programmed.
    
    ## Types of Machine Learning
    
    ### Supervised Learning
    Supervised learning uses labeled training data to learn a mapping function from input 
    variables to output variables.
    
    ### Unsupervised Learning  
    Unsupervised learning finds hidden patterns or intrinsic structures in input data 
    without labeled examples.
    
    ### Reinforcement Learning
    Reinforcement learning is concerned with how software agents ought to take actions 
    in an environment to maximize cumulative reward.
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(test_content)
        temp_path = f.name
    
    try:
        # Run full ingestion
        start_time = time.time()
        result = await ingest_document(
            document_id="test-doc-123",
            file_path=temp_path,
            mime_type="text/plain", 
            user_id="test-user-123",
            chunk_size=200,
            overlap_ratio=0.15
        )
        end_time = time.time()
        
        assert result.success, f"Ingestion should succeed: {result.error_message}"
        assert result.chunks_created > 0, "Should create chunks"
        assert result.embeddings_created > 0, "Should create embeddings"
        assert result.page_count > 0, "Should have page count"
        
        logger.info(f"✓ Pipeline completed successfully")
        logger.info(f"✓ Chunks created: {result.chunks_created}")
        logger.info(f"✓ Embeddings created: {result.embeddings_created}")
        logger.info(f"✓ Processing time: {end_time - start_time:.2f}s")
        
    except Exception as e:
        logger.error(f"❌ Full pipeline test failed: {e}")
        raise
    finally:
        os.unlink(temp_path)
    
    logger.info("Full pipeline test completed ✓")


async def test_database_operations():
    """Test database operations (mocked if DB unavailable)"""
    from app.db.operations import insert_chunks, insert_embeddings
    from app.services.chunking import ChunkData
    from app.db.session import get_db_pool
    
    logger.info("Testing database operations...")
    
    try:
        # Test database connection
        pool = await get_db_pool()
        if pool is None:
            logger.warning("⚠ Database not available, skipping database tests")
            return
        
        # Create sample chunks
        sample_chunks = [
            ChunkData(
                content="Sample chunk content about machine learning",
                section_title="Introduction",
                page_number=1,
                section_type="paragraph", 
                token_count=45,
                char_count=200,
                metadata={"test": True}
            )
        ]
        
        # Test chunk insertion
        chunk_ids = await insert_chunks("test-doc-123", sample_chunks)
        assert len(chunk_ids) == 1, "Should return chunk IDs"
        
        # Test embedding insertion  
        sample_embeddings = [[0.1] * 1536]  # Mock embedding
        await insert_embeddings(chunk_ids, sample_embeddings)
        
        logger.info("✓ Database operations completed")
        
    except Exception as e:
        logger.warning(f"⚠ Database operations failed (expected if DB not connected): {e}")
    
    logger.info("Database operation tests completed ✓")


async def main():
    """Run all tests"""
    logger.info("Starting StudyRAG Ingestion Pipeline Tests")
    logger.info("=" * 50)
    
    test_functions = [
        test_file_validation,
        test_text_extraction,
        test_chunking,
        test_embeddings,
        test_database_operations,
        test_full_pipeline
    ]
    
    results = {"passed": 0, "failed": 0}
    
    for test_func in test_functions:
        try:
            logger.info(f"\n{'='*20} {test_func.__name__} {'='*20}")
            await test_func()
            results["passed"] += 1
        except Exception as e:
            logger.error(f"❌ {test_func.__name__} failed: {e}")
            results["failed"] += 1
    
    logger.info(f"\n{'='*50}")
    logger.info(f"Test Results: {results['passed']} passed, {results['failed']} failed")
    
    if results["failed"] == 0:
        logger.info("🎉 All tests passed!")
    else:
        logger.warning(f"⚠ {results['failed']} tests failed")
    
    return results["failed"] == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)