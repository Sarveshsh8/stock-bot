#!/usr/bin/env python3
"""
FAISS Builder Module

Builds FAISS index from data and analysis
"""

import faiss
import pickle
import numpy as np
import os
from datetime import datetime
from typing import Dict, Any, List

class FAISSBuilder:
    def __init__(self):
        self.output_dir = "data/faiss"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def create_documents(self, data: Dict[str, Any], excel_path: str, multimodal_results: Dict[str, Any], symbol: str) -> List[Dict[str, Any]]:
        """Create documents for indexing"""
        documents = []
        
        # Summary document
        summary_text = f"""
        Stock: {symbol}
        Company: {data['info'].get('longName', 'N/A')}
        Current Price: ${data.get('current_price', 'N/A')}
        Market Cap: ${data['info'].get('marketCap', 0):,.0f}
        Volume: {data['info'].get('volume', 0):,.0f}
        Analysis Date: {data['timestamp']}
        """
        documents.append({'text': summary_text, 'type': 'summary'})
        
        # Technical data document
        if not data['hist_daily'].empty:
            tech_text = f"""
            Technical Data for {symbol}:
            - 5-day high: ${data['hist_daily']['High'].max():.2f}
            - 5-day low: ${data['hist_daily']['Low'].min():.2f}
            - Average volume: {data['hist_daily']['Volume'].mean():,.0f}
            - Price change: {((data['hist_daily']['Close'].iloc[-1] / data['hist_daily']['Close'].iloc[0]) - 1) * 100:.2f}%
            """
            documents.append({'text': tech_text, 'type': 'technical'})
        
        # Multimodal analysis documents
        for key, result in multimodal_results.items():
            if isinstance(result, str):
                documents.append({'text': result, 'type': key})
        
        return documents
    
    def build_index(self, documents: List[Dict[str, Any]], symbol: str) -> str:
        """Build FAISS index from documents"""
        print("🔍 Building FAISS index...")
        
        try:
            # Simple vectorization (word frequency)
            all_text = ' '.join([doc['text'] for doc in documents])
            words = all_text.lower().split()
            word_freq = {}
            for word in words:
                if word.isalpha():
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Create vectors
            unique_words = list(set(word_freq.keys()))
            vectors = []
            
            for doc in documents:
                doc_words = doc['text'].lower().split()
                vector = [doc_words.count(word) for word in unique_words]
                vectors.append(vector)
            
            # Build FAISS index
            vectors = np.array(vectors, dtype=np.float32)
            dimension = vectors.shape[1]
            
            index = faiss.IndexFlatL2(dimension)
            index.add(vectors)
            
            # Save index and metadata
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            index_path = os.path.join(self.output_dir, f"{symbol}_index_{timestamp}.faiss")
            metadata_path = os.path.join(self.output_dir, f"{symbol}_metadata_{timestamp}.pkl")
            
            faiss.write_index(index, index_path)
            
            metadata = {
                'documents': documents,
                'unique_words': unique_words,
                'symbol': symbol,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(metadata_path, 'wb') as f:
                pickle.dump(metadata, f)
            
            print(f"✅ FAISS index saved: {index_path}")
            return index_path
            
        except Exception as e:
            print(f"❌ Error building FAISS index: {e}")
            return ""
    
    def create_index(self, data: Dict[str, Any], excel_path: str, multimodal_results: Dict[str, Any], symbol: str) -> str:
        """Create complete FAISS index"""
        documents = self.create_documents(data, excel_path, multimodal_results, symbol)
        return self.build_index(documents, symbol)
    
    def merge_with_existing(self, new_documents: List[Dict[str, Any]], existing_index_path: str, symbol: str) -> str:
        """Merge new documents with existing database"""
        print("🔄 Merging with existing database...")
        
        try:
            import pickle
            
            # Load existing documents
            existing_metadata_path = existing_index_path.replace('.faiss', '_metadata.pkl')
            
            if os.path.exists(existing_metadata_path):
                with open(existing_metadata_path, 'rb') as f:
                    existing_metadata = pickle.load(f)
                
                existing_documents = existing_metadata['documents']
                all_documents = existing_documents + new_documents
            else:
                all_documents = new_documents
            
            # Build merged index
            return self.build_index(all_documents, symbol)
            
        except Exception as e:
            print(f"❌ Error merging database: {e}")
            return ""
