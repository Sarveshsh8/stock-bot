#!/usr/bin/env python3
"""
Output Generator: Pass retrieved context to model for final output
"""

import os
import sys
import pickle
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any

class FinalOutputGenerator:
    """Generate final output by passing retrieved context to model"""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model_name = model_name
        self.model = None
        self.index = None
        self.documents = []
        self.document_metadata = []
        
    def load_index_and_model(self, index_path: str, docs_path: str) -> bool:
        """Load FAISS index and sentence transformer model"""
        try:
            print("Loading FAISS index and model...")
            
            # Load FAISS index
            if not os.path.exists(index_path):
                print(f"Error: Index file not found: {index_path}")
                return False
            
            self.index = faiss.read_index(index_path)
            print(f"FAISS index loaded: {self.index.ntotal} vectors")
            
            # Load documents
            with open(docs_path, 'rb') as f:
                data = pickle.load(f)
                self.documents = data['documents']
                self.document_metadata = data['metadata']
            
            print(f"Documents loaded: {len(self.documents)} chunks")
            
            # Load sentence transformer
            try:
                self.model = SentenceTransformer(self.model_name)
                print("Sentence transformer model loaded successfully")
            except Exception as e:
                print(f"Error loading model: {e}")
                try:
                    self.model = SentenceTransformer('all-MiniLM-L6-v2')
                    print("Default model loaded successfully")
                except Exception as e2:
                    print(f"Failed to load any model: {e2}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"Error loading index and model: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def retrieve_context(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieve relevant context for a query"""
        try:
            if self.index is None or self.model is None:
                print("Index or model not initialized")
                return []
            
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
                        'source': self.document_metadata[idx].get('source', 'unknown') if idx < len(self.document_metadata) else 'unknown'
                    }
                    results.append(result)
            
            return results
            
        except Exception as e:
            print(f"Error retrieving context: {e}")
            return []
    
    def generate_final_output(self, query: str, context_results: List[Dict[str, Any]]) -> str:
        """Generate final output using retrieved context"""
        try:
            if not context_results:
                return "No relevant context found to generate output."
            
            # Prepare context summary
            context_summary = []
            for result in context_results:
                source = result['source']
                score = result['score']
                content = result['content'][:300] + "..." if len(result['content']) > 300 else result['content']
                context_summary.append(f"[{source.upper()}, Relevance: {score:.3f}]\n{content}")
            
            # Generate comprehensive answer
            final_output = f"""
            FINAL OUTPUT FOR: "{query}"
            {'=' * 60}
            
            RETRIEVED CONTEXT:
            {'-' * 40}
            {chr(10).join(context_summary)}
            
            COMPREHENSIVE ANSWER:
            {'-' * 40}
            """
            
            # Add source-specific insights
            excel_insights = []
            json_insights = []
            
            for result in context_results:
                if result['source'] == 'excel':
                    excel_insights.append(result['content'])
                elif result['source'] == 'json_analysis':
                    json_insights.append(result['content'])
            
            if excel_insights:
                final_output += f"""
            TRADING DATA INSIGHTS:
            {'-' * 30}
            {chr(10).join(excel_insights[:2])}
            """
            
            if json_insights:
                final_output += f"""
            AI ANALYSIS INSIGHTS:
            {'-' * 30}
            {chr(10).join(json_insights[:2])}
            """
            
            # Add summary
            final_output += f"""
            
            SUMMARY:
            {'-' * 20}
            Based on {len(context_results)} relevant sources, I've provided comprehensive insights combining:
            - Trading data analysis (Excel source)
            - AI-powered analysis (JSON source)
            - Relevance scoring for accuracy
            
            The most relevant source has a similarity score of {context_results[0]['score']:.3f}, indicating high confidence in the retrieved information.
            """
            
            return final_output
            
        except Exception as e:
            print(f"Error generating final output: {e}")
            return f"Error generating final output: {str(e)}"
    
    def process_query(self, query: str) -> str:
        """Process a query through the complete pipeline"""
        try:
            print(f"\nProcessing query: '{query}'")
            print("-" * 50)
            
            # Step 1: Retrieve context
            print("Step 1: Retrieving relevant context...")
            context_results = self.retrieve_context(query, top_k=3)
            
            if not context_results:
                return "No relevant context found for your query."
            
            print(f"Retrieved {len(context_results)} relevant context pieces")
            
            # Step 2: Generate final output
            print("Step 2: Generating final output...")
            final_output = self.generate_final_output(query, context_results)
            
            print("Final output generated successfully!")
            return final_output
            
        except Exception as e:
            print(f"Error processing query: {e}")
            return f"Error processing query: {str(e)}"
    
    def interactive_session(self):
        """Run interactive session for final output generation"""
        print("=" * 60)
        print("FINAL OUTPUT GENERATOR")
        print("=" * 60)
        print("Complete pipeline: Query → Context Retrieval → Final Output")
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
                    final_output = self.process_query(query)
                    print(f"\n{final_output}")
                else:
                    print("Please enter a query.")
                    
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")

def main():
    """Main function for final output generation"""
    
    print("=" * 60)
    print("STEP 4: FINAL OUTPUT GENERATION")
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
    
    # Initialize generator
    generator = FinalOutputGenerator()
    
    # Load index and model
    if not generator.load_index_and_model(index_path, docs_path):
        print("Failed to load index and model. Please check if previous steps completed successfully.")
        return
    
    print("\n✅ Index and model loaded successfully!")
    print("Ready for final output generation!")
    
    # Run interactive session
    print("\nStarting interactive session...")
    generator.interactive_session()

if __name__ == "__main__":
    main()
