#!/usr/bin/env python3
"""
Query Engine: Load FAISS index and query to retrieve context
"""

import os
import sys
import pickle
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any

class FAISSQueryEngine:
    """Load FAISS index and query to retrieve context"""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model_name = model_name
        self.model = None
        self.index = None
        self.documents = []
        self.document_metadata = []
        
    def load_index(self, index_path: str, docs_path: str) -> bool:
        """Load the saved FAISS index and documents"""
        try:
            print("Loading FAISS index...")
            
            # Check if files exist
            if not os.path.exists(index_path):
                print(f"Error: Index file not found: {index_path}")
                return False
            
            if not os.path.exists(docs_path):
                print(f"Error: Documents file not found: {docs_path}")
                return False
            
            # Load FAISS index
            self.index = faiss.read_index(index_path)
            print(f"FAISS index loaded: {self.index.ntotal} vectors, dimension {self.index.d}")
            
            # Load documents
            with open(docs_path, 'rb') as f:
                data = pickle.load(f)
                self.documents = data['documents']
                self.document_metadata = data['metadata']
            
            print(f"Documents loaded: {len(self.documents)} chunks")
            print(f"Metadata loaded: {len(self.document_metadata)} entries")
            
            return True
            
        except Exception as e:
            print(f"Error loading index: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_sentence_transformer(self) -> bool:
        """Load the sentence transformer model"""
        try:
            print(f"Loading sentence transformer model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            print("Model loaded successfully")
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            print("Falling back to default model...")
            try:
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                print("Default model loaded successfully")
                return True
            except Exception as e2:
                print(f"Failed to load any model: {e2}")
                return False
    
    def search_index(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search the index for relevant documents"""
        try:
            if self.index is None or self.model is None:
                print("Index or model not initialized")
                return []
            
            print(f"Searching for: '{query}'")
            
            # Encode query
            query_embedding = self.model.encode([query])
            faiss.normalize_L2(query_embedding)
            
            # Search
            scores, indices = self.index.search(query_embedding.astype('float32'), top_k)
            
            # Prepare results
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx < len(self.documents):
                    result = {
                        'rank': i + 1,
                        'score': float(score),
                        'content': self.documents[idx],
                        'metadata': self.document_metadata[idx] if idx < len(self.document_metadata) else {},
                        'source': self.document_metadata[idx].get('source', 'unknown') if idx < len(self.document_metadata) else 'unknown'
                    }
                    results.append(result)
            
            return results
            
        except Exception as e:
            print(f"Error searching index: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def retrieve_context(self, query: str, top_k: int = 3) -> str:
        """Retrieve context for a query"""
        try:
            print(f"\nQuery: {query}")
            
            # Search for relevant documents
            results = self.search_index(query, top_k)
            
            if not results:
                return "No relevant context found for your query."
            
            # Prepare context
            context_parts = []
            context_parts.append(f"Retrieved Context for: '{query}'")
            context_parts.append("=" * 60)
            
            for i, result in enumerate(results):
                score = result['score']
                content = result['content'].strip()
                source = result['source']
                
                context_parts.append(f"\n{i+1}. [Relevance: {score:.3f}, Source: {source}]")
                context_parts.append("-" * 40)
                context_parts.append(content)
            
            # Add summary
            context_parts.append(f"\n\nSummary: Retrieved {len(results)} relevant pieces of context.")
            context_parts.append(f"Most relevant source has similarity score: {results[0]['score']:.3f}")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            print(f"Error retrieving context: {e}")
            return f"Error retrieving context: {str(e)}"
    
    def interactive_query(self):
        """Run interactive query session"""
        print("=" * 60)
        print("FAISS INDEX QUERY ENGINE")
        print("=" * 60)
        print("Ask questions to retrieve relevant context!")
        print("Type 'quit' to exit")
        print("\nExample queries:")
        print("  - What is the current Apple stock price?")
        print("  - Show me technical indicators")
        print("  - What are the financial recommendations?")
        print("  - Give me a trading summary")
        
        while True:
            try:
                query = input("\nYour query: ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    break
                
                if query:
                    context = self.retrieve_context(query)
                    print(f"\nRetrieved Context:\n{context}")
                else:
                    print("Please enter a query.")
                    
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def print_index_info(self):
        """Print information about the loaded index"""
        print("\n" + "=" * 60)
        print("LOADED INDEX INFORMATION")
        print("=" * 60)
        print(f"Total vectors: {self.index.ntotal}")
        print(f"Dimension: {self.index.d}")
        print(f"Total documents: {len(self.documents)}")
        print(f"Excel chunks: {len([d for d in self.document_metadata if d['source'] == 'excel'])}")
        print(f"JSON chunks: {len([d for d in self.document_metadata if d['source'] == 'json_analysis'])}")
        print("=" * 60)

def main():
    """Main function to load index and query"""
    
    print("=" * 60)
    print("STEP 3: LOADING INDEX AND QUERYING")
    print("=" * 60)
    
    # File paths
    index_path = "financial_data.index"
    docs_path = "financial_documents.pkl"
    
    # Check if files exist
    if not os.path.exists(index_path):
        print(f"Error: Index file not found: {index_path}")
        print("Please run Step 2 first to build the index.")
        return
    
    if not os.path.exists(docs_path):
        print(f"Error: Documents file not found: {docs_path}")
        print("Please run Step 2 first to build the index.")
        return
    
    # Initialize query engine
    engine = FAISSQueryEngine()
    
    # Load index
    if not engine.load_index(index_path, docs_path):
        print("Failed to load index. Please check if Step 2 completed successfully.")
        return
    
    # Load sentence transformer
    if not engine.load_sentence_transformer():
        print("Failed to load sentence transformer model.")
        return
    
    print("\n✅ Index and model loaded successfully!")
    
    # Print index information
    engine.print_index_info()
    
    # Run interactive query
    print("\nStarting interactive query session...")
    engine.interactive_query()

if __name__ == "__main__":
    main()
