"""
Q&A System for Financial Data Analysis
"""

import os
import logging
from typing import Dict, List, Any, Optional
import pandas as pd
from pathlib import Path

# Import FAISS and embedding components
try:
    import faiss
    from sentence_transformers import SentenceTransformer
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("Warning: FAISS not available. Install with: pip install faiss-cpu sentence-transformers")

class QASystem:
    """Question-Answering system for financial data"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Q&A system
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.index = None
        self.model = None
        self.documents = []
        self.metadata = []
        self._setup_logging()
        self._initialize_model()
    
    def _setup_logging(self):
        """Setup logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _initialize_model(self):
        """Initialize the embedding model"""
        if not FAISS_AVAILABLE:
            self.logger.warning("FAISS not available. Q&A functionality will be limited.")
            return
        
        try:
            model_name = self.config.get('faiss_settings', {}).get('model_name', 'all-MiniLM-L6-v2')
            self.model = SentenceTransformer(model_name)
            self.logger.info(f"Initialized embedding model: {model_name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize embedding model: {e}")
            self.model = None
    
    def add_documents(self, documents: List[str], metadata: List[Dict] = None):
        """
        Add documents to the knowledge base
        
        Args:
            documents: List of document texts
            metadata: List of metadata dictionaries for each document
        """
        if not self.model:
            self.logger.error("Model not initialized. Cannot add documents.")
            return
        
        if metadata is None:
            metadata = [{}] * len(documents)
        
        self.documents.extend(documents)
        self.metadata.extend(metadata)
        
        self.logger.info(f"Added {len(documents)} documents. Total: {len(self.documents)}")
    
    def add_financial_data(self, data: Dict[str, pd.DataFrame]):
        """
        Add financial data to the knowledge base
        
        Args:
            data: Dictionary mapping symbol to DataFrame
        """
        documents = []
        metadata = []
        
        for symbol, df in data.items():
            # Create summary text for each symbol
            summary = self._create_data_summary(symbol, df)
            documents.append(summary)
            metadata.append({
                'type': 'financial_data',
                'symbol': symbol,
                'data_points': len(df),
                'date_range': f"{df.index[0].date()} to {df.index[-1].date()}"
            })
        
        self.add_documents(documents, metadata)
    
    def _create_data_summary(self, symbol: str, df: pd.DataFrame) -> str:
        """Create a text summary of financial data"""
        summary = f"Financial data for {symbol}:\n"
        summary += f"Data points: {len(df)}\n"
        summary += f"Date range: {df.index[0].date()} to {df.index[-1].date()}\n"
        
        if 'Close' in df.columns:
            latest_close = df['Close'].iloc[-1]
            price_change = df['Close'].iloc[-1] - df['Close'].iloc[0]
            price_change_pct = (price_change / df['Close'].iloc[0]) * 100
            
            summary += f"Latest close price: ${latest_close:.2f}\n"
            summary += f"Total price change: ${price_change:.2f} ({price_change_pct:.2f}%)\n"
        
        if 'Volume' in df.columns:
            avg_volume = df['Volume'].mean()
            summary += f"Average volume: {avg_volume:,.0f}\n"
        
        # Add recent price action
        if len(df) >= 5:
            recent_5d = df['Close'].tail(5)
            summary += f"Recent 5-day prices: {', '.join([f'${p:.2f}' for p in recent_5d.values])}\n"
        
        return summary
    
    def build_index(self):
        """Build the FAISS index from documents"""
        if not self.model or not self.documents:
            self.logger.error("Cannot build index: model or documents not available")
            return
        
        try:
            # Generate embeddings
            embeddings = self.model.encode(self.documents)
            
            # Create FAISS index
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings)
            self.index.add(embeddings.astype('float32'))
            
            self.logger.info(f"Built FAISS index with {len(self.documents)} documents")
            
        except Exception as e:
            self.logger.error(f"Failed to build index: {e}")
    
    def search(self, query: str, k: int = 5) -> List[Dict]:
        """
        Search for relevant documents
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of relevant documents with metadata
        """
        if not self.index or not self.model:
            self.logger.error("Index or model not available")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.model.encode([query])
            faiss.normalize_L2(query_embedding)
            
            # Search
            scores, indices = self.index.search(query_embedding.astype('float32'), k)
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.documents):
                    results.append({
                        'document': self.documents[idx],
                        'metadata': self.metadata[idx],
                        'score': float(score)
                    })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return []
    
    def answer_question(self, question: str, context_documents: List[str] = None) -> str:
        """
        Answer a question using the knowledge base
        
        Args:
            question: User's question
            context_documents: Optional context documents to use
            
        Returns:
            Answer string
        """
        if context_documents is None:
            # Search for relevant documents
            search_results = self.search(question, k=3)
            context_documents = [result['document'] for result in search_results]
        
        if not context_documents:
            return "I don't have enough information to answer your question. Please ensure data has been loaded and indexed."
        
        # Create context from documents
        context = "\n\n".join(context_documents)
        
        # Simple answer generation (in a real system, you'd use a language model)
        answer = f"Based on the available data:\n\n"
        answer += f"Question: {question}\n\n"
        answer += f"Relevant Information:\n{context}\n\n"
        answer += "Please note: This is a basic Q&A system. For production use, integrate with a language model like GPT or Claude for more sophisticated answers."
        
        return answer
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the current index"""
        return {
            'total_documents': len(self.documents),
            'index_built': self.index is not None,
            'model_available': self.model is not None,
            'faiss_available': FAISS_AVAILABLE
        }
