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
import json
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

class AmazonTitanEmbedding:
    """Amazon Titan embedding model wrapper"""
    
    def __init__(self, model_name: str, region: str = "us-east-1"):
        """
        Initialize Amazon Titan embedding model
        
        Args:
            model_name: The model name (e.g., "amazon.titan-embed-text-v1")
            region: AWS region
        """
        self.model_name = model_name
        self.region = region
        
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Initialize Bedrock client
        self.bedrock_runtime = boto3.client(
            'bedrock-runtime',
            region_name=region,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        self.logger = logging.getLogger(__name__)
    
    def encode(self, texts: List[str], show_progress_bar: bool = False) -> np.ndarray:
        """
        Generate embeddings for a list of texts
        
        Args:
            texts: List of texts to embed
            show_progress_bar: Whether to show progress (ignored for API calls)
            
        Returns:
            numpy array of embeddings
        """
        embeddings = []
        
        for text in texts:
            try:
                # Prepare the request body for Titan embedding
                if "v2" in self.model_name:
                    # Titan v2 format
                    body = {
                        "inputText": text,
                        "dimensions": 1024  # Titan v2 default dimension
                    }
                else:
                    # Titan v1 format
                    body = {
                        "inputText": text,
                        "dimensions": 1536  # Titan v1 embedding dimension
                    }
                
                # Invoke the model
                response = self.bedrock_runtime.invoke_model(
                    modelId=self.model_name,
                    body=json.dumps(body),
                    contentType='application/json'
                )
                
                # Parse response
                response_body = json.loads(response['body'].read())
                embedding = response_body['embedding']
                embeddings.append(embedding)
                
            except ClientError as e:
                self.logger.error(f"Error generating embedding: {e}")
                # Return zero vector as fallback
                fallback_dim = 1024 if "v2" in self.model_name else 1536
                embeddings.append([0.0] * fallback_dim)
            except Exception as e:
                self.logger.error(f"Unexpected error generating embedding: {e}")
                fallback_dim = 1024 if "v2" in self.model_name else 1536
                embeddings.append([0.0] * fallback_dim)
        
        return np.array(embeddings, dtype=np.float32)

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
        
        # Storage settings
        self.storage_config = config['faiss_settings'].get('storage', {})
        self.local_directory = self.storage_config.get('local_directory', 'indices')
        self.filename_prefix = self.storage_config.get('filename_prefix', 'financial_index')
        self.use_timestamp = self.storage_config.get('use_timestamp', True)
        self.auto_save = self.storage_config.get('auto_save', True)
        self.max_local_files = self.storage_config.get('max_local_files', 10)
        
        self.model = None
        self.index = None
        self.documents = []
        self.document_metadata = []
        
        self._setup_logging()
        self._load_model()
        self._ensure_local_directory()
    
    def _setup_logging(self):
        """Setup logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _load_model(self):
        """Load embedding model"""
        try:
            # Check if using Amazon Titan or SentenceTransformers
            if self.model_name.startswith("amazon.titan"):
                # Use Amazon Titan embedding
                region = self.config.get('bedrock_settings', {}).get('region', 'us-east-1')
                self.model = AmazonTitanEmbedding(self.model_name, region)
                self.logger.info(f"Loaded Amazon Titan model: {self.model_name}")
            else:
                # Fallback to SentenceTransformers for other models
                from sentence_transformers import SentenceTransformer
                import torch
                
                # Fix for PyTorch device issues on macOS MPS
                os.environ['CUDA_VISIBLE_DEVICES'] = ''
                os.environ['PYTORCH_DISABLE_MPS'] = '1'
                torch.set_num_threads(1)  # Limit threading to avoid conflicts
                
                # Explicitly disable MPS
                if hasattr(torch.backends, 'mps'):
                    torch.backends.mps.is_available = lambda: False
                
                # Always use CPU for stability
                self.model = SentenceTransformer(self.model_name, device='cpu')
                
                # Ensure model is on CPU
                if hasattr(self.model, 'to'):
                    self.model = self.model.to('cpu')
                
                self.logger.info(f"Loaded SentenceTransformer model: {self.model_name} on CPU")
        except Exception as e:
            self.logger.error(f"Error loading model: {str(e)}")
            raise
    
    def _ensure_local_directory(self):
        """Ensure local directory exists"""
        try:
            os.makedirs(self.local_directory, exist_ok=True)
            self.logger.info(f"Local directory ready: {self.local_directory}")
        except Exception as e:
            self.logger.error(f"Error creating local directory: {e}")
    
    def _get_index_paths(self, timestamp: str = None) -> tuple:
        """Get index file paths based on configuration"""
        if timestamp is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if self.use_timestamp:
            index_filename = f"{self.filename_prefix}_{timestamp}.faiss"
            docs_filename = f"{self.filename_prefix}_docs_{timestamp}.pkl"
        else:
            index_filename = f"{self.filename_prefix}.faiss"
            docs_filename = f"{self.filename_prefix}_docs.pkl"
        
        index_path = os.path.join(self.local_directory, index_filename)
        docs_path = os.path.join(self.local_directory, docs_filename)
        
        return index_path, docs_path
    
    def _cleanup_old_files(self):
        """Clean up old index files based on max_local_files setting"""
        try:
            import glob
            
            # Get all index files
            pattern = os.path.join(self.local_directory, f"{self.filename_prefix}_*.faiss")
            index_files = glob.glob(pattern)
            
            if len(index_files) > self.max_local_files:
                # Sort by modification time (oldest first)
                index_files.sort(key=os.path.getmtime)
                
                # Remove oldest files
                files_to_remove = index_files[:-self.max_local_files]
                for file_path in files_to_remove:
                    try:
                        os.remove(file_path)
                        # Also remove corresponding docs file
                        docs_file = file_path.replace('.faiss', '_docs.pkl')
                        if os.path.exists(docs_file):
                            os.remove(docs_file)
                        self.logger.info(f"Cleaned up old index file: {file_path}")
                    except Exception as e:
                        self.logger.warning(f"Could not remove {file_path}: {e}")
                        
        except Exception as e:
            self.logger.warning(f"Error during cleanup: {e}")
    
    def add_yahoo_data_to_index(self, yahoo_data: Dict[str, Any]) -> bool:
        """
        Add Yahoo Finance data to existing FAISS index
        
        Args:
            yahoo_data: Dictionary containing Yahoo Finance data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("Adding Yahoo Finance data to index")
            
            # Process each symbol's data
            for symbol, df in yahoo_data.items():
                self._process_dataframe(symbol, df, 'yahoo_finance')
            
            self.logger.info(f"Added {len(yahoo_data)} Yahoo Finance symbols to index")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding Yahoo data to index: {str(e)}")
            return False
    
    def add_files_to_index(self, file_data: List[Dict[str, Any]], data_type: str = 'uploaded_file') -> bool:
        """
        Add file data to existing FAISS index
        
        Args:
            file_data: List of processed file data
            data_type: Type of data (uploaded_file, youtube_video, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Adding {len(file_data)} {data_type} files to index")
            
            for file_info in file_data:
                # Add data type to metadata
                file_info['data_type'] = data_type
                self._process_file_data(file_info)
            
            self.logger.info(f"Added {len(file_data)} {data_type} files to index")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding {data_type} files to index: {str(e)}")
            return False
    
    def create_unified_index(self, yahoo_data: Dict[str, Any] = None, 
                           uploaded_files: List[Dict[str, Any]] = None,
                           youtube_analyses: List[Dict[str, Any]] = None) -> bool:
        """
        Create a single unified FAISS index from all data sources
        
        Args:
            yahoo_data: Yahoo Finance data
            uploaded_files: Processed uploaded files
            youtube_analyses: YouTube video analyses
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("Creating unified FAISS index from all data sources")
            
            # Clear existing data
            self.documents = []
            self.document_metadata = []
            self.embeddings = []
            
            # Add Yahoo Finance data
            if yahoo_data:
                self.add_yahoo_data_to_index(yahoo_data)
            
            # Add uploaded files
            if uploaded_files:
                self.add_files_to_index(uploaded_files, 'uploaded_file')
            
            # Add YouTube analyses
            if youtube_analyses:
                self.add_files_to_index(youtube_analyses, 'youtube_video')
            
            # Build the unified index
            if self.documents:
                self._build_index()
                self.logger.info(f"Created unified FAISS index with {len(self.documents)} documents")
                return True
            else:
                self.logger.warning("No documents to create index from")
                return False
                
        except Exception as e:
            self.logger.error(f"Error creating unified index: {str(e)}")
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
                    'data_type': 'stock_data',
                    'content_type': data_type,
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
                    'data_type': file_info.get('data_type', 'uploaded_file'),
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
            # Generate embeddings with better error handling
            self.logger.info("Generating embeddings...")
            
            # Process documents in smaller batches to avoid memory issues
            batch_size = 32
            all_embeddings = []
            
            for i in range(0, len(self.documents), batch_size):
                batch_docs = self.documents[i:i + batch_size]
                self.logger.info(f"Processing batch {i//batch_size + 1}/{(len(self.documents) + batch_size - 1)//batch_size}")
                
                try:
                    batch_embeddings = self.model.encode(batch_docs, show_progress_bar=False)
                    all_embeddings.append(batch_embeddings)
                except Exception as e:
                    self.logger.error(f"Error processing batch {i//batch_size + 1}: {e}")
                    raise
            
            # Combine all embeddings
            import numpy as np
            embeddings = np.vstack(all_embeddings)
            
            # Create FAISS index
            self.index = faiss.IndexFlatIP(self.index_dimension)
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings)
            
            # Add embeddings to index
            self.index.add(embeddings.astype('float32'))
            
            self.logger.info(f"Built FAISS index with {self.index.ntotal} vectors")
            
            # Auto-save if enabled
            if self.auto_save:
                self.save_index_locally()
            
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
    
    def save_index_locally(self, timestamp: str = None) -> bool:
        """
        Save FAISS index and documents to local directory using configuration
        
        Args:
            timestamp: Optional timestamp for filename
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.index is None:
                self.logger.warning("No index to save")
                return False
            
            # Get paths based on configuration
            index_path, docs_path = self._get_index_paths(timestamp)
            
            # Save FAISS index
            faiss.write_index(self.index, index_path)
            
            # Save documents and metadata
            with open(docs_path, 'wb') as f:
                pickle.dump({
                    'documents': self.documents,
                    'metadata': self.document_metadata
                }, f)
            
            self.logger.info(f"Saved index to {index_path} and documents to {docs_path}")
            
            # Cleanup old files if needed
            self._cleanup_old_files()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving index locally: {str(e)}")
            return False
    
    def save_index(self, index_path: str, docs_path: str) -> bool:
        """
        Save FAISS index and documents to specified paths (legacy method)
        
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
    
    def load_latest_index(self) -> bool:
        """Load the most recent index from local directory"""
        try:
            import glob
            
            # Find the most recent index file
            pattern = os.path.join(self.local_directory, f"{self.filename_prefix}_*.faiss")
            index_files = glob.glob(pattern)
            
            if not index_files:
                self.logger.warning("No index files found in local directory")
                return False
            
            # Get the most recent file
            latest_index = max(index_files, key=os.path.getmtime)
            latest_docs = latest_index.replace('.faiss', '_docs.pkl')
            
            if not os.path.exists(latest_docs):
                self.logger.error(f"Corresponding docs file not found: {latest_docs}")
                return False
            
            # Load the index
            success = self.load_index(latest_index, latest_docs)
            if success:
                self.logger.info(f"Loaded latest index: {latest_index}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error loading latest index: {e}")
            return False
    
    def get_index_info(self) -> Dict[str, Any]:
        """Get information about the current index"""
        if self.index is None:
            return {
                'status': 'no_index', 
                'total_vectors': 0, 
                'total_documents': 0,
                'local_directory': self.local_directory,
                'filename_prefix': self.filename_prefix,
                'auto_save': self.auto_save
            }
        
        return {
            'status': 'loaded',
            'total_vectors': self.index.ntotal,
            'total_documents': len(self.documents),
            'model_name': self.model_name,
            'index_dimension': self.index_dimension,
            'local_directory': self.local_directory,
            'filename_prefix': self.filename_prefix,
            'auto_save': self.auto_save
        }
    
    def clear_old_indices(self) -> bool:
        """Clear all old indices to force fresh indexing"""
        try:
            import glob
            
            # Find all old index files
            index_pattern = os.path.join(self.local_directory, f"{self.filename_prefix}_*.faiss")
            docs_pattern = os.path.join(self.local_directory, f"{self.filename_prefix}_docs_*.pkl")
            
            old_indices = glob.glob(index_pattern)
            old_docs = glob.glob(docs_pattern)
            
            # Remove old files
            for file_path in old_indices + old_docs:
                try:
                    os.remove(file_path)
                    self.logger.info(f"Removed old index file: {file_path}")
                except Exception as e:
                    self.logger.warning(f"Could not remove {file_path}: {e}")
            
            # Clear current index
            self.index = None
            self.documents = []
            self.document_metadata = []
            
            self.logger.info("Cleared all old indices - fresh indexing will be performed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error clearing old indices: {e}")
            return False
