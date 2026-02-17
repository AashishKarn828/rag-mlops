"""
Document processing service for handling file uploads and text extraction
"""
import PyPDF2
import io
from typing import List
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

class DocumentService:
    """Service for processing documents"""
    
    @staticmethod
    def extract_text_from_pdf(file_content: bytes) -> str:
        """
        Extract text from PDF file
        
        Args:
            file_content: PDF file content in bytes
            
        Returns:
            Extracted text
        """
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise
    
    @staticmethod
    def extract_text_from_txt(file_content: bytes) -> str:
        """
        Extract text from TXT file
        
        Args:
            file_content: TXT file content in bytes
            
        Returns:
            Decoded text
        """
        try:
            return file_content.decode('utf-8')
        except Exception as e:
            logger.error(f"Error extracting text from TXT: {str(e)}")
            raise
    
    @staticmethod
    def chunk_text(
        text: str, 
        chunk_size: int = None, 
        overlap: int = None
    ) -> List[str]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk (in words)
            overlap: Overlap between chunks (in words)
            
        Returns:
            List of text chunks
        """
        if chunk_size is None:
            chunk_size = settings.CHUNK_SIZE
        if overlap is None:
            overlap = settings.CHUNK_OVERLAP
        
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk.strip():  # Only add non-empty chunks
                chunks.append(chunk)
        
        return chunks
    
    @staticmethod
    def validate_file_type(filename: str) -> bool:
        """
        Validate if file type is supported
        
        Args:
            filename: Name of the file
            
        Returns:
            True if supported, False otherwise
        """
        supported_extensions = ['.pdf', '.txt']
        return any(filename.lower().endswith(ext) for ext in supported_extensions)

# Global instance
document_service = DocumentService()