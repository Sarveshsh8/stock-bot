#!/usr/bin/env python3
"""
Q&A System Module

Provides Q&A functionality using FAISS index
"""

import faiss
import pickle
import os
from typing import Dict, Any, List

class QASystem:
    def __init__(self, index_path: str):
        self.index_path = index_path
        self.metadata_path = index_path.replace('.faiss', '_metadata.pkl')
        
        # Try different metadata path patterns
        if not os.path.exists(self.metadata_path):
            # Try with timestamp pattern
            base_name = index_path.replace('.faiss', '')
            if '_index_' in base_name:
                symbol = base_name.split('_index_')[0]
                timestamp = base_name.split('_index_')[1]
                self.metadata_path = f"{symbol}_metadata_{timestamp}.pkl"
            else:
                # Try without 'db' in the name
                self.metadata_path = index_path.replace('_db.faiss', '_metadata.pkl')
        
        # Load index and metadata
        self.index = faiss.read_index(index_path)
        with open(self.metadata_path, 'rb') as f:
            self.metadata = pickle.load(f)
    
    def search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Search for relevant documents"""
        try:
            # Simple keyword matching
            query_words = query.lower().split()
            
            best_matches = []
            
            for i, doc in enumerate(self.metadata['documents']):
                doc_words = doc['text'].lower().split()
                score = sum(1 for word in query_words if word in doc_words)
                
                if score > 0:
                    best_matches.append({
                        'document': doc,
                        'score': score,
                        'index': i
                    })
            
            # Sort by score and return top k
            best_matches.sort(key=lambda x: x['score'], reverse=True)
            return best_matches[:k]
            
        except Exception as e:
            print(f"❌ Error in search: {e}")
            return []
    
    def answer_question(self, question: str) -> str:
        """Answer a question using the index"""
        try:
            matches = self.search(question, k=1)
            
            if matches:
                best_match = matches[0]['document']
                return f"Answer: {best_match['text'][:300]}..."
            else:
                return "Sorry, I couldn't find relevant information."
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_available_topics(self) -> List[str]:
        """Get list of available topics"""
        try:
            topics = []
            for doc in self.metadata['documents']:
                topics.append(doc['type'])
            return list(set(topics))
        except Exception as e:
            return []
