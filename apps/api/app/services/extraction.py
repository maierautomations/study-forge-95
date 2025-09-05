"""Document text extraction service using Unstructured and MarkItDown"""

import asyncio
import logging
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

try:
    from unstructured.partition.auto import partition
    from unstructured.documents.elements import Element
except ImportError:
    partition = None
    Element = None

try:
    from markitdown import MarkItDown
except ImportError:
    MarkItDown = None

logger = logging.getLogger(__name__)


@dataclass
class ExtractedSection:
    """A section of extracted content"""
    title: Optional[str]
    content: str
    page_number: Optional[int] = None
    section_type: str = "text"  # text, header, table, list, etc.


@dataclass 
class ExtractedContent:
    """Complete extracted content from a document"""
    sections: List[ExtractedSection]
    page_count: Optional[int] = None
    title: Optional[str] = None
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    @property
    def full_text(self) -> str:
        """Get all content as a single text string"""
        return "\n\n".join(section.content for section in self.sections if section.content.strip())


# Thread pool for running blocking extraction operations
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="extraction")


async def extract_text_from_file(file_path: str, mime_type: str) -> ExtractedContent:
    """
    Extract structured text from a document file.
    
    Args:
        file_path: Path to the document file
        mime_type: MIME type of the document
        
    Returns:
        ExtractedContent: Structured content with sections and metadata
        
    Raises:
        ValueError: If file format is unsupported
        FileNotFoundError: If file doesn't exist
    """
    file_path_obj = Path(file_path)
    
    if not file_path_obj.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    logger.info(
        "Starting text extraction",
        extra={
            "file_path": str(file_path_obj),
            "mime_type": mime_type,
            "file_size": file_path_obj.stat().st_size
        }
    )
    
    try:
        # Try Unstructured first (best for PDFs and complex documents)
        if partition and mime_type in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
            return await _extract_with_unstructured(file_path)
            
        # Fall back to MarkItDown for other formats
        elif MarkItDown:
            return await _extract_with_markitdown(file_path)
        else:
            raise ValueError("No extraction libraries available. Please install unstructured and markitdown.")
            
    except Exception as e:
        logger.error(
            "Text extraction failed",
            extra={
                "file_path": str(file_path_obj),
                "mime_type": mime_type,
                "error": str(e)
            }
        )
        raise


async def _extract_with_unstructured(file_path: str) -> ExtractedContent:
    """Extract using Unstructured library (best for PDFs)"""
    
    def _partition_file():
        return partition(filename=file_path)
    
    # Run in thread pool to avoid blocking
    elements = await asyncio.get_event_loop().run_in_executor(_executor, _partition_file)
    
    sections = []
    current_page = None
    
    for element in elements:
        # Get page number if available
        page_num = None
        if hasattr(element, 'metadata') and element.metadata:
            page_num = element.metadata.page_number
            if current_page is None:
                current_page = page_num
        
        # Determine section type based on element type
        section_type = "text"
        if hasattr(element, 'category'):
            category = element.category.lower()
            if "title" in category or "header" in category:
                section_type = "header"
            elif "table" in category:
                section_type = "table" 
            elif "list" in category:
                section_type = "list"
        
        # Extract content
        content = str(element).strip()
        if content:
            section = ExtractedSection(
                title=None if section_type != "header" else content,
                content=content,
                page_number=page_num,
                section_type=section_type
            )
            sections.append(section)
    
    # Estimate page count
    page_count = None
    if sections:
        page_numbers = [s.page_number for s in sections if s.page_number is not None]
        if page_numbers:
            page_count = max(page_numbers)
    
    # Extract title (first header or first significant text)
    title = None
    for section in sections[:5]:  # Check first 5 sections
        if section.section_type == "header" and len(section.content) < 200:
            title = section.content
            break
        elif not title and len(section.content) < 100 and len(section.content) > 10:
            title = section.content
    
    return ExtractedContent(
        sections=sections,
        page_count=page_count,
        title=title,
        metadata={"extraction_method": "unstructured"}
    )


async def _extract_with_markitdown(file_path: str) -> ExtractedContent:
    """Extract using MarkItDown (good for various formats)"""
    
    def _convert_file():
        md = MarkItDown()
        return md.convert(file_path)
    
    # Run in thread pool to avoid blocking
    result = await asyncio.get_event_loop().run_in_executor(_executor, _convert_file)
    
    # MarkItDown returns markdown text
    text_content = result.text_content if hasattr(result, 'text_content') else str(result)
    
    # Simple section splitting by markdown headers or paragraphs
    sections = []
    lines = text_content.split('\n')
    current_section = []
    current_title = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Detect markdown headers
        if line.startswith('#'):
            # Save previous section
            if current_section:
                content = '\n'.join(current_section).strip()
                if content:
                    sections.append(ExtractedSection(
                        title=current_title,
                        content=content,
                        section_type="text"
                    ))
                current_section = []
            
            current_title = line.lstrip('#').strip()
            sections.append(ExtractedSection(
                title=current_title,
                content=current_title,
                section_type="header"
            ))
        else:
            current_section.append(line)
    
    # Add final section
    if current_section:
        content = '\n'.join(current_section).strip()
        if content:
            sections.append(ExtractedSection(
                title=current_title,
                content=content,
                section_type="text"
            ))
    
    # If no sections were created, create one from all content
    if not sections:
        sections = [ExtractedSection(
            title=None,
            content=text_content.strip(),
            section_type="text"
        )]
    
    # Extract title (first header)
    title = None
    for section in sections:
        if section.section_type == "header":
            title = section.title
            break
    
    return ExtractedContent(
        sections=sections,
        page_count=None,  # MarkItDown doesn't provide page info
        title=title,
        metadata={"extraction_method": "markitdown"}
    )