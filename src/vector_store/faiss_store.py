import faiss
import numpy as np
import pickle
from pathlib import Path
from typing import List, Dict, Tuple
import logging
from sentence_transformers import SentenceTransformer


class FAISSVectorStore:
    """
    FAISS Vector Store using Open Source Embeddings.
    
    This version uses:
    - Sentence-Transformers (open source, runs locally)
    - No API calls, no costs
    - 100% free and offline capable
    
    Popular models:
    - 'all-MiniLM-L6-v2': Fast, good quality (384 dimensions)
    - 'all-mpnet-base-v2': Better quality (768 dimensions)
    - 'paraphrase-multilingual-MiniLM-L12-v2': Multilingual support
    
    How it works:
    1. Loads open-source model locally
    2. Creates embeddings on your machine
    3. Stores in FAISS index
    4. Fast similarity search
    
    Advantages:
    - No API costs
    - No internet required after model download
    - Privacy - your data never leaves your machine
    - Fast inference
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize FAISS vector store with open-source embeddings.
        
        Parameters:
        - model_name: Name of sentence-transformers model
        
        Popular choices:
        - 'all-MiniLM-L6-v2': Fast, 384 dimensions, good for most tasks
        - 'all-mpnet-base-v2': Higher quality, 768 dimensions
        - 'multi-qa-MiniLM-L6-cos-v1': Optimized for Q&A
        """
        self.model_name = model_name
        self.index = None
        self.documents = []
        self.metadata_list = []
        self.dimension = None
        
        self._setup_logging()
        self._setup_model()
        
    def _setup_logging(self):
        """Setup logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _setup_model(self):
        """
        Load open-source embedding model.
        
        This downloads the model on first run, then uses local cache.
        The model runs on your CPU/GPU - no API calls needed!
        """
        try:
            self.logger.info(f"Loading open-source model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.logger.info(f"Model loaded successfully!")
            self.logger.info(f"Model dimension: {self.model.get_sentence_embedding_dimension()}")
        except Exception as e:
            self.logger.error(f"Error loading model: {str(e)}")
            raise
    
    def create_index(self, texts: List[str], metadata_list: List[Dict]):
        """
        Create FAISS index from text documents using open-source embeddings.
        
        Parameters:
        - texts: List of text summaries to index
        - metadata_list: List of metadata dictionaries
        
        This function:
        1. Takes each text summary
        2. Converts to embedding using local model (FREE!)
        3. Adds to FAISS index
        4. Stores original text and metadata
        
        No API calls, runs on your machine!
        """
        self.logger.info(f"Creating embeddings for {len(texts)} documents using {self.model_name}...")
        
        # Create embeddings using open-source model
        # This runs locally on your machine - no internet needed!
        embeddings_list = self.model.encode(
            texts,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True  # Better for similarity search
        )
        
        embeddings_array = embeddings_list.astype('float32')
        
        # Get dimension
        self.dimension = embeddings_array.shape[1]
        self.logger.info(f"Embedding dimension: {self.dimension}")
        
        # Create FAISS index
        # Using IndexFlatIP for inner product (works well with normalized embeddings)
        self.index = faiss.IndexFlatIP(self.dimension)
        
        # Add vectors to index
        self.index.add(embeddings_array)
        
        # Store documents and metadata
        self.documents = texts
        self.metadata_list = metadata_list
        
        self.logger.info(f"FAISS index created with {self.index.ntotal} vectors")
        self.logger.info(f"Using open-source model: {self.model_name} (FREE!)")
    
    def search(self, query: str, k: int = 5) -> List[Tuple[str, Dict, float]]:
        """
        Search FAISS index for relevant documents.
        
        Parameters:
        - query: User's question
        - k: Number of results to return
        
        Returns:
        - List of (document_text, metadata, similarity_score) tuples
        
        This runs locally - no API calls!
        """
        if self.index is None or self.index.ntotal == 0:
            self.logger.warning("Index is empty")
            return []
        
        # Create embedding for query using local model
        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        query_vector = query_embedding.astype('float32')
        
        # Search the index
        # Higher scores = more similar (because we're using inner product)
        scores, indices = self.index.search(query_vector, k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.documents):
                results.append((
                    self.documents[idx],
                    self.metadata_list[idx],
                    float(scores[0][i])  # Similarity score (higher = better)
                ))
        
        return results
    
    def save(self, save_dir: str):
        """
        Save FAISS index and data to disk.
        
        Parameters:
        - save_dir: Directory to save the index
        """
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_path / "faiss_index.bin"))
        
        # Save documents and metadata
        with open(save_path / "documents.pkl", 'wb') as f:
            pickle.dump(self.documents, f)
        
        with open(save_path / "metadata.pkl", 'wb') as f:
            pickle.dump(self.metadata_list, f)
        
        with open(save_path / "dimension.pkl", 'wb') as f:
            pickle.dump(self.dimension, f)
        
        with open(save_path / "model_name.pkl", 'wb') as f:
            pickle.dump(self.model_name, f)
        
        self.logger.info(f"FAISS index saved to {save_path}")
    
    def load(self, load_dir: str):
        """
        Load previously saved FAISS index.
        
        Parameters:
        - load_dir: Directory containing saved index
        """
        load_path = Path(load_dir)
        
        if not load_path.exists():
            raise FileNotFoundError(f"Index directory not found: {load_path}")
        
        # Load FAISS index
        self.index = faiss.read_index(str(load_path / "faiss_index.bin"))
        
        # Load documents and metadata
        with open(load_path / "documents.pkl", 'rb') as f:
            self.documents = pickle.load(f)
        
        with open(load_path / "metadata.pkl", 'rb') as f:
            self.metadata_list = pickle.load(f)
        
        with open(load_path / "dimension.pkl", 'rb') as f:
            self.dimension = pickle.load(f)
        
        with open(load_path / "model_name.pkl", 'rb') as f:
            self.model_name = pickle.load(f)
        
        self.logger.info(f"FAISS index loaded from {load_path}")
        self.logger.info(f"Index contains {self.index.ntotal} vectors")
        self.logger.info(f"Using model: {self.model_name}")
    
    def get_stats(self) -> Dict:
        """Get statistics about the vector store"""
        return {
            'total_documents': len(self.documents),
            'total_vectors': self.index.ntotal if self.index else 0,
            'dimension': self.dimension,
            'model_name': self.model_name,
            'cost': 'FREE - Open Source!'
        }
    
    def change_model(self, new_model_name: str):
        """
        Change to a different open-source model.
        
        Parameters:
        - new_model_name: Name of new model to use
        
        Note: You'll need to recreate the index after changing models
        """
        self.logger.info(f"Changing model from {self.model_name} to {new_model_name}")
        self.model_name = new_model_name
        self._setup_model()
        self.logger.info("Model changed. Please recreate the index.")

