"""
Text processing module.
Handles text chunking and preprocessing for vector embeddings.
"""

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import tiktoken


class TextProcessor:
    """Processes text for vector storage and retrieval."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize text processor.
        
        Args:
            chunk_size: Maximum size of each text chunk
            chunk_overlap: Overlap between consecutive chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Initialize tokenizer for token counting
        try:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.encoding = None
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using tiktoken.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            int: Number of tokens
        """
        if self.encoding:
            return len(self.encoding.encode(text))
        else:
            # Fallback: rough estimation (1 token ≈ 4 characters)
            return len(text) // 4
    
    def preprocess_text(self, text: str) -> str:
        """
        Clean and preprocess text before chunking.
        
        Args:
            text: Raw text to preprocess
            
        Returns:
            str: Cleaned text
        """
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Remove common Wikipedia artifacts
        text = text.replace('[edit]', '')
        text = text.replace('[citation needed]', '')
        
        # Remove reference markers like [1], [2], etc.
        import re
        text = re.sub(r'\[\d+\]', '', text)
        
        return text.strip()
    
    def create_chunks(self, article_data: dict) -> list[Document]:
        """
        Split article text into chunks and create Document objects.
        
        Args:
            article_data: Dictionary containing article information
            
        Returns:
            list[Document]: List of document chunks with metadata
        """
        full_text = article_data.get('full_text', '')
        
        if not full_text:
            raise ValueError("No text content found in article data")
        
        # Preprocess the text
        cleaned_text = self.preprocess_text(full_text)
        
        # Split into chunks
        chunks = self.text_splitter.split_text(cleaned_text)
        
        # Create Document objects with metadata
        documents = []
        for i, chunk in enumerate(chunks):
            doc = Document(
                page_content=chunk,
                metadata={
                    'source': article_data.get('url', ''),
                    'title': article_data.get('title', ''),
                    'chunk_id': i,
                    'total_chunks': len(chunks),
                    'token_count': self.count_tokens(chunk)
                }
            )
            documents.append(doc)
        
        return documents
    
    def get_text_stats(self, text: str) -> dict:
        """
        Get statistics about the text.
        
        Args:
            text: Text to analyze
            
        Returns:
            dict: Statistics including character count, word count, estimated tokens
        """
        return {
            'character_count': len(text),
            'word_count': len(text.split()),
            'estimated_tokens': self.count_tokens(text),
            'estimated_chunks': (self.count_tokens(text) // self.chunk_size) + 1
        } 