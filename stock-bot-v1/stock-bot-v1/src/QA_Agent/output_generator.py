#!/usr/bin/env python3
"""
Output Generator: Pass retrieved context to Nova Pro model for intelligent final output
"""

import os
import sys
import pickle
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.model.nova_pro_client import NovaProClient
from .prompts import (
    get_prompt, get_context_template, get_output_template, 
    get_error_message, get_success_message, CONFIG
)

class FinalOutputGenerator:
    """Generate intelligent final output using Nova Pro model with retrieved context"""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model_name = model_name
        self.model = None
        self.index = None
        self.documents = []
        self.document_metadata = []
        self.nova_client = None
        
    def load_index_and_model(self, index_path: str, docs_path: str) -> bool:
        """Load FAISS index, sentence transformer model, and Nova Pro client"""
        try:
            # Load FAISS index
            if not os.path.exists(index_path):
                print(get_error_message("file_not_found", file_path=index_path))
                return False
            
            self.index = faiss.read_index(index_path)
            
            # Load documents
            with open(docs_path, 'rb') as f:
                data = pickle.load(f)
                self.documents = data['documents']
                self.document_metadata = data['metadata']
            
            # Load sentence transformer
            try:
                self.model = SentenceTransformer(self.model_name)
            except Exception as e:
                print(get_error_message("loading_failed", component="sentence transformer"))
                try:
                    self.model = SentenceTransformer('all-MiniLM-L6-v2')
                except Exception as e2:
                    print(get_error_message("loading_failed", component="default model"))
                    return False
            
            # Initialize Nova Pro client
            try:
                self.nova_client = NovaProClient(region_name="us-east-1")
            except Exception as e:
                print(get_error_message("nova_pro_failed"))
                self.nova_client = None
            
            return True
            
        except Exception as e:
            print(get_error_message("loading_failed", component="index and models"))
            return False
    
    def retrieve_context(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """Retrieve relevant context for a query"""
        if top_k is None:
            top_k = CONFIG["default_top_k"]
            
        try:
            if self.index is None or self.model is None:
                print(get_error_message("model_not_loaded"))
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
            print(get_error_message("loading_failed", component="context retrieval"))
            return []
    
    def _determine_prompt_type(self, query: str) -> str:
        """Determine the appropriate prompt type based on the query"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['price', 'stock price', 'current price']):
            return "stock_price_analysis"
        elif any(word in query_lower for word in ['technical', 'indicator', 'sma', 'rsi', 'macd']):
            return "technical_indicators"
        elif any(word in query_lower for word in ['sentiment', 'market sentiment', 'trend']):
            return "market_sentiment"
        elif any(word in query_lower for word in ['recommendation', 'advice', 'investment']):
            return "financial_recommendations"
        elif any(word in query_lower for word in ['trading', 'summary', 'overview']):
            return "trading_summary"
        else:
            return "general_analysis"
    
    def generate_final_output_with_nova(self, query: str, context_results: List[Dict[str, Any]]) -> str:
        """Generate intelligent final output using Nova Pro model"""
        try:
            if not context_results:
                return get_error_message("context_not_found")
            
            if self.nova_client is None:
                return self.generate_fallback_output(query, context_results)
            
            # Prepare context for Nova Pro
            context_summary = []
            for result in context_results:
                source = result['source']
                score = result['score']
                content = result['content'][:CONFIG["max_context_length"]] + "..." if len(result['content']) > CONFIG["max_context_length"] else result['content']
                context_summary.append(get_context_template("source_format", 
                    source_upper=source.upper(), score=score, content=content))
            
            # Determine prompt type and get appropriate prompt
            prompt_type = self._determine_prompt_type(query)
            context_text = "\n".join(context_summary)
            
            nova_prompt = get_prompt(prompt_type, query=query, context=context_text)
            
            # Get response from Nova Pro
            nova_response = self.nova_client.text_only_request(
                prompt=nova_prompt,
                max_tokens=CONFIG["max_tokens"],
                temperature=CONFIG["temperature"],
                top_p=CONFIG["top_p"]
            )
            
            # Format the final output
            separator = "=" * CONFIG["separator_length"]
            final_output = get_output_template("nova_pro_header", 
                separator=separator, query=query, response=nova_response)
            
            # Add source information
            for i, result in enumerate(context_results):
                source = result['source']
                score = result['score']
                final_output += f"\n{i+1}. {source.upper()} (Relevance: {score:.3f})"
            
            final_output += get_output_template("source_summary", 
                count=len(context_results), score=context_results[0]['score'])
            
            return final_output
            
        except Exception as e:
            print(get_error_message("nova_pro_failed"))
            return self.generate_fallback_output(query, context_results)
    
    def generate_fallback_output(self, query: str, context_results: List[Dict[str, Any]]) -> str:
        """Fallback text generation when Nova Pro is not available"""
        try:
            # Prepare context summary
            context_summary = []
            for result in context_results:
                source = result['source']
                score = result['score']
                content = result['content'][:300] + "..." if len(result['content']) > 300 else result['content']
                context_summary.append(get_context_template("source_format", 
                    source_upper=source.upper(), score=score, content=content))
            
            # Generate comprehensive answer
            separator = "=" * CONFIG["separator_length"]
            context_separator = "-" * 40
            context_text = "\n".join(context_summary)
            
            final_output = get_output_template("fallback_header", 
                query=query, separator=separator, context_separator=context_separator, context=context_text)
            
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
            
            NOTE: This is a fallback response. For more intelligent analysis, ensure Nova Pro client is properly configured.
            """
            
            return final_output
            
        except Exception as e:
            return get_error_message("loading_failed", component="fallback output generation")
    
    def process_query(self, query: str) -> str:
        """Process a query through the complete intelligent pipeline"""
        try:
            # Step 1: Retrieve context
            context_results = self.retrieve_context(query, top_k=CONFIG["default_top_k"])
            
            if not context_results:
                return get_error_message("context_not_found")
            
            # Step 2: Generate intelligent output with Nova Pro
            final_output = self.generate_final_output_with_nova(query, context_results)
            
            return final_output
            
        except Exception as e:
            return get_error_message("loading_failed", component="query processing")
    
    def interactive_session(self):
        """Run interactive session for intelligent output generation"""
        from .prompts import INTERACTIVE_PROMPTS
        
        for query in INTERACTIVE_PROMPTS["example_queries"]:
            print(f"  - {query}")
        
        if self.nova_client:
            print("\nNova Pro integration: ACTIVE - Intelligent analysis enabled")
        else:
            print("\nNova Pro integration: INACTIVE - Using fallback text generation")
        
        while True:
            try:
                query = input("\nYour query: ").strip()
                
                if query.lower() in INTERACTIVE_PROMPTS["quit_commands"]:
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
                print(INTERACTIVE_PROMPTS["error_message"])

def main():
    """Main function for intelligent output generation"""
    
    
    # File paths
    index_path = "indices/financial_data.index"
    docs_path = "indices/financial_documents.pkl"
    
    # Check if files exist
    if not os.path.exists(index_path):
        print(get_error_message("index_not_found"))
        print("Please run Step 2 first to build the index.")
        return
    
    if not os.path.exists(docs_path):
        print(get_error_message("file_not_found", file_path=docs_path))
        print("Please run Step 2 first to build the index.")
        return
    
    # Initialize generator
    generator = FinalOutputGenerator()
    
    # Load index and models
    if not generator.load_index_and_model(index_path, docs_path):
        print("Failed to load index and models. Please check if previous steps completed successfully.")
        return
    
    print(get_success_message("models_loaded"))
    print("Ready for intelligent output generation!")
    
    # Run interactive session
    print("\nStarting interactive session...")
    generator.interactive_session()

if __name__ == "__main__":
    main()
