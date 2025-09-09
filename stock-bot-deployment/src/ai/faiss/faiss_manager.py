"""
FAISS Vector Database Manager
Handles FAISS index creation, management, and querying
"""

import faiss
import pickle
import numpy as np
import os
from typing import Dict, List, Optional, Any, Tuple
import logging
from sentence_transformers import SentenceTransformer
import json

class FAISSManager:
    """Manages FAISS vector database operations"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize FAISS manager
        
        Args:
            config: Configuration dictionary containing FAISS settings
        """
        self.config = config
        self.model_name = config['faiss_settings']['model_name']
        self.index_dimension = config['faiss_settings']['index_dimension']
        self.chunk_size = config['faiss_settings']['chunk_size']
        self.overlap_size = config['faiss_settings']['overlap_size']
        
        self.model = None
        self.index = None
        self.documents = []
        self.document_metadata = []
        
        self._setup_logging()
        self._load_model()
    
    def _setup_logging(self):
        """Setup logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _load_model(self):
        """Load sentence transformer model"""
        try:
            self.model = SentenceTransformer(self.model_name)
            self.logger.info(f"Loaded model: {self.model_name}")
        except Exception as e:
            self.logger.error(f"Error loading model: {str(e)}")
            raise
    
    def create_index_from_yahoo_data(self, yahoo_data: Dict[str, Any]) -> bool:
        """
        Create FAISS index from Yahoo Finance data
        
        Args:
            yahoo_data: Dictionary containing Yahoo Finance data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("Creating FAISS index from Yahoo Finance data")
            
            # Process each symbol's data
            for symbol, df in yahoo_data.items():
                self._process_dataframe(symbol, df, 'yahoo_finance')
            
            # Create FAISS index
            self._build_index()
            
            self.logger.info(f"Created FAISS index with {len(self.documents)} documents")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating index from Yahoo data: {str(e)}")
            return False
    
    def create_index_from_files(self, file_data: List[Dict[str, Any]]) -> bool:
        """
        Create FAISS index from uploaded files
        
        Args:
            file_data: List of processed file data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("Creating FAISS index from uploaded files")
            
            for file_info in file_data:
                self._process_file_data(file_info)
            
            # Create FAISS index
            self._build_index()
            
            self.logger.info(f"Created FAISS index with {len(self.documents)} documents")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating index from files: {str(e)}")
            return False
    
    def _process_dataframe(self, symbol: str, df, data_type: str):
        """Process DataFrame into text chunks"""
        try:
            # Create summary text
            summary_text = f"Financial data for {symbol}:\n"
            summary_text += f"Date range: {df.index[0]} to {df.index[-1]}\n"
            summary_text += f"Total records: {len(df)}\n"
            summary_text += f"Columns: {', '.join(df.columns)}\n"
            
            # Add recent data summary
            recent_data = df.tail(5)
            summary_text += f"Recent data:\n{recent_data.to_string()}\n"
            
            # Add statistical summary
            stats = df.describe()
            summary_text += f"Statistical summary:\n{stats.to_string()}\n"
            
            # Chunk the text
            chunks = self._chunk_text(summary_text)
            
            for i, chunk in enumerate(chunks):
                self.documents.append(chunk)
                self.document_metadata.append({
                    'symbol': symbol,
                    'data_type': data_type,
                    'chunk_id': i,
                    'source': 'yahoo_finance'
                })
                
        except Exception as e:
            self.logger.error(f"Error processing DataFrame for {symbol}: {str(e)}")
    
    def _process_file_data(self, file_info: Dict[str, Any]):
        """Process uploaded file data"""
        try:
            content = file_info.get('content', '')
            metadata = file_info.get('metadata', {})
            
            if not content:
                return
            
            # Chunk the content
            chunks = self._chunk_text(content)
            
            for i, chunk in enumerate(chunks):
                self.documents.append(chunk)
                self.document_metadata.append({
                    'file_name': metadata.get('file_name', 'unknown'),
                    'file_type': metadata.get('file_type', 'unknown'),
                    'chunk_id': i,
                    'source': 'uploaded_file',
                    **metadata
                })
                
        except Exception as e:
            self.logger.error(f"Error processing file data: {str(e)}")
    
    def _chunk_text(self, text: str) -> List[str]:
        """Split text into chunks"""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings
                for i in range(end, max(start + self.chunk_size // 2, end - 100), -1):
                    if text[i] in '.!?\n':
                        end = i + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - self.overlap_size
            if start >= len(text):
                break
        
        return chunks
    
    def _build_index(self):
        """Build FAISS index from documents"""
        if not self.documents:
            self.logger.warning("No documents to index")
            return
        
        try:
            # Generate embeddings
            self.logger.info("Generating embeddings...")
            embeddings = self.model.encode(self.documents)
            
            # Create FAISS index
            self.index = faiss.IndexFlatIP(self.index_dimension)
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings)
            
            # Add embeddings to index
            self.index.add(embeddings.astype('float32'))
            
            self.logger.info(f"Built FAISS index with {self.index.ntotal} vectors")
            
        except Exception as e:
            self.logger.error(f"Error building FAISS index: {str(e)}")
            raise
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search the FAISS index
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of search results with metadata
        """
        if self.index is None:
            self.logger.warning("No index available for search")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.model.encode([query])
            faiss.normalize_L2(query_embedding)
            
            # Search index
            scores, indices = self.index.search(query_embedding.astype('float32'), k)
            
            # Prepare results
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.documents):
                    results.append({
                        'content': self.documents[idx],
                        'metadata': self.document_metadata[idx],
                        'score': float(score)
                    })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching index: {str(e)}")
            return []
    
    def save_index(self, index_path: str, docs_path: str) -> bool:
        """
        Save FAISS index and documents to disk
        
        Args:
            index_path: Path to save FAISS index
            docs_path: Path to save documents
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.index is None:
                self.logger.warning("No index to save")
                return False
            
            # Save FAISS index
            faiss.write_index(self.index, index_path)
            
            # Save documents and metadata
            with open(docs_path, 'wb') as f:
                pickle.dump({
                    'documents': self.documents,
                    'metadata': self.document_metadata
                }, f)
            
            self.logger.info(f"Saved index to {index_path} and documents to {docs_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving index: {str(e)}")
            return False
    
    def load_index(self, index_path: str, docs_path: str) -> bool:
        """
        Load FAISS index and documents from disk
        
        Args:
            index_path: Path to FAISS index
            docs_path: Path to documents
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(index_path) or not os.path.exists(docs_path):
                self.logger.warning("Index or documents file not found")
                return False
            
            # Load FAISS index
            self.index = faiss.read_index(index_path)
            
            # Load documents and metadata
            with open(docs_path, 'rb') as f:
                data = pickle.load(f)
                self.documents = data['documents']
                self.document_metadata = data['metadata']
            
            self.logger.info(f"Loaded index with {self.index.ntotal} vectors and {len(self.documents)} documents")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading index: {str(e)}")
            return False
    
    def get_index_info(self) -> Dict[str, Any]:
        """Get information about the current index"""
        if self.index is None:
            return {'status': 'no_index', 'total_vectors': 0, 'total_documents': 0}
        
        return {
            'status': 'loaded',
            'total_vectors': self.index.ntotal,
            'total_documents': len(self.documents),
            'model_name': self.model_name,
            'index_dimension': self.index_dimension
        }
