"""
Document processing utilities for RegIntelAI
"""
import os
from typing import List, Dict
from pypdf import PdfReader
from config import CHUNK_SIZE, CHUNK_OVERLAP

# Classe simple de text splitter pour remplacer langchain
class RecursiveCharacterTextSplitter:
    def __init__(self, chunk_size: int, chunk_overlap: int):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def split_text(self, text: str) -> list:
        """Split text into chunks"""
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - self.chunk_overlap
        
        return chunks


def extract_text_from_pdf(pdf_file) -> str:
    """
    Extract text from uploaded PDF file
    
    Args:
        pdf_file: Streamlit uploaded file object
        
    Returns:
        Extracted text as string
    """
    try:
        pdf_reader = PdfReader(pdf_file)
        text = ""
        for page_num, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            text += f"\n\n--- Page {page_num + 1} ---\n\n{page_text}"
        return text
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")


def chunk_documents(text: str, filename: str) -> List[Dict[str, str]]:
    """
    Split document text into chunks with metadata
    
    Args:
        text: Document text to chunk
        filename: Name of the source file
        
    Returns:
        List of chunks with metadata
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )
    
    chunks = text_splitter.split_text(text)
    
    # Add metadata to each chunk
    chunked_docs = []
    for idx, chunk in enumerate(chunks):
        chunked_docs.append({
            "text": chunk,
            "metadata": {
                "source": filename,
                "chunk_id": idx,
                "total_chunks": len(chunks)
            }
        })
    
    return chunked_docs


def format_citations(chunks: List[Dict]) -> str:
    """
    Format retrieved chunks as citations
    
    Args:
        chunks: List of retrieved chunks with metadata
        
    Returns:
        Formatted citation string
    """
    citations = []
    for idx, chunk in enumerate(chunks):
        source = chunk.get("metadata", {}).get("source", "Unknown")
        chunk_id = chunk.get("metadata", {}).get("chunk_id", "?")
        citations.append(f"[{idx + 1}] {source} (Chunk {chunk_id + 1})")
    
    return "\n".join(citations)
